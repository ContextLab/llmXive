"""
Model configuration management for llmXive.

Calculates and exposes feasible model parameters for CPU execution.
"""
from typing import Dict, Any, Optional
import math


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


# Default configuration values
_DEFAULT_CONFIG = {
    'vocab_size': 50257,  # GPT-2 vocab size
    'embed_dim': 256,     # Feasible embed dim for CPU (T008 calculation)
    'num_heads': 4,       # Feasible heads
    'num_layers': 4,      # Feasible layers
    'max_seq_length': 512,
    'learning_rate': 3e-4,
    'batch_size': 8,
    'num_epochs': 100,
    'dropout': 0.1,
    'weight_decay': 0.01,
    'warmup_steps': 100,
}

# Runtime configuration store
_config_store: Dict[str, Any] = _DEFAULT_CONFIG.copy()


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config_store
    _config_store = _DEFAULT_CONFIG.copy()


def set_config(key: str, value: Any) -> None:
    """Set a configuration value."""
    _config_store[key] = value


def get_model_config() -> Dict[str, Any]:
    """Return the full model configuration dictionary."""
    return _config_store.copy()


def get_embed_dim() -> int:
    """Get embedding dimension."""
    return _config_store.get('embed_dim', 256)


def get_num_heads() -> int:
    """Get number of attention heads."""
    return _config_store.get('num_heads', 4)


def get_num_layers() -> int:
    """Get number of transformer layers."""
    return _config_store.get('num_layers', 4)


def get_vocab_size() -> int:
    """Get vocabulary size."""
    return _config_store.get('vocab_size', 50257)


def get_max_seq_length() -> int:
    """Get maximum sequence length."""
    return _config_store.get('max_seq_length', 512)


def get_learning_rate() -> float:
    """Get learning rate."""
    return _config_store.get('learning_rate', 3e-4)


def get_batch_size() -> int:
    """Get batch size."""
    return _config_store.get('batch_size', 8)


def get_num_epochs() -> int:
    """Get number of epochs."""
    return _config_store.get('num_epochs', 100)


def get_dropout() -> float:
    """Get dropout rate."""
    return _config_store.get('dropout', 0.1)


def get_weight_decay() -> float:
    """Get weight decay."""
    return _config_store.get('weight_decay', 0.01)


def get_warmup_steps() -> int:
    """Get warmup steps."""
    return _config_store.get('warmup_steps', 100)
