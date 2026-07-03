"""
Configuration management for the molecular reactivity prediction pipeline.

Loads and validates settings from src/modeling/config.yaml.
Provides a singleton Config instance for the rest of the application.
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path

# Ensure we can import from src
import sys
from pathlib import Path as Pathlib

# Add the project root to sys.path if running directly
project_root = Pathlib(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

logger = get_logger(__name__)

class Config:
    """
    Singleton configuration class that loads settings from config.yaml.
    """
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from the YAML file."""
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded successfully from {config_path}")
            self._validate_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            raise

    def _validate_config(self) -> None:
        """Validate that required sections exist in the configuration."""
        required_sections = ['project', 'paths', 'data_sources', 'modeling', 'evaluation', 'logging']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate specific critical keys
        if 'uspto_url' not in self._config.get('data_sources', {}):
            raise ValueError("Missing required key: data_sources.uspto_url")
        
        if 'min_class_samples' not in self._config.get('modeling', {}):
            raise ValueError("Missing required key: modeling.min_class_samples")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Dot-separated key path (e.g., 'modeling.n_estimators')
            default: Default value if key not found
        
        Returns:
            The configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def get_project_name(self) -> str:
        """Get the project name."""
        return self._config['project']['name']

    def get_data_path(self, dataset_type: str) -> Path:
        """
        Get the full path for a specific data directory.
        
        Args:
            dataset_type: One of 'raw', 'processed', 'models', 'figures', 'logs'
        
        Returns:
            Path object for the requested directory
        """
        base_key = f'paths.data_{dataset_type}'
        relative_path = self.get(base_key)
        
        if not relative_path:
            raise ValueError(f"Unknown data type: {dataset_type}")
        
        return project_root / relative_path

    def get_reaction_templates(self) -> Dict[str, str]:
        """Get the SMARTS patterns for reaction classification."""
        return self._config['reaction_templates']

    def get_model_params(self) -> Dict[str, Any]:
        """Get modeling parameters for the ML model."""
        return self._config['modeling']

    def get_evaluation_params(self) -> Dict[str, Any]:
        """Get evaluation parameters."""
        return self._config['evaluation']

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config['logging']

# Global config instance
config = Config()

# Convenience functions for direct access
def get_config_value(key: str, default: Any = None) -> Any:
    """Convenience function to get a config value."""
    return config.get(key, default)

def get_uspto_url() -> str:
    """Get the USPTO dataset URL."""
    return config.get('data_sources.uspto_url')

def get_min_class_samples() -> int:
    """Get the minimum required samples per class."""
    return config.get('modeling.min_class_samples', 1000)

def get_runtime_limit_minutes() -> int:
    """Get the maximum allowed runtime in minutes."""
    return config.get('modeling.runtime_limit_minutes', 30)
