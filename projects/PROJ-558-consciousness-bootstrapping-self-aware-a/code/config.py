"""
Configuration management for the Consciousness Bootstrapping project.

This module manages hyperparameters and enforces CPU-only execution constraints
as required by the project's infrastructure limitations.
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
    Central configuration for the Consciousness Bootstrapping pipeline.

    Attributes:
        seed (int): Random seed for reproducibility.
        batch_size (int): Batch size for training and evaluation.
        recursion_depth (int): Maximum depth for recursive self-attention (default: 2).
        learning_rate (float): Learning rate for the optimizer.
        token_limit (int): Maximum number of tokens to process (default: 100000).
        device (str): Device to run on ('cpu' enforced).
        model_name (str): Name of the base model (e.g., 'TinyLlama/TinyLlama-1.1B-Chat-v1.0').
        max_steps (int): Maximum number of training steps.
        warmup_steps (int): Number of warmup steps for learning rate scheduler.
        output_dir (str): Directory to save checkpoints and results.
        data_dir (str): Directory for raw and processed data.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    seed: int = 42
    batch_size: int = 4
    recursion_depth: int = 2
    learning_rate: float = 2e-4
    token_limit: int = 100000
    device: str = "cpu"
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    max_steps: int = 1000
    warmup_steps: int = 100
    output_dir: str = "artifacts/results"
    data_dir: str = "data"
    log_level: str = "INFO"
    # Additional constraints
    max_memory_gb: float = 7.0  # Hard limit for CI runner
    enable_mixed_precision: bool = False  # Disabled for CPU stability

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_cpu_only()
        self._validate_recursion_depth()
        self._validate_hyperparameters()

    def _validate_cpu_only(self):
        """Enforce CPU-only execution constraint."""
        if torch.cuda.is_available():
            logger.warning(
                "CUDA is available, but CPU-only execution is enforced by project constraints. "
                "Forcing device to 'cpu'."
            )
        self.device = "cpu"
        if not torch.backends.mps.is_available():
            # Ensure MPS (Apple Silicon) is also disabled if strictly CPU-only is required
            # Note: MPS is often considered a 'CPU-like' backend in this context, but if strict CPU is needed:
            pass
        
        # Explicitly set torch default device
        torch.set_default_device("cpu")

    def _validate_recursion_depth(self):
        """Validate recursion depth constraints."""
        if self.recursion_depth < 1:
            raise ConfigurationError(
                f"Recursion depth must be >= 1, got {self.recursion_depth}"
            )
        if self.recursion_depth > 2:
            raise ConfigurationError(
                f"Recursion depth > 2 is prohibited by project constraints (OOM risk). "
                f"Got {self.recursion_depth}"
            )

    def _validate_hyperparameters(self):
        """Validate hyperparameter ranges."""
        if self.batch_size < 1:
            raise ConfigurationError(f"Batch size must be >= 1, got {self.batch_size}")
        if self.learning_rate <= 0:
            raise ConfigurationError(f"Learning rate must be > 0, got {self.learning_rate}")
        if self.token_limit < 100:
            raise ConfigurationError(f"Token limit too low ({self.token_limit}), minimum 100.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "seed": self.seed,
            "batch_size": self.batch_size,
            "recursion_depth": self.recursion_depth,
            "learning_rate": self.learning_rate,
            "token_limit": self.token_limit,
            "device": self.device,
            "model_name": self.model_name,
            "max_steps": self.max_steps,
            "warmup_steps": self.warmup_steps,
            "output_dir": self.output_dir,
            "data_dir": self.data_dir,
            "log_level": self.log_level,
            "max_memory_gb": self.max_memory_gb,
            "enable_mixed_precision": self.enable_mixed_precision,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_env(cls, prefix: str = "CONSCIOUSNESS_") -> "Config":
        """Create configuration from environment variables."""
        data = {}
        for field_name in cls.__dataclass_fields__:
            env_key = f"{prefix}{field_name.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]
                # Type conversion
                field_type = cls.__dataclass_fields__[field_name].type
                if field_type == int:
                    data[field_name] = int(value)
                elif field_type == float:
                    data[field_name] = float(value)
                elif field_type == bool:
                    data[field_name] = value.lower() in ("true", "1", "yes")
                else:
                    data[field_name] = value
        return cls(**data)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        # Try to load from env, else default
        _config = Config.from_env()
        logger.info(f"Loaded configuration: {_config.to_dict()}")
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
    logger.info(f"Set configuration: {_config.to_dict()}")


def validate_config(config: Optional[Config] = None) -> bool:
    """
    Validate a configuration object.
    
    Args:
        config: Configuration to validate. If None, uses global config.
        
    Returns:
        True if valid, raises ConfigurationError otherwise.
    """
    if config is None:
        config = get_config()
    
    # The dataclass __post_init__ already runs validation,
    # but we call it explicitly here for clarity if needed.
    # Re-triggering validation logic manually if __post_init__ side effects are needed
    try:
        config._validate_cpu_only()
        config._validate_recursion_depth()
        config._validate_hyperparameters()
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"Configuration validation failed: {e}")
        
    return True


def main():
    """Main entry point for config testing."""
    print("Running config validation...")
    try:
        cfg = get_config()
        validate_config(cfg)
        print(f"Configuration valid: {cfg.to_dict()}")
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        exit(1)


if __name__ == "__main__":
    main()