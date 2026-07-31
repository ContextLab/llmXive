import os
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from utils.logging import get_logger, ConfigurationError

logger = get_logger(__name__)

@dataclass
class Config:
    """
    Central configuration for the Consciousness Bootstrapping project.
    Manages hyperparameters and critical constraints.
    """
    # Core Hyperparameters
    seed: int = 42
    batch_size: int = 4
    learning_rate: float = 1e-4
    recursion_depth: int = 2  # FR-001 constraint: max depth 2
    epochs: int = 3
    
    # Critical Constraint: Token Limit
    # Must be exactly 100000 as per spec FR-002 and T005 requirements.
    # No fallback allowed.
    token_limit: int = 100000
    
    # Model Specifics
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    max_sequence_length: int = 2048
    
    # Training Configuration
    use_cpu: bool = True
    gradient_accumulation_steps: int = 1
    warmup_steps: int = 100
    weight_decay: float = 0.01
    
    # Evaluation Configuration
    evaluation_batch_size: int = 1
    num_reasoning_paths: int = 10  # For self-consistency benchmark (N=10)
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Paths
    data_dir: str = "data"
    output_dir: str = "artifacts/results"
    checkpoint_dir: str = "artifacts/checkpoints"

# Global configuration instance
_config: Optional[Config] = None

def get_config() -> Config:
    """
    Returns the global configuration instance.
    Initializes it if not already set.
    """
    global _config
    if _config is None:
        _config = Config()
        # Validate immediately upon first access
        validate_config(_config)
    return _config

def set_config(new_config: Config) -> None:
    """
    Updates the global configuration instance.
    """
    global _config
    _config = new_config
    validate_config(_config)

def validate_config(config: Config) -> None:
    """
    Validates the configuration against critical project constraints.
    
    Raises:
        ConfigurationError: If critical constraints (like token_limit) are violated.
    """
    # CRITICAL: Token Limit Validation (T005 Requirement)
    # Must be exactly 100000. No defaults, no "deferred", no None.
    if config.token_limit != 100000:
        raise ConfigurationError(
            f"CRITICAL CONFIGURATION ERROR: token_limit must be exactly 100000. "
            f"Current value: {config.token_limit}. "
            f"The pipeline cannot proceed without this specific limit as per Spec FR-002."
        )
    
    # Recursion Depth Validation
    if config.recursion_depth > 2:
        raise ConfigurationError(
            f"CRITICAL CONFIGURATION ERROR: recursion_depth cannot exceed 2. "
            f"Current value: {config.recursion_depth}."
        )
    
    # Device Validation
    if config.use_cpu and not torch.cuda.is_available():
        logger.info("CUDA not available, forcing CPU mode.")
        config.use_cpu = True
    elif config.use_cpu and torch.cuda.is_available():
        logger.warning("CUDA is available but use_cpu is forced to True.")

def main() -> None:
    """
    Entry point for testing configuration validation.
    """
    try:
        cfg = get_config()
        logger.info(f"Configuration loaded successfully. Token limit: {cfg.token_limit}")
        logger.info(f"Recursion depth: {cfg.recursion_depth}")
        logger.info(f"Seed: {cfg.seed}")
    except ConfigurationError as e:
        logger.critical(str(e))
        raise

if __name__ == "__main__":
    main()
