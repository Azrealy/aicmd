"""
Configuration Manager - Handles all configuration and settings
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration for the AI command tool."""

    DEFAULT_CONFIG = {
        "openai_model": "gpt-3.5-turbo",
        "anthropic_model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "temperature": 0.1,
        "auto_execute": False,
        "verbose": False,
        "safety_checks": True,
        "cache_responses": True,
        "cache_duration": 3600,
        "terminal_integration": True,
        "shell_hooks": True
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = self._get_config_path(config_path)
        self.config = self._load_config()

    def _get_config_path(self, custom_path: Optional[str]) -> Path:
        """Get the configuration file path."""
        if custom_path:
            return Path(custom_path)

        # Default locations
        config_dir = Path.home() / '.aicmd'
        config_dir.mkdir(exist_ok=True)

        return config_dir / 'config.json'

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config = self.DEFAULT_CONFIG.copy()

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                config.update(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")

        return config

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value

    def get_api_key(self) -> Optional[str]:
        """Get the appropriate API key based on priority."""
        # Check environment variables first
        openai_key = self.get_openai_key()
        if openai_key:
            return openai_key

        anthropic_key = self.get_anthropic_key()
        if anthropic_key:
            return anthropic_key

        return None

    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        # Environment variable takes precedence
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key:
            return env_key

        # Check config file
        return self.config.get('openai_api_key')

    def get_anthropic_key(self) -> Optional[str]:
        """Get Anthropic API key."""
        # Environment variable takes precedence
        env_key = os.getenv('ANTHROPIC_API_KEY')
        if env_key:
            return env_key

        # Check config file
        return self.config.get('anthropic_api_key')

    def get_custom_endpoint(self) -> Optional[str]:
        """Get custom endpoint URL."""
        return self.config.get('custom_endpoint')
