"""
Logger - Utilities for logging and output formatting
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """Enhanced logger with color support and different output levels."""

    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
    }

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        self.verbose = verbose
        self.supports_color = self._supports_color()
        self.log_file = log_file

        # Setup file logging if requested
        if log_file:
            self._setup_file_logging(log_file)

    def _supports_color(self) -> bool:
        """Check if terminal supports color output."""
        return (
            os.getenv('TERM', '').lower() != 'dumb' and
            hasattr(sys.stdout, 'isatty') and
            sys.stdout.isatty() and
            os.getenv('NO_COLOR') is None
        )

    def _setup_file_logging(self, log_file: str):
        """Setup file logging."""
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def _colorize(self, text: str, color: str) -> str:
        """Add color to text if color is supported."""
        if self.supports_color and color in self.COLORS:
            return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
        return text

    def _format_timestamp(self) -> str:
        """Get formatted timestamp for verbose output."""
        return datetime.now().strftime('%H:%M:%S')

    def info(self, message: str, color: str = 'white'):
        """Log info message."""
        formatted_message = self._colorize(message, color)

        if self.verbose:
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {formatted_message}")
        else:
            print(formatted_message)

        if self.log_file:
            logging.info(message)

    def success(self, message: str):
        """Log success message."""
        icon = self._colorize("✓", 'bright_green')
        formatted_message = self._colorize(message, 'bright_green')

        if self.verbose:
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {icon} {formatted_message}")
        else:
            print(f"{icon} {formatted_message}")

        if self.log_file:
            logging.info(f"SUCCESS: {message}")

    def warning(self, message: str):
        """Log warning message."""
        icon = self._colorize("⚠", 'bright_yellow')
        formatted_message = self._colorize(message, 'bright_yellow')

        if self.verbose:
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {icon} {formatted_message}")
        else:
            print(f"{icon} {formatted_message}")

        if self.log_file:
            logging.warning(message)

    def error(self, message: str):
        """Log error message."""
        icon = self._colorize("✗", 'bright_red')
        formatted_message = self._colorize(message, 'bright_red')

        if self.verbose:
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {icon} {formatted_message}", file=sys.stderr)
        else:
            print(f"{icon} {formatted_message}", file=sys.stderr)

        if self.log_file:
            logging.error(message)

    def debug(self, message: str):
        """Log debug message (only shown in verbose mode)."""
        if self.verbose:
            icon = self._colorize("🐛", 'cyan')
            formatted_message = self._colorize(message, 'cyan')
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {icon} {formatted_message}")

        if self.log_file:
            logging.debug(message)

    def command(self, command: str):
        """Log a command that will be executed."""
        icon = self._colorize("$", 'blue')
        formatted_command = self._colorize(command, 'bright_blue')

        if self.verbose:
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {icon} {formatted_command}")
        else:
            print(f"{icon} {formatted_command}")

        if self.log_file:
            logging.info(f"COMMAND: {command}")

    def ai_response(self, response: str):
        """Log AI response with special formatting."""
        icon = self._colorize("🤖", 'magenta')

        if self.verbose:
            timestamp = self._colorize(f"[{self._format_timestamp()}]", 'dim')
            print(f"{timestamp} {icon} AI Response:")
        else:
            print(f"{icon} AI Response:")

        # Format the response with proper indentation
        lines = response.split('\n')
        for line in lines:
            if line.strip():
                print(f"   {line}")
            else:
                print()

        if self.log_file:
            logging.info(f"AI_RESPONSE: {response}")

    def section_header(self, title: str):
        """Print a section header."""
        if self.supports_color:
            border = self._colorize("═" * 50, 'blue')
            header = self._colorize(f" {title} ", 'bright_white')
            print(f"{border}")
            print(f"{header}")
            print(f"{border}")
        else:
            print(f"\n{'=' * 50}")
            print(f" {title} ")
            print(f"{'=' * 50}")

        if self.log_file:
            logging.info(f"SECTION: {title}")

    def progress(self, message: str):
        """Show progress message."""
        if self.supports_color:
            spinner = self._colorize("⏳", 'yellow')
            formatted_message = self._colorize(message, 'yellow')
            print(f"{spinner} {formatted_message}", end='', flush=True)
        else:
            print(f"⏳ {message}", end='', flush=True)

    def progress_done(self, message: str = "Done"):
        """Complete progress message."""
        print(f"\r{self._colorize('✓', 'green')} {self._colorize(message, 'green')}")

        if self.log_file:
            logging.info(f"PROGRESS_DONE: {message}")

    def table_row(self, *columns, headers=False):
        """Print a table row."""
        if headers:
            row = " | ".join(str(col).ljust(15) for col in columns)
            print(self._colorize(row, 'bold'))
            print(self._colorize("-" * len(row), 'dim'))
        else:
            row = " | ".join(str(col).ljust(15) for col in columns)
            print(row)

    def separator(self, char: str = "-", length: int = 50):
        """Print a separator line."""
        line = char * length
        print(self._colorize(line, 'dim'))

    def json_output(self, data: dict, pretty: bool = True):
        """Output JSON data."""
        import json

        if pretty:
            json_str = json.dumps(data, indent=2)
        else:
            json_str = json.dumps(data)

        if self.supports_color:
            # Simple JSON syntax highlighting
            json_str = json_str.replace('"', self._colorize('"', 'green'))
            json_str = json_str.replace(':', self._colorize(':', 'blue'))
            json_str = json_str.replace(',', self._colorize(',', 'blue'))

        print(json_str)

        if self.log_file:
            logging.info(f"JSON_OUTPUT: {json.dumps(data)}")

    def code_block(self, code: str, language: str = ""):
        """Display a code block."""
        if language:
            header = self._colorize(f"```{language}", 'dim')
            print(header)
        else:
            print(self._colorize("```", 'dim'))

        for line in code.split('\n'):
            print(f"  {line}")

        print(self._colorize("```", 'dim'))

        if self.log_file:
            logging.info(f"CODE_BLOCK ({language}): {code}")

    def banner(self, text: str):
        """Display a banner message."""
        width = max(len(text) + 4, 50)
        border = "=" * width

        print(self._colorize(border, 'bright_blue'))
        print(self._colorize(f"  {text.center(width-4)}  ", 'bright_white'))
        print(self._colorize(border, 'bright_blue'))

        if self.log_file:
            logging.info(f"BANNER: {text}")
