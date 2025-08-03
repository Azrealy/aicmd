"""
History Manager - Handles command history with arrow key navigation
"""

import readline
from pathlib import Path
from typing import List


class HistoryManager:
    """Manages command history for interactive modes."""

    def __init__(self, history_type: str = "general"):
        self.history_type = history_type
        self.history_file = self._get_history_file()
        self.current_session = []
        self.setup_readline()

    def _get_history_file(self) -> Path:
        """Get the history file path."""
        aicmd_dir = Path.home() / '.aicmd'
        aicmd_dir.mkdir(exist_ok=True)

        if self.history_type == "chat":
            return aicmd_dir / 'chat_history.txt'
        else:
            return aicmd_dir / 'interactive_history.txt'

    def setup_readline(self):
        """Setup readline for arrow key navigation and history."""
        try:
            # Load existing history
            if self.history_file.exists():
                readline.read_history_file(str(self.history_file))

            # Configure readline
            readline.set_history_length(1000)  # Keep last 1000 commands

            # Enable tab completion (basic)
            readline.parse_and_bind('tab: complete')

            # Enable history search with Ctrl+R
            readline.parse_and_bind('"\C-r": reverse-search-history')

            # Enable arrow key navigation (should work by default)
            readline.parse_and_bind('"\e[A": previous-history')  # Up arrow
            readline.parse_and_bind('"\e[B": next-history')      # Down arrow

        except Exception as e:
            # readline might not be available on all systems
            print(f"Warning: Could not setup readline: {e}")

    def add_command(self, command: str):
        """Add a command to history."""
        if not command or command.strip() in ['', 'help', 'quit', 'exit', 'q', 'clear']:
            return

        command = command.strip()

        # Add to current session
        self.current_session.append(command)

        # Add to readline history
        try:
            readline.add_history(command)
        except:
            pass

        # Save to file
        self._save_to_file(command)

    def _save_to_file(self, command: str):
        """Save command to history file."""
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(f"{command}\n")
        except Exception as e:
            # Silently fail if we can't write to history
            pass

    def get_history(self, limit: int = 50) -> List[str]:
        """Get recent history entries."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Return last N lines, cleaned up
                    return [line.strip() for line in lines[-limit:] if line.strip()]
            return []
        except Exception:
            return []

    def clear_history(self):
        """Clear all history."""
        try:
            # Clear readline history
            readline.clear_history()

            # Clear history file
            if self.history_file.exists():
                self.history_file.unlink()

            # Clear current session
            self.current_session = []

        except Exception as e:
            print(f"Warning: Could not clear history: {e}")

    def show_history(self, limit: int = 20):
        """Show recent history entries."""
        history = self.get_history(limit)
        if not history:
            print("No history found.")
            return

        print(f"\n📝 Recent History (last {len(history)} commands):")
        print("=" * 50)
        for i, cmd in enumerate(history[-limit:], 1):
            print(f"{i:2d}. {cmd}")
        print()

    def search_history(self, query: str) -> List[str]:
        """Search history for commands containing the query."""
        history = self.get_history()
        return [cmd for cmd in history if query.lower() in cmd.lower()]

    def save_session(self):
        """Save the readline history to file on exit."""
        try:
            readline.write_history_file(str(self.history_file))
        except Exception:
            pass

    def get_input_with_history(self, prompt: str) -> str:
        """Get input with history support."""
        try:
            # Use readline for input with history support
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            # Fallback to regular input if readline fails
            return input(prompt)


class AdvancedHistoryManager(HistoryManager):
    """Enhanced history manager with more features."""

    def __init__(self, history_type: str = "general"):
        super().__init__(history_type)
        self.setup_advanced_features()

    def setup_advanced_features(self):
        """Setup advanced readline features."""
        try:
            # Custom key bindings for better UX
            readline.parse_and_bind(
                '"\C-l": clear-screen')       # Ctrl+L to clear
            # Ctrl+U to clear line
            readline.parse_and_bind('"\C-u": unix-line-discard')
            # Ctrl+W to delete word
            readline.parse_and_bind('"\C-w": unix-word-rubout')

            # History expansion
            readline.parse_and_bind('set expand-tilde on')
            readline.parse_and_bind('set completion-ignore-case on')

        except Exception:
            pass

    def add_command_with_metadata(self, command: str, result_type: str = "unknown"):
        """Add command with metadata (timestamp, type, etc.)."""
        if not command or command.strip() in ['', 'help', 'quit', 'exit', 'q', 'clear']:
            return

        command = command.strip()

        # Add to readline history
        self.add_command(command)

        # Save with metadata
        try:
            import time
            timestamp = int(time.time())
            metadata_file = self.history_file.with_suffix('.meta')

            with open(metadata_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp}|{result_type}|{command}\n")

        except Exception:
            pass

    def get_history_with_metadata(self, limit: int = 50):
        """Get history with metadata if available."""
        try:
            metadata_file = self.history_file.with_suffix('.meta')
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                history_items = []
                for line in lines[-limit:]:
                    parts = line.strip().split('|', 2)
                    if len(parts) == 3:
                        timestamp, result_type, command = parts
                        try:
                            import datetime
                            dt = datetime.datetime.fromtimestamp(
                                int(timestamp))
                            history_items.append({
                                'command': command,
                                'type': result_type,
                                'time': dt.strftime('%H:%M:%S'),
                                'date': dt.strftime('%Y-%m-%d')
                            })
                        except:
                            history_items.append({
                                'command': command,
                                'type': result_type,
                                'time': 'unknown',
                                'date': 'unknown'
                            })

                return history_items
        except Exception:
            pass

        # Fallback to regular history
        regular_history = self.get_history(limit)
        return [{'command': cmd, 'type': 'unknown', 'time': 'unknown', 'date': 'unknown'}
                for cmd in regular_history]
