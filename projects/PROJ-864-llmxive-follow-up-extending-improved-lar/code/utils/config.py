"""
Configuration management for the llmXive project.

This module handles loading configuration from a YAML file and provides
global access to configuration values.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

class Config:
    """Singleton configuration class."""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def load(self, config_path: Optional[Path] = None):
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
        """
        if config_path is None:
            # Default location: project root / config / config.yaml
            project_root = Path(__file__).resolve().parent.parent.parent
            config_path = project_root / "config" / "config.yaml"
        
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated key path (e.g., 'data.token_limit').
            default: Default value if key not found.
        
        Returns:
            The configuration value or default.
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated key path.
            value: Value to set.
        """
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

# Global config instance
_config_instance = Config()

def get_config() -> Config:
    """Get the global config instance."""
    return _config_instance

def reset_config():
    """Reset the global config instance."""
    global _config_instance
    _config_instance = Config()

def load_config(config_path: Optional[Path] = None):
    """Load configuration into the global instance."""
    _config_instance.load(config_path)

# Convenience functions for common config values
def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume project root is 3 levels up from this file
    return Path(__file__).resolve().parent.parent.parent

def get_data_dir() -> Path:
    """Get the data directory."""
    return get_project_root() / "data"

def get_raw_dir() -> Path:
    """Get the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    return get_data_dir() / "processed"

def get_artifacts_dir() -> Path:
    """Get the artifacts directory."""
    return get_data_dir() / "artifacts"

def get_token_limit() -> int:
    """Get the token limit for the corpus."""
    return _config_instance.get('data.token_limit', 1_000_000)

def get_max_ram_gb() -> float:
    """Get the maximum RAM limit in GB."""
    return _config_instance.get('resources.max_ram_gb', 7.0)

def get_train_split_ratio() -> float:
    """Get the training set split ratio."""
    return _config_instance.get('data.train_split_ratio', 0.8)

def get_learning_rate() -> float:
    """Get the learning rate."""
    return _config_instance.get('training.learning_rate', 1e-4)

def get_batch_size() -> int:
    """Get the batch size."""
    return _config_instance.get('training.batch_size', 32)

def get_num_epochs() -> int:
    """Get the number of training epochs."""
    return _config_instance.get('training.num_epochs', 100)

def get_max_seq_length() -> int:
    """Get the maximum sequence length."""
    return _config_instance.get('model.max_seq_length', 512)

def get_vocab_size() -> int:
    """Get the vocabulary size."""
    return _config_instance.get('model.vocab_size', 50257) # GPT-2 vocab size

def get_embed_dim() -> int:
    """Get the embedding dimension."""
    return _config_instance.get('model.embed_dim', 512)

def get_num_heads() -> int:
    """Get the number of attention heads."""
    return _config_instance.get('model.num_heads', 8)

def get_device() -> str:
    """Get the device to use for training."""
    return _config_instance.get('training.device', 'cpu')

def set_config(key: str, value: Any):
    """Set a configuration value."""
    _config_instance.set(key, value)