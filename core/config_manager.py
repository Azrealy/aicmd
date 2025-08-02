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

    def save_config(self):
        """Save current configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            raise Exception(f"Could not save config file: {e}")

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

    def update_config(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        self.config.update(updates)

    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()

    def validate_config(self) -> tuple[bool, list]:
        """Validate current configuration."""
        errors = []

        # Check if at least one API key is available
        if not self.get_api_key():
            errors.append(
                "No API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")

        # Validate numeric values
        numeric_fields = ['max_tokens', 'temperature', 'cache_duration']
        for field in numeric_fields:
            value = self.get(field)
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"'{field}' must be a number")

        # Validate temperature range
        temp = self.get('temperature')
        if temp is not None and (temp < 0 or temp > 2):
            errors.append("'temperature' must be between 0 and 2")

        # Validate max_tokens
        max_tokens = self.get('max_tokens')
        if max_tokens is not None and (max_tokens < 1 or max_tokens > 8000):
            errors.append("'max_tokens' must be between 1 and 8000")

        return len(errors) == 0, errors

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)."""
        summary = self.config.copy()

        # Remove sensitive information
        sensitive_keys = ['openai_api_key', 'anthropic_api_key']
        for key in sensitive_keys:
            if key in summary:
                summary[key] = '***' if summary[key] else None

        # Add derived information
        summary['has_openai_key'] = bool(self.get_openai_key())
        summary['has_anthropic_key'] = bool(self.get_anthropic_key())
        summary['config_file'] = str(self.config_path)

        return summary
