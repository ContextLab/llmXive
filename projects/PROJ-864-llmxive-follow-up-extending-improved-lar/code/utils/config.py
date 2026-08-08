import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from models.config import (
    get_model_config,
    EMBED_DIM,
    NUM_HEADS,
    PARAMS,
)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Singleton configuration manager."""
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def load(self, config_path: Optional[Path] = None) -> None:
        """Load configuration from a YAML file."""
        if config_path is None:
            # Default to project root config
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            config_path = project_root / "config.yaml"

        if not config_path.exists():
            # Fallback to defaults if no config file
            self._config = self._get_defaults()
            return

        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config file: {e}")

    def _get_defaults(self) -> Dict[str, Any]:
        """Return default configuration values."""
        return {
            "token_limit": 10_000_000,
            "max_ram_gb": 7.0,
            "learning_rate": 1e-4,
            "batch_size": 32,
            "num_epochs": 100,
            "max_seq_length": 512,
            "vocab_size": 50257,
            "embed_dim": EMBED_DIM,
            "num_heads": NUM_HEADS,
            "device": "cpu",
            "data_dir": "data",
            "processed_dir": "data/processed",
            "artifacts_dir": "data/artifacts",
            "project_root": "projects/PROJ-864-llmxive-follow-up-extending-improved-lar",
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        return key in self._config

_config_instance = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return _config_instance

def reset_config() -> None:
    """Reset the global configuration to defaults."""
    _config_instance._config = _config_instance._get_defaults()

# Helper functions for specific config values

def get_token_limit() -> int:
    """Get the token limit for the corpus."""
    return _config_instance.get("token_limit", 10_000_000)

def get_max_ram_gb() -> float:
    """Get the maximum RAM threshold in GB."""
    return _config_instance.get("max_ram_gb", 7.0)

def get_learning_rate() -> float:
    """Get the learning rate."""
    return _config_instance.get("learning_rate", 1e-4)

def get_batch_size() -> int:
    """Get the batch size."""
    return _config_instance.get("batch_size", 32)

def get_num_epochs() -> int:
    """Get the number of epochs."""
    return _config_instance.get("num_epochs", 100)

def get_max_seq_length() -> int:
    """Get the maximum sequence length."""
    return _config_instance.get("max_seq_length", 512)

def get_vocab_size() -> int:
    """Get the vocabulary size."""
    return _config_instance.get("vocab_size", 50257)

def get_embed_dim() -> int:
    """Get the embedding dimension."""
    return _config_instance.get("embed_dim", EMBED_DIM)

def get_num_heads() -> int:
    """Get the number of attention heads."""
    return _config_instance.get("num_heads", NUM_HEADS)

def get_device() -> str:
    """Get the device to use (cpu, cuda, etc.)."""
    return _config_instance.get("device", "cpu")

def get_project_root() -> Path:
    """Get the project root directory."""
    root = _config_instance.get("project_root", "projects/PROJ-864-llmxive-follow-up-extending-improved-lar")
    return Path(root)

def get_data_dir() -> Path:
    """Get the data directory."""
    data_dir = _config_instance.get("data_dir", "data")
    return get_project_root() / data_dir

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    processed_dir = _config_instance.get("processed_dir", "data/processed")
    return get_data_dir() / processed_dir

def get_artifacts_dir() -> Path:
    """Get the artifacts directory."""
    artifacts_dir = _config_instance.get("artifacts_dir", "data/artifacts")
    return get_data_dir() / artifacts_dir