"""
Configuration management for the project.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Configuration holder."""
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

_config: Optional[Config] = None
_project_root: Optional[Path] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

def reset_config() -> None:
    """Reset the global configuration."""
    global _config, _project_root
    _config = None
    _project_root = None

def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file (optional)

    Returns:
        Config instance
    """
    global _config
    
    if config_path is None:
        # Default config path
        project_root = get_project_root()
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # Create default config
        _config = Config(_get_default_config())
        return _config

    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    _config = Config(config_dict)
    return _config

def _get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "project": {
            "name": "llmxive-follow-up-extending-improved-lar",
            "root": str(Path(__file__).parent.parent.parent)
        },
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "artifacts_dir": "data/artifacts"
        },
        "model": {
            "embed_dim": 768,
            "num_heads": 12,
            "num_layers": 6,
            "vocab_size": 50257,
            "max_seq_length": 1024,
            "learning_rate": 1e-4,
            "batch_size": 8,
            "num_epochs": 100,
            "dropout": 0.1,
            "weight_decay": 0.01,
            "warmup_steps": 100
        },
        "training": {
            "max_ram_gb": 7.0,
            "token_limit": 1000000,
            "train_split_ratio": 0.8
        },
        "device": "cpu"
    }

def get_project_root() -> Path:
    """Get the project root directory."""
    global _project_root
    if _project_root is None:
        config = get_config()
        _project_root = Path(config.get("project", {}).get("root", 
                    Path(__file__).parent.parent.parent))
    return _project_root

def get_data_dir() -> Path:
    """Get the data directory."""
    project_root = get_project_root()
    return project_root / "data"

def get_raw_dir() -> Path:
    """Get the raw data directory."""
    data_dir = get_data_dir()
    return data_dir / "raw"

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    data_dir = get_data_dir()
    return data_dir / "processed"

def get_artifacts_dir() -> Path:
    """Get the artifacts directory."""
    data_dir = get_data_dir()
    return data_dir / "artifacts"

def get_token_limit() -> int:
    """Get the token limit for the corpus."""
    config = get_config()
    return config.get("training", {}).get("token_limit", 1000000)

def get_max_ram_gb() -> float:
    """Get the maximum RAM constraint in GB."""
    config = get_config()
    return config.get("training", {}).get("max_ram_gb", 7.0)

def get_learning_rate() -> float:
    """Get the learning rate."""
    config = get_config()
    return config.get("model", {}).get("learning_rate", 1e-4)

def get_batch_size() -> int:
    """Get the batch size."""
    config = get_config()
    return config.get("model", {}).get("batch_size", 8)

def get_num_epochs() -> int:
    """Get the number of training epochs."""
    config = get_config()
    return config.get("model", {}).get("num_epochs", 100)

def get_max_seq_length() -> int:
    """Get the maximum sequence length."""
    config = get_config()
    return config.get("model", {}).get("max_seq_length", 1024)

def get_vocab_size() -> int:
    """Get the vocabulary size."""
    config = get_config()
    return config.get("model", {}).get("vocab_size", 50257)

def get_embed_dim() -> int:
    """Get the embedding dimension."""
    config = get_config()
    return config.get("model", {}).get("embed_dim", 768)

def get_num_heads() -> int:
    """Get the number of attention heads."""
    config = get_config()
    return config.get("model", {}).get("num_heads", 12)

def get_device() -> str:
    """Get the device to use for training."""
    config = get_config()
    return config.get("device", "cpu")

def get_train_split_ratio() -> float:
    """Get the training split ratio."""
    config = get_config()
    return config.get("training", {}).get("train_split_ratio", 0.8)

def set_config(key: str, value: Any) -> None:
    """Set a configuration value."""
    config = get_config()
    if '.' in key:
        parts = key.split('.')
        current = config._config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    else:
        config._config[key] = value
