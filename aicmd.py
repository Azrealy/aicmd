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
        choices=['fix', 'suggest', 'explain', 'setup'],
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
        elif args.interactive:
            interactive_mode(processor, logger)
        elif args.action and args.input_text:
            input_str = ' '.join(args.input_text)
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
                if not text:
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
            logger.info("\nSuggested command:", 'bright_yellow')
            logger.info(f"  {result['command']}", 'bright_red')

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
                logger.info("\nSuggested fix:")
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


def show_help():
    """Show interactive mode help."""
    help_text = """
Available commands:
  fix <error_message>     - Fix a command error
  suggest <description>   - Suggest a command for a task
  explain <command>       - Explain what a command does
  help                   - Show this help message
  quit/exit/q           - Exit interactive mode

You can also just type a description and it will be treated as a suggestion request.
"""
    print(help_text)


if __name__ == '__main__':
    main()
