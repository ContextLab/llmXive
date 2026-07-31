import os
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from utils.logging import get_logger, ConfigurationError

logger = get_logger(__name__)

@dataclass
class Config:
    """
    Configuration management for the Consciousness Bootstrapping project.
    
    This class enforces strict validation of hyperparameters, particularly
    the token_limit which must be exactly 100000 as per project specifications.
    """
    
    # Core Hyperparameters
    seed: int = 42
    batch_size: int = 4
    recursion_depth: int = 2
    learning_rate: float = 1e-4
    
    # CRITICAL: Token limit constraint
    # Must be exactly 100000. No fallbacks allowed.
    token_limit: int = 100000
    
    # Training parameters
    num_epochs: int = 1
    max_steps: Optional[int] = None
    warmup_steps: int = 100
    
    # Model parameters
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    hidden_size: int = 768
    num_attention_heads: int = 12
    num_hidden_layers: int = 12
    
    # Evaluation parameters
    self_consistency_n: int = 5
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Paths
    data_dir: str = "data"
    output_dir: str = "artifacts"
    checkpoint_dir: str = "artifacts/checkpoints"
    results_dir: str = "artifacts/results"
    
    # Device configuration
    device: str = "cpu"
    use_cpu_only: bool = True

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def set_config(new_config: Config) -> None:
    """Set a new config instance (useful for testing)."""
    global _config_instance
    _config_instance = new_config

def validate_config(config: Optional[Config] = None) -> None:
    """
    Validate the configuration, with strict enforcement on token_limit.
    
    Raises:
        ConfigurationError: If token_limit is not exactly 100000 or if
            other critical constraints are violated.
    """
    if config is None:
        config = get_config()
    
    # CRITICAL: Token limit validation
    if config.token_limit != 100000:
        raise ConfigurationError(
            f"token_limit must be exactly 100000. "
            f"Current value: {config.token_limit}. "
            f"This is a hard constraint per project specification."
        )
    
    # Validate recursion depth
    if config.recursion_depth < 1 or config.recursion_depth > 2:
        raise ConfigurationError(
            f"recursion_depth must be between 1 and 2. "
            f"Current value: {config.recursion_depth}"
        )
    
    # Validate batch size
    if config.batch_size < 1:
        raise ConfigurationError(
            f"batch_size must be at least 1. "
            f"Current value: {config.batch_size}"
        )
    
    # Validate learning rate
    if config.learning_rate <= 0:
        raise ConfigurationError(
            f"learning_rate must be positive. "
            f"Current value: {config.learning_rate}"
        )
    
    # Validate device configuration
    if config.use_cpu_only and not config.device == "cpu":
        logger.warning(
            f"use_cpu_only is True but device is set to '{config.device}'. "
            f"Overriding to 'cpu'."
        )
        config.device = "cpu"
    
    logger.info("Configuration validated successfully.")
    logger.info(f"  token_limit: {config.token_limit}")
    logger.info(f"  recursion_depth: {config.recursion_depth}")
    logger.info(f"  batch_size: {config.batch_size}")
    logger.info(f"  learning_rate: {config.learning_rate}")
    logger.info(f"  device: {config.device}")

def main():
    """Main entry point for config validation."""
    try:
        config = get_config()
        validate_config(config)
        logger.info("Config validation PASSED.")
        return 0
    except ConfigurationError as e:
        logger.error(f"Config validation FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during config validation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())