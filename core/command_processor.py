import os
from utils.system_info import SystemInfo
from utils.command_parser import CommandParser
from .ai_client import AIClient
from typing import Dict, Optional


class CommandProcessor:
    """Main processor for handling command-related AI requests."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.ai_client = AIClient(config, logger)
        self.command_parser = CommandParser()
        self.system_info = SystemInfo()

    def fix_error(self, error_message: str) -> Optional[Dict]:
        """Fix a command error using AI assistance."""
        self.logger.debug(f"Processing error: {error_message}")

        # Parse the error message format from our fish integration
        lines = error_message.strip().split('\n')
        command = None
        error_text = None
        exit_code = None
        status = None

        for line in lines:
            if line.startswith('Command: '):
                command = line.replace('Command: ', '').strip()
            elif line.startswith('Error: '):
                error_text = line.replace('Error: ', '').strip()
            elif line.startswith('Exit Code: '):
                exit_code = line.replace('Exit Code: ', '').strip()
            elif line.startswith('Status: '):
                status = line.replace('Status: ', '').strip()

        # If we couldn't parse the structured format, treat whole message as error
        if not command and not error_text:
            error_text = error_message
            command = self.command_parser.extract_command_from_error(
                error_message)

        # Get system context
        context = self._build_system_context()

        # Build prompt for error fixing
        prompt = self._build_simple_fix_prompt(
            command, error_text, exit_code, status, context)

        try:
            response = self.ai_client.get_completion(prompt)
            return self._parse_ai_response(response, 'fix')
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None

    def _build_simple_fix_prompt(self, command: str, error_text: str, exit_code: str, status: str, context: Dict) -> str:
        """Build a simple, focused prompt for fixing command errors."""
        # Get available commands for AI reference
        available_commands = self.command_parser.get_available_commands_context()
        common_commands_str = ", ".join(
            available_commands[:20])  # Limit to first 20

        # Determine error type
        error_type = "UNKNOWN"
        if status == "COMMAND_NOT_FOUND" or exit_code == "127":
            error_type = "COMMAND_NOT_FOUND"
        elif exit_code and exit_code != "0":
            error_type = "COMMAND_FAILED"

        return f"""You are an expert command-line assistant. Fix this command error and provide a working solution.

SYSTEM INFO:
- OS: {context['os']}
- Shell: {context['shell']}
- Directory: {context['cwd']}

ERROR TO FIX:
- Command: {command or 'Unknown'}
- Error: {error_text or 'No error message'}
- Exit Code: {exit_code or 'Unknown'}
- Type: {error_type}

COMMON COMMANDS: {common_commands_str}

INSTRUCTIONS:
1. **TYPO DETECTION**: If this is a "command not found" error, check if it's a typo:
   - Examples: 'lls' → 'ls', 'dockeraa' → 'docker', 'gti' → 'git'
   
2. **KEEP ARGUMENTS**: Preserve any arguments from the original command

3. **BE SPECIFIC**: Give one clear, executable command as the solution

4. **EXPLAIN BRIEFLY**: Why this error occurred and why your fix works

RESPONSE FORMAT:
EXPLANATION:
[Brief explanation of the error and why your solution works]

COMMAND:
[The exact command to run - just the command, no extra formatting]

SAFETY:
[Any warnings or notes about the command]

Focus on practical solutions. Be confident in typo corrections when the intent is clear."""

    def suggest_command(self, description: str) -> Optional[Dict]:
        """Suggest a command based on natural language description."""
        self.logger.debug(f"Generating command suggestion for: {description}")

        context = self._build_system_context()
        prompt = self._build_suggest_prompt(description, context)

        try:
            response = self.ai_client.get_completion(prompt)
            return self._parse_ai_response(response, 'suggest')
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None

    def ask_question(self, question: str, conversation_context: dict = None) -> Optional[Dict]:
        """Ask a general question about computers, coding, or technology with context."""
        self.logger.debug(f"Processing question with context: {question}")

        # Get system context for better answers
        context = self._build_system_context()

        # Build prompt for general questions with conversation context
        prompt = self._build_chat_prompt_with_context(
            question, context, conversation_context)

        try:
            response = self.ai_client.get_completion(prompt)
            return response
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None

    def _build_chat_prompt_with_context(self, question: str, context: Dict, conversation_context: dict = None) -> str:
        """Build simplified prompt for coding/computer questions with conversation context."""

        # Build context section if available
        context_section = ""
        if conversation_context:
            context_parts = []

            if conversation_context.get('current_topic'):
                context_parts.append(
                    f"Current topic: {conversation_context['current_topic']}")

            if conversation_context.get('previous_questions'):
                recent_q = conversation_context['previous_questions'][-3:]
                if recent_q:
                    context_parts.append(
                        f"Recent questions: {'; '.join(recent_q)}")

            if conversation_context.get('related_qa'):
                context_parts.append("Related previous answers available")

            if context_parts:
                context_section = f"Context: {'. '.join(context_parts)}. "

        return f"""You are a computer scientist and expert programming engineer. Answer technical questions clearly and practically.

{context_section}Question: {question}

Instructions:
- Give direct, expert-level answers
- Use # for titles and headings
- Highlight code with ```language blocks
- Be concise but complete
- Include practical examples when helpful
- Reference previous context if relevant

Format your response with proper markdown formatting."""

    def _parse_chat_response(self, response: str) -> Dict:
        """Parse chat response into structured format."""
        result = {
            'action': 'chat',
            'raw_response': response
        }

        # Try to extract code sections
        lines = response.split('\n')
        answer_lines = []
        code_lines = []
        language = ""

        current_section = "answer"

        for line in lines:
            line_upper = line.strip().upper()

            if line_upper.startswith('CODE:'):
                current_section = "code"
                continue
            elif line_upper.startswith('LANGUAGE:'):
                language = line.replace('LANGUAGE:', '').replace(
                    'Language:', '').strip()
                continue
            elif line_upper.startswith('ANSWER:'):
                current_section = "answer"
                continue

            if current_section == "answer":
                answer_lines.append(line)
            elif current_section == "code":
                code_lines.append(line)

        # Clean up the answer
        answer = '\n'.join(answer_lines).strip()
        if answer.startswith('ANSWER:'):
            answer = answer.replace('ANSWER:', '').strip()

        result['answer'] = answer if answer else response

        # Add code if found
        if code_lines:
            code = '\n'.join(code_lines).strip()
            # Remove markdown code blocks if present
            if code.startswith('```') and code.endswith('```'):
                code_lines = code.split('\n')
                if len(code_lines) > 2:
                    # Remove first and last lines (```)
                    code = '\n'.join(code_lines[1:-1])
                    # Extract language from first line if present
                    if not language and code_lines[0].startswith('```'):
                        language = code_lines[0].replace('```', '').strip()

            result['code'] = code
            result['language'] = language.lower() if language else 'text'

    def explain_command(self, command: str) -> Optional[Dict]:
        """Explain what a command does."""
        self.logger.debug(f"Explaining command: {command}")

        context = self._build_system_context()
        prompt = self._build_explain_prompt(command, context)

        try:
            response = self.ai_client.get_completion(prompt)
            return self._parse_ai_response(response, 'explain')
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None

    def _build_system_context(self) -> Dict:
        """Build system context for AI prompts."""
        return {
            'os': self.system_info.get_os_info(),
            'shell': self.system_info.get_shell_info(),
            'cwd': os.getcwd(),
            'user': os.getenv('USER', 'unknown'),
            'available_tools': self.system_info.get_available_tools(),
            'recent_commands': self.system_info.get_recent_commands()
        }

    def _build_suggest_prompt(self, description: str, context: Dict) -> str:
        """Build prompt for command suggestions."""
        return f"""You are an expert command-line assistant. Suggest the best command(s) for the given task.

SYSTEM CONTEXT:
- OS: {context['os']}
- Shell: {context['shell']}
- Current Directory: {context['cwd']}
- User: {context['user']}
- Available Tools: {', '.join(context['available_tools'])}

TASK DESCRIPTION:
{description}

REQUIREMENTS:
1. Suggest the most appropriate command for this task
2. Explain what the command does
3. Include any necessary flags or options
4. Warn about potentially destructive operations
5. Consider the user's current system and available tools

RESPONSE FORMAT:
Provide your response in this exact format:

EXPLANATION:
[Clear explanation of what this command accomplishes]

COMMAND:
[The suggested command to run]

ALTERNATIVES:
[Other ways to accomplish the same task, if applicable]

SAFETY:
[Any safety considerations or warnings]

Prioritize commands that are commonly available and cross-platform when possible."""

    def _build_explain_prompt(self, command: str, context: Dict) -> str:
        """Build prompt for command explanations."""
        return f"""You are an expert command-line assistant. Explain the given command in detail.

SYSTEM CONTEXT:
- OS: {context['os']}
- Shell: {context['shell']}

COMMAND TO EXPLAIN:
{command}

REQUIREMENTS:
1. Break down each part of the command
2. Explain what each flag/option does
3. Describe the expected output or behavior
4. Mention any potential risks or side effects
5. Suggest variations or related commands

RESPONSE FORMAT:
Provide your response in this exact format:

EXPLANATION:
[Detailed breakdown of the command and its components]

BREAKDOWN:
[Part-by-part analysis of the command syntax]

BEHAVIOR:
[What the command does and expected results]

SAFETY:
[Any risks, side effects, or precautions]

Be educational and thorough in your explanation."""

    def _parse_ai_response(self, response: str, action_type: str) -> Dict:
        """Parse AI response into structured format."""
        result = {
            'action': action_type,
            'raw_response': response
        }

        # Extract sections using simple parsing
        sections = ['EXPLANATION:', 'COMMAND:', 'ALTERNATIVES:',
                    'SAFETY:', 'BREAKDOWN:', 'BEHAVIOR:']

        current_section = None
        current_content = []

        for line in response.split('\n'):
            line = line.strip()

            # Check if this line starts a new section
            section_found = False
            for section in sections:
                if line.startswith(section):
                    # Save previous section
                    if current_section:
                        section_name = current_section.replace(':', '').lower()
                        result[section_name] = '\n'.join(
                            current_content).strip()

                    # Start new section
                    current_section = section
                    current_content = [line[len(section):].strip()]
                    section_found = True
                    break

            if not section_found and current_section:
                current_content.append(line)

        # Save the last section
        if current_section:
            section_name = current_section.replace(':', '').lower()
            result[section_name] = '\n'.join(current_content).strip()

        # Clean up command extraction
        if 'command' in result:
            # Remove any markdown formatting
            command = result['command'].strip()
            if command.startswith('```') and command.endswith('```'):
                lines = command.split('\n')
                if len(lines) > 2:
                    command = '\n'.join(lines[1:-1])
                else:
                    command = command.replace('```', '')
            result['command'] = command.strip()

        return result

    def validate_command_safety(self, command: str) -> tuple[bool, str]:
        """Validate if a command is safe to execute."""
        dangerous_patterns = [
            'rm -rf /',
            'rm -rf *',
            'dd if=',
            'mkfs.',
            'fdisk',
            'format',
            'shutdown',
            'reboot',
            'halt',
            'init 0',
            'init 6',
            ':(){ :|:& };:',  # Fork bomb
            'chmod -R 777 /',
            'chown -R',
            'sudo su',
            'curl | sh',
            'wget | sh'
        ]

        command_lower = command.lower()

        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False, f"Potentially dangerous command detected: contains '{pattern}'"

        # Check for suspicious redirections
        if ' > /dev/' in command_lower or ' >> /dev/' in command_lower:
            return False, "Command attempts to write to device files"

        # Check for network downloads with execution
        if ('curl' in command_lower or 'wget' in command_lower) and ('|' in command or ';' in command):
            return False, "Command downloads and executes content from the internet"

        return True, "Command appears safe"
