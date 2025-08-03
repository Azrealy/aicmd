"""
History Manager - Handles command history with arrow key navigation
"""

import os
import readline
import time
from pathlib import Path
from typing import List, Optional


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


class ConversationContext:
    """Manages conversation context for AI chat mode."""

    def __init__(self, history_manager):
        self.history_manager = history_manager
        self.conversation_memory = []
        self.max_context_messages = 10  # Keep last 10 Q&A pairs
        self.current_topic = None
        self.related_commands = []

    def add_qa_pair(self, question: str, answer: str, has_code: bool = False):
        """Add a question-answer pair to conversation memory."""
        qa_pair = {
            'question': question,
            'answer': answer,
            'has_code': has_code,
            'timestamp': time.time()
        }

        self.conversation_memory.append(qa_pair)

        # Keep only recent messages to avoid token limits
        if len(self.conversation_memory) > self.max_context_messages:
            self.conversation_memory = self.conversation_memory[-self.max_context_messages:]

        # Update current topic based on recent questions
        self._update_current_topic()

    def get_context_for_question(self, current_question: str) -> dict:
        """Get relevant context for the current question."""
        context = {
            'previous_questions': [],
            'recent_topics': [],
            'related_qa': [],
            'current_topic': self.current_topic
        }

        # Get recent questions for context
        recent_history = self.history_manager.get_history(5)
        context['previous_questions'] = recent_history

        # Find related Q&A pairs from conversation memory
        context['related_qa'] = self._find_related_qa(current_question)

        # Extract topics from recent conversation
        context['recent_topics'] = self._extract_recent_topics()

        return context

    def _update_current_topic(self):
        """Update current topic based on recent questions."""
        if not self.conversation_memory:
            return

        recent_questions = [qa['question']
                            for qa in self.conversation_memory[-3:]]

        # Simple topic detection based on keywords
        topics = {
            'git': ['git', 'repository', 'commit', 'branch', 'merge', 'push', 'pull'],
            'python': ['python', 'django', 'flask', 'pandas', 'numpy', 'pip'],
            'javascript': ['javascript', 'node', 'npm', 'react', 'vue', 'angular'],
            'docker': ['docker', 'container', 'image', 'dockerfile', 'compose'],
            'linux': ['linux', 'ubuntu', 'bash', 'shell', 'terminal', 'command'],
            'database': ['sql', 'database', 'mysql', 'postgresql', 'mongodb', 'query'],
            'web': ['http', 'api', 'rest', 'web', 'server', 'client', 'html', 'css']
        }

        topic_scores = {}
        for topic, keywords in topics.items():
            score = 0
            for question in recent_questions:
                question_lower = question.lower()
                for keyword in keywords:
                    if keyword in question_lower:
                        score += 1
            topic_scores[topic] = score

        # Set current topic to the highest scoring one
        if topic_scores and max(topic_scores.values()) > 0:
            self.current_topic = max(topic_scores, key=topic_scores.get)

    def _find_related_qa(self, current_question: str) -> list:
        """Find related Q&A pairs from conversation memory."""
        if not self.conversation_memory:
            return []

        current_words = set(current_question.lower().split())
        related_qa = []

        for qa in self.conversation_memory[-5:]:  # Check last 5 Q&A pairs
            question_words = set(qa['question'].lower().split())

            # Calculate similarity based on common words
            common_words = current_words.intersection(question_words)
            if len(common_words) >= 2:  # At least 2 common words
                related_qa.append({
                    'question': qa['question'],
                    'answer': qa['answer'][:200] + '...' if len(qa['answer']) > 200 else qa['answer'],
                    'similarity': len(common_words)
                })

        # Sort by similarity and return top 3
        related_qa.sort(key=lambda x: x['similarity'], reverse=True)
        return related_qa[:3]

    def _extract_recent_topics(self) -> list:
        """Extract topics from recent conversation."""
        if not self.conversation_memory:
            return []

        topics = set()
        for qa in self.conversation_memory[-3:]:
            question = qa['question'].lower()

            # Extract programming languages
            languages = ['python', 'javascript', 'java',
                         'c++', 'go', 'rust', 'php', 'ruby']
            for lang in languages:
                if lang in question:
                    topics.add(lang)

            # Extract technologies
            technologies = ['git', 'docker', 'kubernetes',
                            'react', 'vue', 'angular', 'django', 'flask']
            for tech in technologies:
                if tech in question:
                    topics.add(tech)

        return list(topics)

    def clear_context(self):
        """Clear conversation context."""
        self.conversation_memory = []
        self.current_topic = None
        self.related_commands = []


class AdvancedHistoryManager(HistoryManager):
    """Enhanced history manager with more features."""

    def __init__(self, history_type: str = "general"):
        super().__init__(history_type)
        self.conversation_context = ConversationContext(self)
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

    def add_qa_to_context(self, question: str, answer: str, has_code: bool = False):
        """Add question-answer pair to conversation context."""
        self.conversation_context.add_qa_pair(question, answer, has_code)

    def get_conversation_context(self, current_question: str) -> dict:
        """Get conversation context for current question."""
        return self.conversation_context.get_context_for_question(current_question)

    def clear_conversation_context(self):
        """Clear conversation context."""
        self.conversation_context.clear_context()

    def get_current_topic(self) -> str:
        """Get current conversation topic."""
        return self.conversation_context.current_topic

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
