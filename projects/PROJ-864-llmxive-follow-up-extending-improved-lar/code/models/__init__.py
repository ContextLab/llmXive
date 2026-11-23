"""
Models package for llmXive Follow-up: Extending Improved Large Language Diffusion Models.

This package contains the implementation of the Autoregressive and Diffusion models
used in the comparative study.
"""

from models.autoregressive import AutoregressiveModel, create_autoregressive_model
from models.diffusion import DiffusionModel, create_diffusion_model
from models.config import (
    get_model_config,
    get_embed_dim,
    get_num_heads,
    get_vocab_size,
    get_max_seq_length,
    ConfigError
)

__all__ = [
    "AutoregressiveModel",
    "create_autoregressive_model",
    "DiffusionModel",
    "create_diffusion_model",
    "get_model_config",
    "get_embed_dim",
    "get_num_heads",
    "get_vocab_size",
    "get_max_seq_length",
    "ConfigError"
]
