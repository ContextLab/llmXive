import os
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from utils.logging import get_logger, ConfigurationError

logger = get_logger(__name__)

@dataclass
class Config:
    """
    Configuration container for the Consciousness Bootstrapping project.
    Manages hyperparameters and runtime settings.
    """
    # Randomness
    seed: int = 42
    
    # Training
    batch_size: int = 4
    learning_rate: float = 1e-4
    recursion_depth: int = 2  # FR-001: Temporal recursive self-attention depth
    
    # Data & Limits
    # Constitution Principle VII & FR-002: Token limit MUST be 100,000
    token_limit: int = 100000
    
    # Model
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    max_length: int = 2048
    
    # Evaluation
    num_workers: int = 0
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Paths
    data_dir: str = "data"
    output_dir: str = "artifacts"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        validate_config(self)

_global_config: Optional[Config] = None

def get_config() -> Config:
    """
    Returns the global configuration instance.
    Creates a default one if none exists.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_config(config: Config) -> None:
    """
    Sets the global configuration instance.
    """
    global _global_config
    _global_config = config
    logger.info("Global configuration updated.")

def validate_config(config: Config) -> None:
    """
    Validates the configuration against project constraints.
    
    Raises:
        ConfigurationError: If any constraint is violated.
    """
    if config.token_limit is None or not isinstance(config.token_limit, int):
        raise ConfigurationError(
            f"token_limit must be an integer. Got {type(config.token_limit)}."
        )
    
    # Constitution Principle VII: token_limit MUST be 100,000
    if config.token_limit != 100000:
        raise ConfigurationError(
            f"token_limit must be exactly 100000 (100k) as per Constitution Principle VII. "
            f"Current value: {config.token_limit}"
        )
    
    if config.recursion_depth < 1:
        raise ConfigurationError("recursion_depth must be at least 1.")
    
    if config.batch_size < 1:
        raise ConfigurationError("batch_size must be at least 1.")
    
    if config.learning_rate <= 0:
        raise ConfigurationError("learning_rate must be positive.")
    
    logger.info("Configuration validation passed.")

def main() -> None:
    """
    Entry point for testing configuration validation.
    """
    try:
        config = get_config()
        validate_config(config)
        print(f"Config loaded successfully:")
        print(f"  Seed: {config.seed}")
        print(f"  Batch Size: {config.batch_size}")
        print(f"  Recursion Depth: {config.recursion_depth}")
        print(f"  Learning Rate: {config.learning_rate}")
        print(f"  Token Limit: {config.token_limit}")
    except ConfigurationError as e:
        print(f"Configuration Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()