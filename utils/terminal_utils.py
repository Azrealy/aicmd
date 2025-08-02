"""
Terminal Utilities - Helper functions for terminal interaction
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple


class TerminalUtils:
    """Utilities for interacting with the terminal environment."""

    @staticmethod
    def get_shell() -> str:
        """Get the current shell."""
        shell = os.getenv('SHELL', '/bin/bash')
        return Path(shell).name

    @staticmethod
    def get_last_command() -> Tuple[Optional[str], Optional[int]]:
        """Get the last executed command and its exit code."""
        shell = TerminalUtils.get_shell()

        try:
            if shell == 'bash':
                return TerminalUtils._get_bash_last_command()
            elif shell == 'zsh':
                return TerminalUtils._get_zsh_last_command()
            elif shell == 'fish':
                return TerminalUtils._get_fish_last_command()
            else:
                return None, None
        except Exception:
            return None, None

    @staticmethod
    def _get_bash_last_command() -> Tuple[Optional[str], Optional[int]]:
        """Get last command from bash history."""
        try:
            # Try to get from HISTFILE or default location
            hist_file = os.getenv(
                'HISTFILE', os.path.expanduser('~/.bash_history'))

            if os.path.exists(hist_file):
                with open(hist_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_command = lines[-1].strip()
                        # Get exit code from $?
                        result = subprocess.run(
                            ['bash', '-c', 'echo $?'],
                            capture_output=True,
                            text=True
                        )
                        exit_code = int(result.stdout.strip(
                        )) if result.stdout.strip().isdigit() else None
                        return last_command, exit_code
        except Exception:
            pass

        return None, None

    @staticmethod
    def _get_zsh_last_command() -> Tuple[Optional[str], Optional[int]]:
        """Get last command from zsh history."""
        try:
            hist_file = os.getenv(
                'HISTFILE', os.path.expanduser('~/.zsh_history'))

            if os.path.exists(hist_file):
                with open(hist_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Zsh history format might include timestamps
                        last_line = lines[-1].strip()
                        if ';' in last_line:
                            last_command = last_line.split(';', 1)[1]
                        else:
                            last_command = last_line

                        # Get exit code
                        result = subprocess.run(
                            ['zsh', '-c', 'echo $?'],
                            capture_output=True,
                            text=True
                        )
                        exit_code = int(result.stdout.strip(
                        )) if result.stdout.strip().isdigit() else None
                        return last_command, exit_code
        except Exception:
            pass

        return None, None

    @staticmethod
    def _get_fish_last_command() -> Tuple[Optional[str], Optional[int]]:
        """Get last command from fish history."""
        try:
            # Fish stores history differently
            result = subprocess.run(
                ['fish', '-c', 'history --max=1'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                last_command = result.stdout.strip()

                # Get exit code
                exit_result = subprocess.run(
                    ['fish', '-c', 'echo $status'],
                    capture_output=True,
                    text=True
                )
                exit_code = int(exit_result.stdout.strip(
                )) if exit_result.stdout.strip().isdigit() else None
                return last_command, exit_code
        except Exception:
            pass

        return None, None

    @staticmethod
    def get_last_error() -> Optional[str]:
        """Attempt to get the last error output."""
        # This is challenging since stderr is usually not persisted
        # We can try a few approaches

        try:
            # Check if there's a temporary error log
            temp_dir = Path(tempfile.gettempdir())
            error_files = list(temp_dir.glob('aicmd_error_*'))

            if error_files:
                # Get the most recent error file
                latest_error = max(
                    error_files, key=lambda f: f.stat().st_mtime)
                with open(latest_error, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass

        return None

    @staticmethod
    def save_error_output(error_text: str):
        """Save error output for later retrieval."""
        try:
            temp_dir = Path(tempfile.gettempdir())
            error_file = temp_dir / f'aicmd_error_{os.getpid()}'

            with open(error_file, 'w') as f:
                f.write(error_text)
        except Exception:
            pass

    @staticmethod
    def get_terminal_size() -> Tuple[int, int]:
        """Get terminal size (columns, rows)."""
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except OSError:
            return 80, 24  # Default fallback

    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports color output."""
        return (
            os.getenv('TERM', '').lower() != 'dumb' and
            hasattr(os.sys.stdout, 'isatty') and
            os.sys.stdout.isatty()
        )

    @staticmethod
    def get_working_directory() -> str:
        """Get current working directory."""
        return os.getcwd()

    @staticmethod
    def is_command_available(command: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            subprocess.run(
                ['which', command],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_environment_info() -> dict:
        """Get relevant environment information."""
        return {
            'shell': TerminalUtils.get_shell(),
            'term': os.getenv('TERM', 'unknown'),
            'user': os.getenv('USER', 'unknown'),
            'home': os.getenv('HOME', 'unknown'),
            'path': os.getenv('PATH', ''),
            'pwd': os.getcwd(),
            'supports_color': TerminalUtils.supports_color(),
            'terminal_size': TerminalUtils.get_terminal_size()
        }

    @staticmethod
    def setup_shell_integration(shell: str = None) -> str:
        """Generate shell integration code for the specified shell."""
        if shell is None:
            shell = TerminalUtils.get_shell()

        if shell == 'bash':
            return '''
# AI Command Tool Integration for Bash
export AICMD_SHELL="bash"

# Function to capture command errors
aicmd_error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        local last_command=$(fc -ln -1)
        echo "Command failed with exit code $exit_code: $last_command" > /tmp/aicmd_last_error
    fi
    return $exit_code
}

# Set up error capture
trap 'aicmd_error_handler' ERR

# Command not found handler
command_not_found_handle() {
    echo "Command not found: $1" > /tmp/aicmd_last_error
    aicmd fix "Command not found: $1" 2>/dev/null || echo "bash: $1: command not found"
}
'''

        elif shell == 'zsh':
            return '''
# AI Command Tool Integration for Zsh
export AICMD_SHELL="zsh"

# Function to capture command errors
aicmd_error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        local last_command=$(fc -ln -1)
        echo "Command failed with exit code $exit_code: $last_command" > /tmp/aicmd_last_error
    fi
    return $exit_code
}

# Set up error capture
autoload -U add-zsh-hook
add-zsh-hook precmd aicmd_error_handler

# Command not found handler
command_not_found_handler() {
    echo "Command not found: $1" > /tmp/aicmd_last_error
    aicmd fix "Command not found: $1" 2>/dev/null || echo "zsh: command not found: $1"
}
'''

        elif shell == 'fish':
            return '''
# AI Command Tool Integration for Fish
set -gx AICMD_SHELL "fish"

# Function to handle command not found
function fish_command_not_found
    echo "Command not found: $argv[1]" > /tmp/aicmd_last_error
    aicmd fix "Command not found: $argv[1]" 2>/dev/null; or echo "fish: Unknown command: $argv[1]"
end
'''

        else:
            return f'# AI Command Tool: Shell "{shell}" not supported for integration'
