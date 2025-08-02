"""
AI Client - Handles communication with AI services (OpenAI, Anthropic, etc.)
"""

import json
import requests
from typing import Dict, Any
from datetime import datetime


class AIClient:
    """Client for interacting with AI services."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self._setup_client()

    def _setup_client(self):
        """Setup the AI client based on configuration."""
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'AI-Command-Tool/1.0'
        })

        # Configure API client based on available keys
        self.provider = self._detect_provider()
        self.logger.debug(f"Using AI provider: {self.provider}")

    def _detect_provider(self) -> str:
        """Detect which AI provider to use based on available API keys."""
        if self.config.get_openai_key():
            return 'openai'
        elif self.config.get_anthropic_key():
            return 'anthropic'
        elif self.config.get_custom_endpoint():
            return 'custom'
        else:
            raise ValueError(
                "No AI provider configured. Please set up API keys.")

    def get_completion(self, prompt: str, **kwargs) -> str:
        """Get completion from the configured AI provider."""
        if self.provider == 'openai':
            return self._get_openai_completion(prompt, **kwargs)
        elif self.provider == 'anthropic':
            return self._get_anthropic_completion(prompt, **kwargs)
        elif self.provider == 'custom':
            return self._get_custom_completion(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_openai_completion(self, prompt: str, **kwargs) -> str:
        """Get completion from OpenAI API."""
        api_key = self.config.get_openai_key()
        model = kwargs.get('model', self.config.get(
            'openai_model', 'gpt-3.5-turbo'))
        max_tokens = kwargs.get(
            'max_tokens', self.config.get('max_tokens', 1000))
        temperature = kwargs.get(
            'temperature', self.config.get('temperature', 0.1))

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert command-line assistant focused on helping users with terminal commands, error fixing, and system administration.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': False
        }

        try:
            self.logger.debug(
                f"Sending request to OpenAI API (model: {model})")
            response = self.session.post(
                'https://testaifoundrykai.cognitiveservices.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-01-01-preview',
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected OpenAI API response format: {e}")

    def _get_anthropic_completion(self, prompt: str, **kwargs) -> str:
        """Get completion from Anthropic Claude API."""
        api_key = self.config.get_anthropic_key()
        model = kwargs.get('model', self.config.get(
            'anthropic_model', 'claude-3-sonnet-20240229'))
        max_tokens = kwargs.get(
            'max_tokens', self.config.get('max_tokens', 1000))
        temperature = kwargs.get(
            'temperature', self.config.get('temperature', 0.1))

        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        system_prompt = 'You are an expert command-line assistant focused on helping users with terminal commands, error fixing, and system administration.'

        data = {
            'model': model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }

        try:
            self.logger.debug(
                f"Sending request to Anthropic API (model: {model})")
            response = self.session.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result['content'][0]['text'].strip()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Anthropic API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected Anthropic API response format: {e}")

    def _get_custom_completion(self, prompt: str, **kwargs) -> str:
        """Get completion from custom endpoint (e.g., local LLM)."""
        endpoint = self.config.get_custom_endpoint()
        headers = {'Content-Type': 'application/json'}

        # Add custom headers if configured
        custom_headers = self.config.get('custom_headers', {})
        headers.update(custom_headers)

        # Build request data based on custom format
        data = {
            'prompt': prompt,
            'max_tokens': kwargs.get('max_tokens', self.config.get('max_tokens', 1000)),
            'temperature': kwargs.get('temperature', self.config.get('temperature', 0.1))
        }

        # Allow custom data format
        custom_format = self.config.get('custom_format', {})
        if custom_format:
            data.update(custom_format)

        try:
            self.logger.debug(
                f"Sending request to custom endpoint: {endpoint}")
            response = self.session.post(
                endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Try common response formats
            if 'text' in result:
                return result['text'].strip()
            elif 'response' in result:
                return result['response'].strip()
            elif 'content' in result:
                return result['content'].strip()
            elif 'output' in result:
                return result['output'].strip()
            else:
                # Fallback: return the entire response as JSON string
                return json.dumps(result, indent=2)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Custom API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected custom API response format: {e}")

    def test_connection(self) -> bool:
        """Test connection to the AI service."""
        try:
            test_prompt = "Respond with 'OK' if you can see this message."
            response = self.get_completion(test_prompt, max_tokens=10)
            return 'OK' in response.upper()
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (if supported by provider)."""
        # This would need to be implemented based on provider capabilities
        # For now, return basic info
        return {
            'provider': self.provider,
            'last_request': datetime.now().isoformat(),
            'status': 'active'
        }
