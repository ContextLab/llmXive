"""
Environment configuration management for the ball milling prediction project.

This module handles loading, validation, and access to configuration settings
defined in config.yaml. It provides a singleton pattern for settings access
and convenience functions for retrieving specific configuration values.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.utils.logger import get_module_logger

# Custom exception for configuration errors
class ConfigError(Exception):
    """Raised when there is an error with configuration loading or validation."""
    pass

class Settings:
    """
    Singleton class to manage application settings.
    
    Loads configuration from config.yaml and provides methods to access
    various configuration sections.
    """
    
    _instance: Optional['Settings'] = None
    _config: Dict[str, Any] = {}
    _config_path: Optional[Path] = None
    
    def __new__(cls) -> 'Settings':
        """Ensure only one instance of Settings exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize settings if not already initialized."""
        if not self._config:
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from config.yaml file."""
        logger = get_module_logger(__name__)
        
        # Determine config file path
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        config_path = project_root / 'config.yaml'
        
        if not config_path.exists():
            # Try to create default config if it doesn't exist
            logger.warning(f"Config file not found at {config_path}. Creating default config.")
            self._create_default_config(config_path)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            self._config_path = config_path
            logger.info(f"Configuration loaded from {config_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config.yaml: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config file: {e}")
    
    def _create_default_config(self, config_path: Path) -> None:
        """Create a default config.yaml file with template values."""
        logger = get_module_logger(__name__)
        
        default_config = {
            'api_endpoints': {
                'materials_project': 'https://next-gen.materialsproject.org/api/v2',
                'nist_search': 'https://www.nist.gov/pml/automated-spectroscopy-database-search-api',
                'arxiv': 'http://export.arxiv.org/api/query'
            },
            'resource_limits': {
                'gpr_max_runtime': 1800,  # 30 minutes in seconds
                'gpr_max_memory': 5.0      # 5 GB
            },
            'ocr_settings': {
                'ocr_enabled': True,
                'ocr_language': 'eng',
                'ocr_confidence_threshold': 0.7
            },
            'data_paths': {
                'raw': 'data/raw',
                'processed': 'data/processed',
                'splits': 'data/splits'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Default config created at {config_path}")
        except Exception as e:
            raise ConfigError(f"Failed to create default config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Dot-separated key path (e.g., 'resource_limits.gpr_max_runtime')
            default: Default value if key doesn't exist
        
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
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get all API endpoint configurations."""
        return self._config.get('api_endpoints', {})
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limit configurations."""
        return self._config.get('resource_limits', {})
    
    def get_ocr_settings(self) -> Dict[str, Any]:
        """Get OCR configuration settings."""
        return self._config.get('ocr_settings', {})
    
    def get_data_paths(self) -> Dict[str, str]:
        """Get data path configurations."""
        return self._config.get('data_paths', {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = {}
        self._load_config()

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    if _settings is not None:
        _settings._config = {}
        _settings = None

# Convenience functions
def get_config_value(key: str, default: Any = None) -> Any:
    """
    Convenience function to get a configuration value.
    
    Args:
        key: Dot-separated key path
        default: Default value if key doesn't exist
    
    Returns:
        The configuration value or default
    """
    return get_settings().get(key, default)

def get_resource_limits() -> Dict[str, Any]:
    """Convenience function to get resource limits."""
    return get_settings().get_resource_limits()

def get_api_endpoints() -> Dict[str, str]:
    """Convenience function to get API endpoints."""
    return get_settings().get_api_endpoints()

def get_ocr_settings() -> Dict[str, Any]:
    """Convenience function to get OCR settings."""
    return get_settings().get_ocr_settings()

def get_data_paths() -> Dict[str, str]:
    """Convenience function to get data paths."""
    return get_settings().get_data_paths()

def create_default_config(output_path: Optional[Path] = None) -> Path:
    """
    Create a default configuration file.
    
    Args:
        output_path: Optional path to create the config file
    
    Returns:
        Path to the created config file
    """
    if output_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        output_path = project_root / 'config.yaml'
    
    settings = get_settings()
    settings._create_default_config(output_path)
    return output_path
