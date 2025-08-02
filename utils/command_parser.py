"""
Command Parser - Utilities for parsing and analyzing commands
"""

import re
import shlex
from typing import Optional, List, Dict, Tuple


class CommandParser:
    """Parser for command-line commands and error messages."""

    def __init__(self):
        # Common error patterns
        self.error_patterns = [
            # Command not found
            (r"bash: (.+): command not found", "command_not_found"),
            (r"zsh: command not found: (.+)", "command_not_found"),
            (r"fish: Unknown command[: ]*(.+)", "command_not_found"),
            (r"'(.+)' is not recognized as an internal or external command",
             "command_not_found"),

            # File/directory errors
            (r"No such file or directory[: ]*(.+)", "file_not_found"),
            (r"cannot access[: ]*(.+)", "file_not_found"),
            (r"Permission denied[: ]*(.+)", "permission_denied"),

            # Network errors
            (r"curl: \(\d+\) (.+)", "network_error"),
            (r"wget: (.+)", "network_error"),
            (r"Connection refused", "connection_refused"),

            # Package manager errors
            (r"E: Unable to locate package (.+)", "package_not_found"),
            (r"No package '(.+)' found", "package_not_found"),
            (r"brew: command not found", "homebrew_not_installed"),

            # Git errors
            (r"fatal: not a git repository", "not_git_repo"),
            (r"error: pathspec '(.+)' did not match any file", "git_pathspec_error"),

            # Docker errors
            (r"docker: Error response from daemon: (.+)", "docker_error"),
            (r"Cannot connect to the Docker daemon", "docker_daemon_error"),

            # Python errors
            (r"ModuleNotFoundError: No module named '(.+)'", "python_module_not_found"),
            (r"SyntaxError: (.+)", "python_syntax_error"),

            # Node.js/npm errors
            (r"npm ERR! (.+)", "npm_error"),
            (r"Error: Cannot find module '(.+)'", "node_module_not_found"),
        ]

    def extract_command_from_error(self, error_text: str) -> Optional[str]:
        """Extract the failed command from error text."""
        # Try to find command in common error formats
        patterns = [
            r"Command '(.+)' failed",
            r"bash: (.+): command not found",
            r"zsh: command not found: (.+)",
            r"fish: Unknown command[: ]*(.+)",
            r"Error running command: (.+)",
            r"Failed to execute: (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_text)
            if match:
                return match.group(1).strip()

        # Try to extract from shell prompt context
        lines = error_text.split('\n')
        for line in lines:
            # Look for lines that start with $ or contain shell prompts
            if re.match(r'^\$\s+(.+)', line.strip()):
                return re.match(r'^\$\s+(.+)', line.strip()).group(1)

            # Look for lines that might be commands (no spaces at start, contain command-like text)
            if not line.startswith(' ') and any(cmd in line for cmd in ['ls', 'cd', 'git', 'npm', 'pip', 'docker']):
                return line.strip()

        return None

    def categorize_error(self, error_text: str) -> Tuple[str, Optional[str]]:
        """Categorize the type of error and extract relevant information."""
        for pattern, category in self.error_patterns:
            match = re.search(pattern, error_text, re.IGNORECASE)
            if match:
                extracted = match.group(1) if match.groups() else None
                return category, extracted

        return "unknown_error", None

    def parse_command(self, command: str) -> Dict:
        """Parse a command into its components."""
        try:
            # Use shlex to properly handle quoted arguments
            parts = shlex.split(command)
        except ValueError:
            # If shlex fails, fallback to simple split
            parts = command.split()

        if not parts:
            return {
                'command': '',
                'base_command': '',
                'arguments': [],
                'flags': [],
                'options': {},
                'redirections': []
            }

        base_command = parts[0]
        arguments = []
        flags = []
        options = {}
        redirections = []

        i = 1
        while i < len(parts):
            part = parts[i]

            # Check for redirections
            if part in ['>', '>>', '<', '|', '2>', '2>>', '&>', '&>>']:
                if i + 1 < len(parts):
                    redirections.append((part, parts[i + 1]))
                    i += 2
                else:
                    redirections.append((part, ''))
                    i += 1
                continue

            # Check for flags (start with -)
            if part.startswith('-'):
                if '=' in part:
                    # Option with value (--option=value)
                    key, value = part.split('=', 1)
                    options[key] = value
                elif i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    # Option with separate value (--option value)
                    options[part] = parts[i + 1]
                    i += 2
                    continue
                else:
                    # Simple flag
                    flags.append(part)
            else:
                # Regular argument
                arguments.append(part)

            i += 1

        return {
            'command': command,
            'base_command': base_command,
            'arguments': arguments,
            'flags': flags,
            'options': options,
            'redirections': redirections
        }

    def suggest_command_fixes(self, failed_command: str, error_category: str) -> List[str]:
        """Suggest possible fixes for a failed command."""
        suggestions = []
        parsed = self.parse_command(failed_command)
        base_cmd = parsed['base_command']

        if error_category == "command_not_found":
            suggestions.extend(self._suggest_command_alternatives(base_cmd))
        elif error_category == "permission_denied":
            suggestions.append(f"sudo {failed_command}")
            suggestions.append(f"chmod +x {' '.join(parsed['arguments'])}")
        elif error_category == "file_not_found":
            suggestions.extend(self._suggest_file_fixes(parsed))
        elif error_category == "package_not_found":
            suggestions.extend(self._suggest_package_install(
                base_cmd, parsed['arguments']))

        return suggestions

    def _suggest_command_alternatives(self, command: str) -> List[str]:
        """Suggest alternative commands for command not found errors."""
        alternatives = {
            'ls': ['dir', 'find . -maxdepth 1'],
            'll': ['ls -la', 'ls -l'],
            'cat': ['type', 'more', 'less'],
            'grep': ['findstr', 'select-string'],
            'ps': ['Get-Process', 'tasklist'],
            'kill': ['Stop-Process', 'taskkill'],
            'wget': ['curl -O', 'Invoke-WebRequest'],
            'curl': ['wget', 'Invoke-RestMethod'],
            'python': ['python3', 'py'],
            'pip': ['pip3', 'python -m pip'],
            'node': ['nodejs'],
            'npm': ['yarn', 'pnpm'],
            'git': ['Install git first'],
            'docker': ['Install Docker first'],
            'vim': ['nano', 'code', 'notepad'],
            'nano': ['vim', 'code', 'notepad'],
        }

        suggestions = alternatives.get(command, [])

        # Add common typo corrections
        typo_corrections = {
            'gti': 'git',
            'cd..': 'cd ..',
            'ks': 'ls',
            'sl': 'ls',
            'clar': 'clear',
            'claer': 'clear',
            'grpe': 'grep',
            'mkdi': 'mkdir',
            'toutch': 'touch',
        }

        if command in typo_corrections:
            suggestions.insert(0, typo_corrections[command])

        return suggestions

    def _suggest_file_fixes(self, parsed: Dict) -> List[str]:
        """Suggest fixes for file not found errors."""
        suggestions = []

        for arg in parsed['arguments']:
            if arg and not arg.startswith('-'):
                # Suggest creating the file/directory
                if '.' in arg:
                    suggestions.append(f"touch {arg}")
                else:
                    suggestions.append(f"mkdir -p {arg}")

                # Suggest finding similar files
                suggestions.append(f"find . -name '*{arg}*' -type f")
                suggestions.append(f"ls -la | grep {arg}")

        return suggestions

    def _suggest_package_install(self, package_manager: str, packages: List[str]) -> List[str]:
        """Suggest package installation commands."""
        suggestions = []

        for pkg in packages:
            if pkg and not pkg.startswith('-'):
                if package_manager in ['apt', 'apt-get']:
                    suggestions.append(
                        f"sudo apt update && sudo apt install {pkg}")
                elif package_manager == 'yum':
                    suggestions.append(f"sudo yum install {pkg}")
                elif package_manager == 'dnf':
                    suggestions.append(f"sudo dnf install {pkg}")
                elif package_manager == 'brew':
                    suggestions.append(f"brew install {pkg}")
                elif package_manager == 'pip':
                    suggestions.append(f"pip install {pkg}")
                elif package_manager == 'npm':
                    suggestions.append(f"npm install {pkg}")

        return suggestions

    def is_safe_command(self, command: str) -> Tuple[bool, str]:
        """Check if a command is safe to execute."""
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+\*',
            r'dd\s+if=',
            r'mkfs\.',
            r'fdisk',
            r'format\s+[A-Z]:',
            r'shutdown',
            r'reboot',
            r'halt',
            r'init\s+[06]',
            r':\(\)\{\s*:\|:\&\s*\}\s*;:',  # Fork bomb
            r'chmod\s+-R\s+777\s+/',
            r'chown\s+-R',
            r'curl.*\|\s*sh',
            r'wget.*\|\s*sh',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Potentially dangerous command detected: {pattern}"

        return True, "Command appears safe"
