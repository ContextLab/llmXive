"""
Model configuration constants and utilities.
"""
from typing import Dict, Any, Optional

# Core model hyperparameters
EMBED_DIM = 768
NUM_HEADS = 12
PARAMS = 100000000  # 100M parameters target
VOCAB_SIZE = 50257  # GPT-2 vocab size
MAX_SEQ_LENGTH = 512

# Training hyperparameters
LEARNING_RATE = 1e-4
BATCH_SIZE = 8
NUM_EPOCHS = 100

# Resource constraints
MAX_RAM_GB = 8.0
TOKEN_LIMIT = 10000000  # 10M tokens target

class ConfigError(Exception):
    """Raised when model configuration is invalid."""
    pass

def get_model_config(model_type: str = "autoregressive") -> Dict[str, Any]:
    """
    Get configuration dictionary for a specific model type.
    
    Args:
        model_type: Type of model ("autoregressive" or "diffusion")
        
    Returns:
        Configuration dictionary
    """
    base_config = {
        "embed_dim": EMBED_DIM,
        "num_heads": NUM_HEADS,
        "vocab_size": VOCAB_SIZE,
        "max_seq_length": MAX_SEQ_LENGTH,
        "learning_rate": LEARNING_RATE,
        "batch_size": BATCH_SIZE,
        "num_epochs": NUM_EPOCHS,
    }
    
    if model_type == "autoregressive":
        base_config["model_type"] = "causal_lm"
    elif model_type == "diffusion":
        base_config["model_type"] = "bidirectional_md"
    else:
        raise ConfigError(f"Unknown model type: {model_type}")
        
    return base_config

# Getters for individual parameters
def get_embed_dim() -> int:
    return EMBED_DIM

def get_num_heads() -> int:
    return NUM_HEADS

def get_vocab_size() -> int:
    return VOCAB_SIZE

def get_max_seq_length() -> int:
    return MAX_SEQ_LENGTH

def get_learning_rate() -> float:
    return LEARNING_RATE

def get_batch_size() -> int:
    return BATCH_SIZE

def get_num_epochs() -> int:
    return NUM_EPOCHS
