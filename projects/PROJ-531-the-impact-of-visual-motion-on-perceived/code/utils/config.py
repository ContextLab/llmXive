"""
Environment variable management for API keys and data paths.

This module provides a centralized configuration manager that loads
environment variables with sensible defaults for the llmXive pipeline.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


class ConfigManager:
    """Manages environment variables for API keys and data paths."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            env_file: Optional path to a .env file to load.
        """
        self.env_file = env_file
        self._load_env_file()
        self._config = self._build_config()

    def _load_env_file(self) -> None:
        """Load environment variables from a .env file if it exists."""
        if self.env_file and os.path.exists(self.env_file):
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            except Exception:
                pass  # Silently ignore if .env loading fails

    def _build_config(self) -> Dict[str, Any]:
        """Build configuration dictionary from environment variables."""
        return {
            # API Keys (optional, with defaults)
            'OPENML_API_KEY': os.getenv('OPENML_API_KEY', ''),
            'HF_TOKEN': os.getenv('HF_TOKEN', ''),
            
            # Data Paths
            'RAW_DATA_DIR': os.getenv('RAW_DATA_DIR', 'data/raw'),
            'PROCESSED_DATA_DIR': os.getenv('PROCESSED_DATA_DIR', 'data/processed'),
            'RESULTS_DIR': os.getenv('RESULTS_DIR', 'data/results'),
            'FIGURES_DIR': os.getenv('FIGURES_DIR', 'data/results/plots'),
            
            # Feature Flags
            'ENABLE_REAL_DATA': os.getenv('ENABLE_REAL_DATA', 'false').lower() == 'true',
            'USE_SYNTHETIC_FALLBACK': os.getenv('USE_SYNTHETIC_FALLBACK', 'true').lower() == 'true',
            
            # Logging
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'LOG_FILE': os.getenv('LOG_FILE', 'logs/pipeline.log'),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key.
            default: Default value if key not found.
            
        Returns:
            The configuration value or default.
        """
        return self._config.get(key, default)

    def get_path(self, key: str) -> Path:
        """
        Get a configuration value as a Path object.
        
        Args:
            key: The configuration key for a path.
            
        Returns:
            A Path object for the configuration value.
        """
        value = self._config.get(key, '')
        return Path(value)

    def ensure_dirs(self) -> None:
        """Ensure all configured directories exist."""
        for key in ['RAW_DATA_DIR', 'PROCESSED_DATA_DIR', 'RESULTS_DIR', 'FIGURES_DIR']:
            path = self.get_path(key)
            path.mkdir(parents=True, exist_ok=True)

    def is_real_data_available(self) -> bool:
        """
        Check if real data sources are configured and available.
        
        Returns:
            True if real data is enabled and API keys are present.
        """
        if not self.get('ENABLE_REAL_DATA'):
            return False
        
        # Check if at least one API key is configured
        has_openml = bool(self.get('OPENML_API_KEY'))
        has_hf = bool(self.get('HF_TOKEN'))
        return has_openml or has_hf

    def to_json(self, indent: int = 2) -> str:
        """
        Export configuration to JSON string.
        
        Args:
            indent: JSON indentation level.
            
        Returns:
            JSON string representation of the configuration.
        """
        return json.dumps(self._config, indent=indent, sort_keys=True)


# Singleton instance for easy import
config = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return config
