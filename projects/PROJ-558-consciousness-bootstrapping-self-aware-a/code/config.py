"""
Configuration management for the Consciousness Bootstrapping project.

This module manages hyperparameters, enforces CPU-only execution constraints,
and provides a centralized configuration interface for the entire pipeline.
"""
import os
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from utils.logging import get_logger, ConfigurationError

from utils.logging import get_logger, ConfigurationError as LoggingConfigError

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class Config:
    """
    Central configuration class for the Consciousness Bootstrapping project.

    Attributes:
        seed (int): Random seed for reproducibility.
        batch_size (int): Training batch size.
        recursion_depth (int): Maximum recursion depth for self-attention (default: 2).
        learning_rate (float): Learning rate for optimizer.
        token_limit (int): Maximum number of tokens for dataset truncation.
        cpu_only (bool): Enforce CPU-only execution.
        model_name (str): Name of the base model to use.
        max_epochs (int): Maximum number of training epochs.
        output_dir (str): Directory for saving checkpoints and results.
    """

    def __init__(
        self,
        seed: int = 42,
        batch_size: int = 4,
        recursion_depth: int = 2,
        learning_rate: float = 1e-4,
        token_limit: int = 100000,
        cpu_only: bool = True,
        model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v0.3",
        max_epochs: int = 3,
        output_dir: str = "artifacts/checkpoints",
        data_dir: str = "data/raw",
        results_dir: str = "artifacts/results",
        log_level: str = "INFO",
    ):
        self.seed = seed
        self.batch_size = batch_size
        self.recursion_depth = recursion_depth
        self.learning_rate = learning_rate
        self.token_limit = token_limit
        self.cpu_only = cpu_only
        self.model_name = model_name
        self.max_epochs = max_epochs
        self.output_dir = output_dir
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.log_level = log_level

        # Enforce constraints immediately upon initialization
        self._enforce_constraints()

    def _enforce_constraints(self) -> None:
        """
        Enforce project-specific constraints, particularly CPU-only execution.

        Raises:
            ConfigurationError: If constraints cannot be satisfied.
        """
        if self.cpu_only:
            if torch.cuda.is_available():
                logger.warning(
                    "CUDA is available, but CPU-only mode is enforced. "
                    "Disabling GPU usage."
                )
            # Explicitly set device to CPU
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            logger.info("CPU-only execution enforced. GPU access disabled.")
        
        # Validate recursion depth constraint
        if self.recursion_depth > 2:
            raise ConfigurationError(
                f"Recursion depth {self.recursion_depth} exceeds maximum allowed value of 2. "
                "This is a hard constraint per project specifications."
            )
        
        # Validate token limit
        if self.token_limit <= 0:
            raise ConfigurationError(
                f"Token limit must be positive, got {self.token_limit}."
            )

        # Validate batch size
        if self.batch_size <= 0:
            raise ConfigurationError(
                f"Batch size must be positive, got {self.batch_size}."
            )

        logger.info(f"Configuration validated: seed={self.seed}, batch_size={self.batch_size}, "
                   f"recursion_depth={self.recursion_depth}, token_limit={self.token_limit}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "seed": self.seed,
            "batch_size": self.batch_size,
            "recursion_depth": self.recursion_depth,
            "learning_rate": self.learning_rate,
            "token_limit": self.token_limit,
            "cpu_only": self.cpu_only,
            "model_name": self.model_name,
            "max_epochs": self.max_epochs,
            "output_dir": self.output_dir,
            "data_dir": self.data_dir,
            "results_dir": self.results_dir,
            "log_level": self.log_level,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary."""
        return cls(
            seed=config_dict.get("seed", 42),
            batch_size=config_dict.get("batch_size", 4),
            recursion_depth=config_dict.get("recursion_depth", 2),
            learning_rate=config_dict.get("learning_rate", 1e-4),
            token_limit=config_dict.get("token_limit", 100000),
            cpu_only=config_dict.get("cpu_only", True),
            model_name=config_dict.get("model_name", "TinyLlama/TinyLlama-1.1B-Chat-v0.3"),
            max_epochs=config_dict.get("max_epochs", 3),
            output_dir=config_dict.get("output_dir", "artifacts/checkpoints"),
            data_dir=config_dict.get("data_dir", "data/raw"),
            results_dir=config_dict.get("results_dir", "artifacts/results"),
            log_level=config_dict.get("log_level", "INFO"),
        )


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config: The global configuration object.
    
    Raises:
        ConfigurationError: If configuration has not been initialized.
    """
    global _global_config
    if _global_config is None:
        raise ConfigurationError(
            "Configuration not initialized. Call set_config() or main() first."
        )
    return _global_config


def set_config(config: Optional[Config] = None, **kwargs) -> Config:
    """
    Set or update the global configuration.

    Args:
        config: A Config instance to set as global.
        **kwargs: Parameters to update in the existing config or create a new one.
    
    Returns:
        Config: The updated global configuration.
    """
    global _global_config
    
    if config is not None:
        _global_config = config
    elif kwargs:
        if _global_config is None:
            _global_config = Config(**kwargs)
        else:
            # Update existing config with new values
            for key, value in kwargs.items():
                if hasattr(_global_config, key):
                    setattr(_global_config, key, value)
                else:
                    raise ConfigurationError(f"Unknown configuration parameter: {key}")
    else:
        # Initialize with defaults if no config provided
        _global_config = Config()
    
    logger.info("Global configuration set.")
    return _global_config


def validate_config(config: Optional[Config] = None) -> bool:
    """
    Validate a configuration instance.

    Args:
        config: Configuration to validate. If None, uses global config.
    
    Returns:
        bool: True if valid.
    
    Raises:
        ConfigurationError: If validation fails.
    """
    if config is None:
        config = get_config()
    
    # Re-run constraint enforcement
    config._enforce_constraints()
    return True


def main():
    """
    Main entry point for testing configuration.
    """
    logger.info("Testing configuration module...")
    
    # Test default configuration
    config = Config()
    logger.info(f"Default config: {config.to_dict()}")
    
    # Test custom configuration
    custom_config = Config(
        seed=123,
        batch_size=8,
        recursion_depth=2,
        learning_rate=5e-5,
        token_limit=50000,
        cpu_only=True,
    )
    logger.info(f"Custom config: {custom_config.to_dict()}")
    
    # Test global config setting
    set_config(custom_config)
    global_config = get_config()
    logger.info(f"Global config: {global_config.to_dict()}")
    
    # Test validation
    try:
        validate_config()
        logger.info("Configuration validation passed.")
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
    
    # Test recursion depth constraint violation
    try:
        bad_config = Config(recursion_depth=3)
        logger.error("Should have raised ConfigurationError for recursion_depth > 2")
    except ConfigurationError as e:
        logger.info(f"Correctly caught constraint violation: {e}")
    
    logger.info("Configuration module test complete.")


if __name__ == "__main__":
    main()
