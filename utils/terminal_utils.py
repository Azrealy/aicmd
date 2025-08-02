"""
Terminal Utilities - Helper functions for terminal interaction
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Tuple, List


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
    def get_last_command_with_error() -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """Get the last executed command, its exit code, and any error output."""
        command, exit_code = TerminalUtils.get_last_command()
        error_output = TerminalUtils.get_last_error()

        return command, exit_code, error_output

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
            # First, try to get from our temp files (more reliable)
            if os.path.exists('/tmp/aicmd_last_command') and os.path.exists('/tmp/aicmd_last_exit_code'):
                try:
                    with open('/tmp/aicmd_last_command', 'r') as f:
                        command = f.read().strip()
                    with open('/tmp/aicmd_last_exit_code', 'r') as f:
                        exit_code = int(f.read().strip())
                    if command:
                        return command, exit_code
                except (IOError, ValueError):
                    pass

            # Fallback to fish history command
            result = subprocess.run(
                ['fish', '-c', 'history --max=1'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                last_command = result.stdout.strip()

                # Get exit code from fish
                exit_result = subprocess.run(
                    ['fish', '-c', 'echo $status'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                exit_code = None
                if exit_result.returncode == 0 and exit_result.stdout.strip().isdigit():
                    exit_code = int(exit_result.stdout.strip())

                return last_command, exit_code

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
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
    def capture_command_error(command: str, error_output: str, exit_code: int):
        """Capture command error information for later retrieval."""
        try:
            timestamp = int(time.time())
            error_data = {
                'command': command,
                'error_output': error_output,
                'exit_code': exit_code,
                'timestamp': timestamp,
                'cwd': os.getcwd()
            }

            # Save to multiple locations for reliability
            temp_files = [
                f'/tmp/aicmd_last_error',
                f'/tmp/aicmd_error_{os.getpid()}',
                f'/tmp/aicmd_error_latest'
            ]

            # Create a formatted error message
            if error_output.strip():
                formatted_error = f"Command '{command}' failed with exit code {exit_code}:\n{error_output}"
            else:
                formatted_error = f"Command '{command}' failed with exit code {exit_code}"

            for temp_file in temp_files:
                try:
                    with open(temp_file, 'w') as f:
                        f.write(formatted_error)
                except (IOError, OSError):
                    continue

            # Also save detailed JSON data
            import json
            try:
                with open('/tmp/aicmd_error_data.json', 'w') as f:
                    json.dump(error_data, f)
            except (IOError, OSError, ImportError):
                pass

        except Exception:
            pass  # Fail silently to not interfere with user's workflow

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
aicmd_capture_error() {
    local exit_code=$?
    local last_command=$(fc -ln -1 2>/dev/null | sed 's/^[ \t]*//')
    
    # IMPORTANT: Avoid infinite loops - don't capture aicmd errors
    if [[ "$last_command" =~ ^aicmd.* ]]; then
        return $exit_code
    fi
    
    if [ $exit_code -ne 0 ] && [ -n "$last_command" ]; then
        # Create error message with timestamp
        local timestamp=$(date +%s)
        local error_msg="Command '$last_command' failed with exit code $exit_code"
        
        # Save to temporary file for aicmd to detect
        echo "$error_msg" > /tmp/aicmd_last_error
        echo "$last_command" > /tmp/aicmd_last_command
        echo "$exit_code" > /tmp/aicmd_last_exit_code
        echo "$timestamp" > /tmp/aicmd_timestamp
        
        # Show hint if auto-suggest is enabled
        if [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
            echo "💡 Tip: Run 'aicmd fix' to get help with this error"
        fi
    fi
    
    return $exit_code
}

# Set up error capture using trap
trap 'aicmd_capture_error' ERR

# Enhanced command not found handler
command_not_found_handle() {
    local cmd="$1"
    shift  # Remove the first argument
    local args="$*"  # Get remaining arguments as string
    
    # IMPORTANT: Avoid infinite loops - don't handle aicmd command not found
    if [[ "$cmd" =~ ^aicmd.* ]]; then
        echo "bash: $cmd: command not found"
        echo "💡 Make sure aicmd is installed and in your PATH"
        return 127
    fi
    
    # Save detailed error information
    local timestamp=$(date +%s)
    if [ -n "$args" ]; then
        local full_command="$cmd $args"
        echo "bash: $cmd: command not found (full command: $full_command)" > /tmp/aicmd_last_error
        echo "$full_command" > /tmp/aicmd_last_command
    else
        echo "bash: $cmd: command not found" > /tmp/aicmd_last_error
        echo "$cmd" > /tmp/aicmd_last_command
    fi
    
    echo "127" > /tmp/aicmd_last_exit_code
    echo "$timestamp" > /tmp/aicmd_timestamp
    
    # Also create a simple error format for better detection
    echo "Command '$cmd' not found" > /tmp/aicmd_simple_error
    
    if [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
        echo "💡 Tip: Run 'aicmd fix' to get help finding this command"
    fi
    
    echo "bash: $cmd: command not found"
    return 127
}

# Cleanup function
aicmd_cleanup() {
    local temp_files="/tmp/aicmd_last_error /tmp/aicmd_simple_error /tmp/aicmd_last_command /tmp/aicmd_last_exit_code /tmp/aicmd_current_command /tmp/aicmd_timestamp"
    for file in $temp_files; do
        if [ -f "$file" ]; then
            # Remove files older than 1 minute
            if [ $(($(date +%s) - $(stat -c %Y "$file" 2>/dev/null || echo 0))) -gt 60 ]; then
                rm -f "$file"
            fi
        fi
    done
}

# Optional: Enable auto-suggestions
# export AICMD_AUTO_SUGGEST=1
'''

        elif shell == 'zsh':
            return '''
# AI Command Tool Integration for Zsh
export AICMD_SHELL="zsh"

# Function to capture command errors
aicmd_capture_error() {
    local exit_code=$?
    local last_command=$(fc -ln -1 2>/dev/null)
    
    if [ $exit_code -ne 0 ] && [ -n "$last_command" ]; then
        # Create error message
        local error_msg="Command '$last_command' failed with exit code $exit_code"
        
        # Save to temporary file for aicmd to detect
        echo "$error_msg" > /tmp/aicmd_last_error
        echo "$last_command" > /tmp/aicmd_last_command
        echo "$exit_code" > /tmp/aicmd_last_exit_code
        
        # Show hint if auto-suggest is enabled
        if [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
            echo "💡 Tip: Run 'aicmd fix' to get help with this error"
        fi
    fi
    
    return $exit_code
}

# Set up error capture using precmd hook
autoload -U add-zsh-hook
add-zsh-hook precmd aicmd_capture_error

# Enhanced command not found handler
command_not_found_handler() {
    local cmd="$1"
    shift  # Remove the first argument
    local args="$@"  # Get remaining arguments
    local full_command="$cmd $args"
    
    # Save detailed error information
    echo "Command not found: $cmd" > /tmp/aicmd_last_error
    echo "$full_command" > /tmp/aicmd_last_command
    echo "127" > /tmp/aicmd_last_exit_code
    
    # Create a formatted error message with the full command
    if [ -n "$args" ]; then
        echo "zsh: command not found: $cmd (full command: $full_command)" > /tmp/aicmd_last_error
    else
        echo "zsh: command not found: $cmd" > /tmp/aicmd_last_error
    fi
    
    if [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
        echo "💡 Tip: Run 'aicmd fix' to get help finding this command"
    fi
    
    echo "zsh: command not found: $cmd"
    return 127
}

# Optional: Enable auto-suggestions
# export AICMD_AUTO_SUGGEST=1
'''

        elif shell == 'fish':
            return '''
# AI Command Tool Integration for Fish
set -gx AICMD_SHELL "fish"

# Function to capture command errors using fish's event system
function aicmd_capture_error --on-event fish_postexec
    set -l exit_code $status
    set -l last_command $argv[1]
    
    # IMPORTANT: Avoid infinite loops - don't capture aicmd errors
    if string match -q "aicmd*" "$last_command"
        return
    end
    
    if test $exit_code -ne 0 -a -n "$last_command"
        # Create error message with timestamp for freshness check
        set -l timestamp (date +%s)
        set -l error_msg "Command '$last_command' failed with exit code $exit_code"
        
        # Save to temporary file for aicmd to detect
        echo "$error_msg" > /tmp/aicmd_last_error
        echo "$last_command" > /tmp/aicmd_last_command
        echo "$exit_code" > /tmp/aicmd_last_exit_code
        echo "$timestamp" > /tmp/aicmd_timestamp
        
        # Show hint if auto-suggest is enabled
        if test "$AICMD_AUTO_SUGGEST" = "1"
            echo "💡 Tip: Run 'aicmd fix' to get help with this error"
        end
    end
end

# Enhanced command not found handler for Fish
function fish_command_not_found
    set -l cmd $argv[1]
    set -l remaining_args $argv[2..-1]
    
    # IMPORTANT: Avoid infinite loops - don't handle aicmd command not found
    if string match -q "aicmd*" "$cmd"
        echo "fish: Unknown command: $cmd"
        echo "💡 Make sure aicmd is installed and in your PATH"
        return 127
    end
    
    # Build full command string
    if test (count $remaining_args) -gt 0
        set -l full_command "$cmd "(string join " " $remaining_args)
        echo "fish: Unknown command: $cmd (full command: $full_command)" > /tmp/aicmd_last_error
        echo "$full_command" > /tmp/aicmd_last_command
    else
        echo "fish: Unknown command: $cmd" > /tmp/aicmd_last_error
        echo "$cmd" > /tmp/aicmd_last_command
    end
    
    echo "127" > /tmp/aicmd_last_exit_code
    echo (date +%s) > /tmp/aicmd_timestamp
    
    # Create simple error format for better detection
    echo "Command '$cmd' not found" > /tmp/aicmd_simple_error
    
    if test "$AICMD_AUTO_SUGGEST" = "1"
        echo "💡 Tip: Run 'aicmd fix' to get help finding this command"
    end
    
    echo "fish: Unknown command: $cmd"
end

# Fish-specific function to handle command completion errors
function aicmd_preexec --on-event fish_preexec
    # IMPORTANT: Don't capture aicmd commands to avoid loops
    if not string match -q "aicmd*" "$argv"
        # Store the command that's about to be executed
        echo "$argv" > /tmp/aicmd_current_command
    end
end

# Cleanup function to remove old temp files
function aicmd_cleanup
    set -l temp_files /tmp/aicmd_last_error /tmp/aicmd_simple_error /tmp/aicmd_last_command /tmp/aicmd_last_exit_code /tmp/aicmd_current_command /tmp/aicmd_timestamp
    for file in $temp_files
        if test -f $file
            # Remove files older than 1 minute
            if test (math (date +%s) - (stat -c %Y $file 2>/dev/null || echo 0)) -gt 60
                rm -f $file
            end
        end
    end
end

# Run cleanup periodically (every 10 commands)
set -g aicmd_command_count 0
function aicmd_periodic_cleanup --on-event fish_postexec
    set -g aicmd_command_count (math $aicmd_command_count + 1)
    if test (math $aicmd_command_count % 10) -eq 0
        aicmd_cleanup
    end
end

# Fish-specific aliases for convenience
alias aicmd-enable-auto 'set -gx AICMD_AUTO_SUGGEST 1'
alias aicmd-disable-auto 'set -e AICMD_AUTO_SUGGEST'
alias aicmd-cleanup 'aicmd_cleanup'

# Optional: Enable auto-suggestions
# set -gx AICMD_AUTO_SUGGEST 1
'''

        else:
            return f'# AI Command Tool: Shell "{shell}" not supported for integration'
