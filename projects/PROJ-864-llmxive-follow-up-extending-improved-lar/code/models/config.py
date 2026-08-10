"""
Model configuration constants and utilities.

This module defines the hyperparameters and configuration logic for the
Autoregressive and Diffusion models.
"""

from typing import Dict, Any, Optional

class ConfigError(Exception):
    """Raised when a configuration value is missing or invalid."""
    pass

# Default configuration values (can be overridden by external config files)
_DEFAULT_CONFIG = {
    "embed_dim": 768,
    "num_heads": 12,
    "num_layers": 12,
    "vocab_size": 50257,  # GPT-2 vocab size
    "max_seq_length": 1024,
    "learning_rate": 1e-4,
    "batch_size": 16,
    "num_epochs": 100,
    "dropout": 0.1,
    "weight_decay": 0.01,
    "warmup_steps": 1000
}

# Global config storage (simulating a config manager)
_config: Dict[str, Any] = {}

def get_model_config() -> Dict[str, Any]:
    """
    Retrieve the full model configuration dictionary.

    Returns:
        Dict containing all model hyperparameters.
    """
    if not _config:
        return _DEFAULT_CONFIG.copy()
    return _config.copy()

def get_embed_dim() -> int:
    """Get the embedding dimension."""
    return _config.get("embed_dim", _DEFAULT_CONFIG["embed_dim"])

def get_num_heads() -> int:
    """Get the number of attention heads."""
    return _config.get("num_heads", _DEFAULT_CONFIG["num_heads"])

def get_num_layers() -> int:
    """Get the number of transformer layers."""
    return _config.get("num_layers", _DEFAULT_CONFIG["num_layers"])

def get_vocab_size() -> int:
    """Get the vocabulary size."""
    return _config.get("vocab_size", _DEFAULT_CONFIG["vocab_size"])

def get_max_seq_length() -> int:
    """Get the maximum sequence length."""
    return _config.get("max_seq_length", _DEFAULT_CONFIG["max_seq_length"])

def get_learning_rate() -> float:
    """Get the learning rate."""
    return _config.get("learning_rate", _DEFAULT_CONFIG["learning_rate"])

def get_batch_size() -> int:
    """Get the batch size."""
    return _config.get("batch_size", _DEFAULT_CONFIG["batch_size"])

def get_num_epochs() -> int:
    """Get the number of training epochs."""
    return _config.get("num_epochs", _DEFAULT_CONFIG["num_epochs"])

def get_dropout() -> float:
    """Get the dropout rate."""
    return _config.get("dropout", _DEFAULT_CONFIG["dropout"])

def get_weight_decay() -> float:
    """Get the weight decay parameter."""
    return _config.get("weight_decay", _DEFAULT_CONFIG["weight_decay"])

def get_warmup_steps() -> int:
    """Get the number of warmup steps."""
    return _config.get("warmup_steps", _DEFAULT_CONFIG["warmup_steps"])

def reset_config() -> None:
    """Reset the configuration to defaults."""
    global _config
    _config = {}

def set_config(key: str, value: Any) -> None:
    """
    Set a specific configuration value.

    Args:
        key: Configuration key name.
        value: Value to set.
    """
    global _config
    _config[key] = value
