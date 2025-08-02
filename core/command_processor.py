"""
Command Processor - Core logic for AI command assistance
"""

import os
import platform
import subprocess
from typing import Dict, Optional, List
from core.ai_client import AIClient
from utils.command_parser import CommandParser
from utils.system_info import SystemInfo


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

        # Extract command from error if possible
        failed_command = self.command_parser.extract_command_from_error(
            error_message)

        # Get system context
        context = self._build_system_context()

        # Build prompt for error fixing
        prompt = self._build_fix_prompt(error_message, failed_command, context)

        try:
            response = self.ai_client.get_completion(prompt)
            return self._parse_ai_response(response, 'fix')
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None

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

    def _build_fix_prompt(self, error_message: str, failed_command: str, context: Dict) -> str:
        """Build prompt for fixing command errors."""
        return f"""You are an expert command-line assistant. Help fix command errors and provide working solutions.

SYSTEM CONTEXT:
- OS: {context['os']}
- Shell: {context['shell']}
- Current Directory: {context['cwd']}
- User: {context['user']}
- Available Tools: {', '.join(context['available_tools'])}

ERROR TO FIX:
{error_message}

{f"FAILED COMMAND: {failed_command}" if failed_command else ""}

REQUIREMENTS:
1. Provide a clear explanation of what went wrong
2. Give a corrected command that should work
3. Explain why the fix works
4. Make sure the command is safe to execute
5. Consider the user's current system and environment

RESPONSE FORMAT:
Provide your response in this exact format:

EXPLANATION:
[Clear explanation of the error and solution]

COMMAND:
[The corrected command to run]

SAFETY:
[Any safety considerations or warnings]

Focus on practical, executable solutions. Be concise but thorough."""

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
