"""
Configuration management utilities for llmXive.
Handles loading, saving, and accessing configuration parameters from code/config.yaml.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Global config cache
_config_cache: Optional[Dict[str, Any]] = None

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def get_project_root() -> Path:
    """Returns the project root directory."""
    # Assuming the script is run from the project root or a subdirectory
    return Path(__file__).resolve().parent.parent.parent

def get_config_path() -> Path:
    """Returns the path to the config.yaml file."""
    return get_project_root() / "code" / "config.yaml"

def get_data_dir() -> Path:
    """Returns the data directory."""
    return get_project_root() / "data"

def get_raw_dir() -> Path:
    """Returns the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Returns the processed data directory."""
    return get_data_dir() / "processed"

def get_artifacts_dir() -> Path:
    """Returns the artifacts directory."""
    return get_data_dir() / "artifacts"

def load_config() -> Dict[str, Any]:
    """
    Loads the configuration from code/config.yaml.
    Caches the result to avoid repeated file I/O.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = get_config_path()
    if not config_path.exists():
        raise ConfigError(f"Config file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            _config_cache = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config.yaml: {e}")

    if _config_cache is None:
        raise ConfigError("Config file is empty.")

    return _config_cache

def save_config(config: Dict[str, Any]) -> None:
    """
    Saves the configuration to code/config.yaml.
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise ConfigError(f"Failed to save config.yaml: {e}")

def reset_config() -> None:
    """Resets the configuration cache."""
    global _config_cache
    _config_cache = None

def get_config() -> Dict[str, Any]:
    """Alias for load_config()."""
    return load_config()

# Helper functions to access specific config values
def get_token_limit() -> int:
    config = load_config()
    return config.get("token_target", 1_000_000)

def get_max_ram_gb() -> float:
    return 7.0  # Hardcoded default, can be moved to config if needed

def get_train_split_ratio() -> float:
    config = load_config()
    return config.get("train_split_ratio", 0.9)

def get_learning_rate() -> float:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("learning_rate", 1e-4)

def get_batch_size() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("batch_size", 32)

def get_num_epochs() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("num_epochs", 5)

def get_max_seq_length() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("max_seq_length", 512)

def get_vocab_size() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("vocab_size", 50257)

def get_embed_dim() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("d_model", 512)

def get_num_heads() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("num_heads", 8)

def get_num_layers() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("num_layers", 8)

def get_device() -> str:
    config = load_config()
    return config.get("device", "cpu")

def get_dropout() -> float:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("dropout", 0.1)

def get_weight_decay() -> float:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("weight_decay", 0.01)

def get_warmup_steps() -> int:
    config = load_config()
    params = config.get("model_params", {})
    return params.get("warmup_steps", 100)