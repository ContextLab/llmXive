"""
Configuration management for the Consciousness Bootstrapping project.

This module provides a centralized configuration system for managing hyperparameters
and settings across the project. It uses a dataclass for immutable configuration
values with validation.
"""

import os
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from utils.logging import get_logger, ConfigurationError

logger = get_logger(__name__)


@dataclass
class Config:
    """
    Central configuration class for the project.

    Attributes:
        seed (int): Random seed for reproducibility.
        batch_size (int): Batch size for training.
        recursion_depth (int): Maximum depth of recursive self-attention (default 2).
        learning_rate (float): Learning rate for the optimizer.
        token_limit (int): Maximum number of tokens to process (default 100000).
        device (str): Device to use for training ('cpu' or 'cuda').
        num_workers (int): Number of workers for data loading.
        max_epochs (int): Maximum number of training epochs.
        warmup_steps (int): Number of warmup steps for learning rate scheduler.
        weight_decay (float): Weight decay for optimizer.
        log_interval (int): Log training progress every N steps.
        save_interval (int): Save checkpoint every N steps.
        validation_interval (int): Run validation every N steps.
    """
    seed: int = 42
    batch_size: int = 4
    recursion_depth: int = 2
    learning_rate: float = 1e-4
    token_limit: int = 100000  # CRITICAL: Must be 100000 as per spec requirement
    device: str = 'cpu'
    num_workers: int = 0
    max_epochs: int = 10
    warmup_steps: int = 100
    weight_decay: float = 0.01
    log_interval: int = 10
    save_interval: int = 100
    validation_interval: int = 500

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.token_limit <= 0:
            raise ConfigurationError(f"token_limit must be positive, got {self.token_limit}")
        
        if self.recursion_depth < 1:
            raise ConfigurationError(f"recursion_depth must be at least 1, got {self.recursion_depth}")
        
        if self.batch_size <= 0:
            raise ConfigurationError(f"batch_size must be positive, got {self.batch_size}")
        
        if self.learning_rate <= 0:
            raise ConfigurationError(f"learning_rate must be positive, got {self.learning_rate}")
        
        if self.seed < 0:
            raise ConfigurationError(f"seed must be non-negative, got {self.seed}")

        logger.info(f"Configuration initialized: seed={self.seed}, batch_size={self.batch_size}, "
                   f"recursion_depth={self.recursion_depth}, learning_rate={self.learning_rate}, "
                   f"token_limit={self.token_limit}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The current configuration.
        
    Raises:
        ConfigurationError: If configuration has not been initialized.
    """
    global _config
    if _config is None:
        raise ConfigurationError("Configuration not initialized. Call set_config() first.")
    return _config


def set_config(config: Optional[Config] = None, **kwargs) -> Config:
    """
    Set the global configuration instance.
    
    Args:
        config: A Config instance to use, or None to create a new one with kwargs.
        **kwargs: Configuration values to override defaults when creating new config.
                
    Returns:
        Config: The updated configuration.
    """
    global _config
    
    if config is not None:
        _config = config
    else:
        _config = Config(**kwargs)
    
    logger.info(f"Configuration set: {vars(_config)}")
    return _config


def validate_config(config: Optional[Config] = None) -> bool:
    """
    Validate the configuration.
    
    Args:
        config: Configuration to validate. If None, uses global config.
                
    Returns:
        bool: True if valid.
        
    Raises:
        ConfigurationError: If validation fails.
    """
    global _config
    config_to_validate = config if config is not None else _config
    
    if config_to_validate is None:
        raise ConfigurationError("No configuration to validate. Call set_config() first.")
    
    try:
        # Force validation by accessing __post_init__
        config_to_validate.__post_init__()
        logger.info("Configuration validation successful")
        return True
    except (ConfigurationError, ValueError) as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ConfigurationError(f"Invalid configuration: {e}")


def main():
    """
    Main function to demonstrate configuration usage.
    This can be run as a script to test configuration validation.
    """
    print("Testing configuration initialization...")
    
    # Test default configuration
    try:
        config = set_config()
        print(f"Default config created: {config}")
        validate_config(config)
        print("✓ Default configuration is valid")
    except ConfigurationError as e:
        print(f"✗ Default configuration failed: {e}")
        return 1
    
    # Test custom configuration with token_limit=100000
    try:
        custom_config = set_config(
            seed=123,
            batch_size=8,
            recursion_depth=2,
            learning_rate=5e-5,
            token_limit=100000  # Explicitly set as required
        )
        print(f"Custom config created: {custom_config}")
        validate_config(custom_config)
        print("✓ Custom configuration is valid")
    except ConfigurationError as e:
        print(f"✗ Custom configuration failed: {e}")
        return 1
    
    # Test invalid configuration (negative token_limit)
    try:
        invalid_config = set_config(token_limit=-1)
        validate_config(invalid_config)
        print("✗ Invalid configuration should have failed!")
        return 1
    except ConfigurationError:
        print("✓ Invalid configuration correctly rejected")
    
    # Test invalid configuration (zero recursion_depth)
    try:
        invalid_config = set_config(recursion_depth=0)
        validate_config(invalid_config)
        print("✗ Invalid configuration should have failed!")
        return 1
    except ConfigurationError:
        print("✓ Invalid configuration correctly rejected")
    
    print("\nAll configuration tests passed!")
    return 0


if __name__ == "__main__":
    exit(main())
