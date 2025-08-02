#!/usr/bin/env python3
"""
AI Command Tool - Main Entry Point
A smart command-line assistant that fixes errors and provides command advice.
"""

from utils.logger import Logger
from utils.terminal_utils import TerminalUtils
from core.config_manager import ConfigManager
from core.command_processor import CommandProcessor
import sys
import argparse
import os
import subprocess
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for the AI command tool."""
    parser = argparse.ArgumentParser(
        description="AI-powered command assistant for fixing errors and providing advice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aicmd fix "ls: cannot access 'nonexistent': No such file or directory"
  aicmd suggest "compress files"
  aicmd explain "find . -name '*.py' -exec grep -l 'import' {} \\;"
  aicmd --interactive
        """
    )

    parser.add_argument(
        'action',
        nargs='?',
        choices=['fix', 'suggest', 'explain', 'setup', 'cleanup'],
        help='Action to perform'
    )

    parser.add_argument(
        'input_text',
        nargs='*',
        help='Error message, command description, or command to explain'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive mode'
    )

    parser.add_argument(
        '--config',
        help='Path to config file'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--auto-execute',
        action='store_true',
        help='Automatically execute suggested commands (use with caution)'
    )

    args = parser.parse_args()

    # Initialize components
    logger = Logger(verbose=args.verbose)
    config = ConfigManager(config_path=args.config)
    processor = CommandProcessor(config, logger)

    try:
        if args.action == 'setup':
            setup_tool(config, logger)
        elif args.action == 'cleanup':
            cleanup_temp_files(logger)
            logger.success("Cleaned up temporary files")
        elif args.interactive:
            interactive_mode(processor, logger)
        elif args.action and (args.input_text or args.action == 'fix'):
            # Allow 'fix' without input_text for auto-detection
            input_str = ' '.join(args.input_text) if args.input_text else ""
            handle_single_command(args.action, input_str,
                                  processor, logger, args.auto_execute)
        else:
            # If no action specified, try to detect from stdin or last command
            handle_smart_mode(processor, logger, args.auto_execute)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def setup_tool(config, logger):
    """Setup the AI command tool."""
    logger.info("Setting up AI Command Tool...")

    # Create config directory if it doesn't exist
    config_dir = Path.home() / '.aicmd'
    config_dir.mkdir(exist_ok=True)

    # Check if API key is configured
    if not config.get_api_key():
        logger.info("No API key found. Please configure your AI service:")
        logger.info("1. OpenAI API: Set OPENAI_API_KEY environment variable")
        logger.info(
            "2. Anthropic API: Set ANTHROPIC_API_KEY environment variable")
        logger.info("3. Or configure in ~/.aicmd/config.json")

    # Setup shell integration
    setup_shell_integration(logger)

    logger.info("Setup complete!")


def setup_shell_integration(logger):
    """Setup shell integration for automatic error detection."""
    shell_configs = {
        'bash': Path.home() / '.bashrc',
        'zsh': Path.home() / '.zshrc',
        'fish': Path.home() / '.config/fish/config.fish'
    }

    integration_code = '''
# AI Command Tool Integration
export AICMD_AUTO_SUGGEST=1
function command_not_found_handler() {
    aicmd fix "$@" 2>/dev/null || echo "Command not found: $@"
}
'''

    logger.info("Shell integration setup instructions:")
    for shell, config_file in shell_configs.items():
        if config_file.exists():
            logger.info(f"For {shell}, add to {config_file}:")
            logger.info(integration_code)


def interactive_mode(processor, logger):
    """Start interactive mode."""
    logger.info("AI Command Assistant - Interactive Mode")
    logger.info("Type 'help' for commands, 'quit' to exit\n")

    while True:
        try:
            user_input = input("aicmd> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if user_input.lower() == 'help':
                show_help()
                continue

            # Parse interactive command
            parts = user_input.split(' ', 1)
            action = parts[0].lower()
            text = parts[1] if len(parts) > 1 else ""

            if action in ['fix', 'suggest', 'explain']:
                if action == 'fix' and not text:
                    # Handle fix without text - auto-detect error
                    logger.info(
                        "No error message provided. Detecting last command error...")
                    last_error = detect_last_error(logger)
                    if last_error:
                        logger.info(f"Detected error: {last_error}")
                        text = last_error
                    else:
                        logger.error(
                            "No recent error detected. Please provide an error message.")
                        logger.info("Usage: fix \"your error message\"")
                        continue
                elif not text and action != 'fix':
                    logger.error(f"Please provide text for '{action}' command")
                    continue
                handle_single_command(action, text, processor, logger, False)
            else:
                # Treat as a command suggestion request
                handle_single_command(
                    'suggest', user_input, processor, logger, False)

        except EOFError:
            break


def handle_single_command(action, input_text, processor, logger, auto_execute):
    """Handle a single command action."""
    if action == 'fix':
        # If no input text provided, try to get the last error automatically
        if not input_text.strip():
            logger.info(
                "No error message provided. Detecting last command error...")
            last_error = detect_last_error(logger)
            if last_error:
                logger.info(f"Detected error: {last_error}")
                input_text = last_error
            else:
                logger.error(
                    "No recent error detected. Please provide an error message.")
                logger.info("Usage: aicmd fix \"your error message\"")
                return

        result = processor.fix_error(input_text)
    elif action == 'suggest':
        result = processor.suggest_command(input_text)
    elif action == 'explain':
        result = processor.explain_command(input_text)
    else:
        logger.error(f"Unknown action: {action}")
        return

    if result:
        logger.info(result['explanation'])

        if 'command' in result and result['command']:
            logger.info(f"\nSuggested command:")
            logger.info(f"  {result['command']}")

            if auto_execute:
                execute_command(result['command'], logger)
            else:
                if should_execute_command():
                    execute_command(result['command'], logger)


def handle_smart_mode(processor, logger, auto_execute):
    """Handle smart mode - detect context and provide appropriate help."""
    # Try to get the last command and its exit status
    last_command, exit_code = TerminalUtils.get_last_command()

    if last_command and exit_code != 0:
        logger.info(f"Detected failed command: {last_command}")
        # Get the error output if possible
        error_output = TerminalUtils.get_last_error()

        error_context = f"Command '{last_command}' failed"
        if error_output:
            error_context += f" with error: {error_output}"

        result = processor.fix_error(error_context)
        if result:
            logger.info(result['explanation'])
            if 'command' in result and result['command']:
                logger.info(f"\nSuggested fix:")
                logger.info(f"  {result['command']}")

                if auto_execute or should_execute_command():
                    execute_command(result['command'], logger)
    else:
        logger.info(
            "No recent errors detected. Use --help for usage information.")


def should_execute_command():
    """Ask user if they want to execute the suggested command."""
    try:
        response = input("\nExecute this command? [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    except (EOFError, KeyboardInterrupt):
        return False


def execute_command(command, logger):
    """Execute the suggested command."""
    import subprocess
    import shlex

    try:
        logger.info(f"Executing: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            logger.warning(
                f"Command failed with exit code {result.returncode}")
        else:
            logger.info("Command executed successfully!")

    except subprocess.TimeoutExpired:
        logger.error("Command timed out after 30 seconds")
    except Exception as e:
        logger.error(f"Failed to execute command: {e}")


def detect_last_error(logger):
    """Detect the last command error from various sources."""
    logger.debug("Attempting to detect last command error...")

    # Try multiple methods to detect the last error
    error_sources = [
        get_error_from_temp_file,
        get_error_from_shell_history,
        get_error_from_exit_code,
        get_error_from_stderr_capture
    ]

    for source_func in error_sources:
        try:
            error = source_func(logger)
            if error:
                logger.debug(
                    f"Found error from {source_func.__name__}: {error}")
                return error
        except Exception as e:
            logger.debug(f"Error source {source_func.__name__} failed: {e}")

    return None


def get_error_from_temp_file(logger):
    """Get error from temporary file created by shell integration."""
    temp_files = [
        '/tmp/aicmd_last_error',
        '/tmp/aicmd_simple_error',
        '/tmp/aicmd_error_output',
        f'/tmp/aicmd_error_{os.getpid()}'
    ]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                # Check file age - only use if less than 30 seconds old
                file_age = time.time() - os.path.getmtime(temp_file)
                if file_age > 30:  # 30 seconds timeout
                    logger.debug(
                        f"Temp file {temp_file} is too old ({file_age:.1f}s), skipping")
                    continue

                with open(temp_file, 'r') as f:
                    error_content = f.read().strip()
                    if error_content:
                        # Try to get the full command with arguments
                        command_file = '/tmp/aicmd_last_command'
                        if os.path.exists(command_file):
                            try:
                                with open(command_file, 'r') as cmd_f:
                                    full_command = cmd_f.read().strip()
                                    if full_command and full_command not in error_content:
                                        # Enhance error message with full command context
                                        error_content = f"{error_content}\nFailed command: {full_command}"
                            except (IOError, OSError):
                                pass

                        # IMPORTANT: Clean up the temp files after reading to prevent reuse
                        cleanup_temp_files(logger)

                        logger.debug(
                            f"Found error in {temp_file}: {error_content}")
                        return error_content
            except (IOError, OSError):
                continue

    return None


def cleanup_temp_files(logger):
    """Clean up temporary error files to prevent reuse."""
    temp_files = [
        '/tmp/aicmd_last_error',
        '/tmp/aicmd_simple_error',
        '/tmp/aicmd_last_command',
        '/tmp/aicmd_last_exit_code',
        '/tmp/aicmd_current_command',
        '/tmp/aicmd_error_output'
    ]

    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"Cleaned up {temp_file}")
        except OSError:
            pass  # Ignore cleanup errors


def get_error_from_shell_history(logger):
    """Attempt to get error from shell history and exit codes."""
    try:
        # First, try to get from our temporary files
        command_file = '/tmp/aicmd_last_command'
        if os.path.exists(command_file):
            try:
                with open(command_file, 'r') as f:
                    last_command = f.read().strip()
                    if last_command:
                        logger.debug(
                            f"Found command from temp file: {last_command}")
                        # Check if this was a command not found error
                        if os.path.exists('/tmp/aicmd_last_exit_code'):
                            with open('/tmp/aicmd_last_exit_code', 'r') as exit_f:
                                exit_code = exit_f.read().strip()
                                if exit_code == '127':  # Command not found
                                    return f"Command '{last_command}' not found"
                        return f"Command '{last_command}' failed"
            except (IOError, OSError):
                pass

        # Fallback to shell history
        last_command, exit_code = TerminalUtils.get_last_command()

        if last_command and exit_code and exit_code != 0:
            shell = TerminalUtils.get_shell()

            if exit_code == 127:  # Command not found
                return f"Command '{last_command}' not found"
            else:
                error_context = f"Command '{last_command}' failed with exit code {exit_code}"
                return error_context

    except Exception as e:
        logger.debug(f"Could not get error from shell history: {e}")

    return None


def get_error_from_exit_code(logger):
    """Get error information based on the last exit code."""
    try:
        shell = TerminalUtils.get_shell()

        if shell == 'bash':
            result = subprocess.run(['bash', '-c', 'echo $?'],
                                    capture_output=True, text=True, timeout=2)
        elif shell == 'zsh':
            result = subprocess.run(['zsh', '-c', 'echo $?'],
                                    capture_output=True, text=True, timeout=2)
        elif shell == 'fish':
            result = subprocess.run(['fish', '-c', 'echo $status'],
                                    capture_output=True, text=True, timeout=2)
        else:
            return None

        if result.returncode == 0:
            exit_code = result.stdout.strip()
            if exit_code != '0':
                return f"Last command failed with exit code {exit_code}"

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass

    return None


def get_error_from_stderr_capture(logger):
    """Try to get error from captured stderr if available."""
    # Check if there's a recent stderr capture file
    temp_dir = Path('/tmp')
    stderr_files = list(temp_dir.glob('aicmd_stderr_*'))

    if stderr_files:
        # Get the most recent stderr file
        try:
            latest_stderr = max(stderr_files, key=lambda f: f.stat().st_mtime)
            # Only use if it's less than 60 seconds old
            if time.time() - latest_stderr.stat().st_mtime < 60:
                with open(latest_stderr, 'r') as f:
                    stderr_content = f.read().strip()
                    if stderr_content:
                        return stderr_content
        except (OSError, IOError):
            pass

    return None


def show_help():
    """Show interactive mode help."""
    help_text = """
Available commands:
  fix [error_message]     - Fix a command error (auto-detects if no message provided)
  suggest <description>   - Suggest a command for a task
  explain <command>       - Explain what a command does
  help                   - Show this help message
  quit/exit/q           - Exit interactive mode

You can also just type a description and it will be treated as a suggestion request.
"""
    print(help_text)


if __name__ == '__main__':
    main()
