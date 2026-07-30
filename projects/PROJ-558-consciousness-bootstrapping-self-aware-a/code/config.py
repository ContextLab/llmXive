"""
Configuration management for the Consciousness Bootstrapping project.

Manages hyperparameters and enforces CPU-only execution constraints.
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
    Central configuration container for the project.
    
    Attributes:
        seed: Random seed for reproducibility (default: 42).
        batch_size: Training batch size (default: 4).
        recursion_depth: Maximum depth of recursive self-attention (default: 2).
        learning_rate: Learning rate for optimizer (default: 1e-4).
        token_limit: Maximum tokens per context (default: 100000).
        num_epochs: Number of training epochs (default: 1).
        device: Execution device ('cpu' enforced).
        model_name: HuggingFace model identifier (default: 'TinyLlama/TinyLlama-1.1B-Chat-v1.0').
        data_path: Path to raw data directory.
        output_path: Path to output artifacts directory.
        log_level: Logging level (default: 'INFO').
    """
    seed: int = 42
    batch_size: int = 4
    recursion_depth: int = 2
    learning_rate: float = 1e-4
    token_limit: int = 100000
    num_epochs: int = 1
    device: str = field(default="cpu", init=False)
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    data_path: str = "data/raw"
    output_path: str = "artifacts"
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Enforce CPU-only execution and validate constraints."""
        self._enforce_cpu_only()
        self._validate_constraints()
        
    def _enforce_cpu_only(self):
        """
        Force execution on CPU to comply with CI constraints.
        Raises ConfigurationError if GPU is detected and forced.
        """
        if torch.cuda.is_available():
            logger.warning("CUDA detected, but configuration enforces CPU-only execution.")
        # Explicitly set device to CPU regardless of availability
        self.device = "cpu"
        logger.info(f"Execution device enforced: {self.device}")
        
    def _validate_constraints(self):
        """Validate hyperparameter constraints."""
        if self.recursion_depth < 0:
            raise ConfigurationError("Recursion depth must be non-negative.")
        if self.recursion_depth > 2:
            # Hard constraint as per spec/edge cases
            raise ConfigurationError(
                f"Recursion depth {self.recursion_depth} exceeds maximum allowed (2). "
                "Configuration validation failed."
            )
        if self.token_limit <= 0:
            raise ConfigurationError("Token limit must be positive.")
        if self.batch_size <= 0:
            raise ConfigurationError("Batch size must be positive.")
        if self.learning_rate <= 0:
            raise ConfigurationError("Learning rate must be positive.")
            
        logger.info("Configuration validation passed.")

# Global configuration instance
_global_config: Optional[Config] = None

def get_config() -> Config:
    """
    Retrieve the global configuration instance.
    Creates a new instance if none exists.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_config(config: Config) -> None:
    """
    Set the global configuration instance.
    """
    global _global_config
    _global_config = config
    logger.info("Global configuration updated.")

def validate_config(config: Optional[Config] = None) -> bool:
    """
    Validate a configuration instance.
    Returns True if valid, raises ConfigurationError otherwise.
    """
    if config is None:
        config = get_config()
    try:
        # Trigger validation via __post_init__ logic if needed
        # Re-instantiating to ensure validation runs if state changed
        Config(
            seed=config.seed,
            batch_size=config.batch_size,
            recursion_depth=config.recursion_depth,
            learning_rate=config.learning_rate,
            token_limit=config.token_limit,
            num_epochs=config.num_epochs,
            model_name=config.model_name,
            data_path=config.data_path,
            output_path=config.output_path,
            log_level=config.log_level
        )
        return True
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

def main():
    """
    CLI entry point for configuration validation and display.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Configuration Manager")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--recursion-depth", type=int, default=2, help="Recursion depth")
    parser.add_argument("--learning-rate", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--token-limit", type=int, default=100000, help="Token limit")
    parser.add_argument("--device", type=str, default="cpu", help="Target device (ignored, forced to cpu)")
    
    args = parser.parse_args()
    
    try:
        config = Config(
            seed=args.seed,
            batch_size=args.batch_size,
            recursion_depth=args.recursion_depth,
            learning_rate=args.learning_rate,
            token_limit=args.token_limit
        )
        
        logger.info("Configuration loaded successfully:")
        logger.info(f"  Seed: {config.seed}")
        logger.info(f"  Batch Size: {config.batch_size}")
        logger.info(f"  Recursion Depth: {config.recursion_depth}")
        logger.info(f"  Learning Rate: {config.learning_rate}")
        logger.info(f"  Token Limit: {config.token_limit}")
        logger.info(f"  Device: {config.device}")
        
        # Validate
        validate_config(config)
        logger.info("Validation successful.")
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)

if __name__ == "__main__":
    main()