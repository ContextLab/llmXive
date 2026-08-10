"""
Configuration Management Module for llmXive Follow-up Project.

This module provides a centralized configuration system using YAML files.
It supports loading project-specific settings, data paths, and hyperparameters.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Singleton-like configuration holder."""
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def load(self, config_path: Optional[Path] = None):
        """Load configuration from a YAML file."""
        if config_path is None:
            # Default path relative to project root
            project_root = Path(__file__).resolve().parent.parent.parent
            config_path = project_root / "projects" / "PROJ-864-llmxive-follow-up-extending-improved-lar" / "config.yaml"
        
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # Set defaults if missing
        self._set_defaults()

    def _set_defaults(self):
        """Set default values for missing configuration keys."""
        defaults = {
            "project_root": "projects/PROJ-864-llmxive-follow-up-extending-improved-lar",
            "data_dir": "data",
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "artifacts_dir": "data/artifacts",
            "token_limit": 1000000,  # 1M tokens (Staged Simplification)
            "max_ram_gb": 6.0,
            "learning_rate": 1e-4,
            "batch_size": 32,
            "num_epochs": 100,
            "max_seq_length": 1024,
            "vocab_size": 50257,  # GPT-2 vocab size
            "embed_dim": 768,
            "num_heads": 12,
            "device": "cpu",
            "train_split_ratio": 0.9
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

# Global config instance
_config_instance = Config()

def get_config() -> Dict[str, Any]:
    """Get the full configuration dictionary."""
    return _config_instance._config

def reset_config():
    """Reset the configuration to defaults."""
    _config_instance._config = {}
    _config_instance._set_defaults()

# Helper functions for common config keys
def get_token_limit() -> int:
    """Get the target token limit for the corpus."""
    return _config_instance.get("token_limit", 1_000_000)

def get_max_ram_gb() -> float:
    """Get the maximum RAM usage in GB."""
    return _config_instance.get("max_ram_gb", 6.0)

def get_learning_rate() -> float:
    """Get the learning rate."""
    return _config_instance.get("learning_rate", 1e-4)

def get_batch_size() -> int:
    """Get the batch size."""
    return _config_instance.get("batch_size", 32)

def get_num_epochs() -> int:
    """Get the number of training epochs."""
    return _config_instance.get("num_epochs", 100)

def get_max_seq_length() -> int:
    """Get the maximum sequence length."""
    return _config_instance.get("max_seq_length", 1024)

def get_vocab_size() -> int:
    """Get the vocabulary size."""
    return _config_instance.get("vocab_size", 50257)

def get_embed_dim() -> int:
    """Get the embedding dimension."""
    return _config_instance.get("embed_dim", 768)

def get_num_heads() -> int:
    """Get the number of attention heads."""
    return _config_instance.get("num_heads", 12)

def get_device() -> str:
    """Get the device (cpu/cuda)."""
    return _config_instance.get("device", "cpu")

def get_project_root() -> Path:
    """Get the project root directory."""
    root = _config_instance.get("project_root", "projects/PROJ-864-llmxive-follow-up-extending-improved-lar")
    return Path(root)

def get_data_dir() -> Path:
    """Get the data directory."""
    data_dir = _config_instance.get("data_dir", "data")
    return get_project_root() / data_dir

def get_raw_dir() -> Path:
    """Get the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    return get_data_dir() / "processed"

def get_artifacts_dir() -> Path:
    """Get the artifacts directory."""
    return get_data_dir() / "artifacts"

def get_train_split_ratio() -> float:
    """Get the training split ratio."""
    return _config_instance.get("train_split_ratio", 0.9)

# Load config on module import
try:
    # Try to load from default location
    _config_instance.load()
except ConfigError:
    # If config file is missing, use defaults (for testing/initialization)
    pass
