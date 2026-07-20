"""
Environment configuration management for llmXive.

Provides a centralized Config dataclass and management functions
for project-wide settings including CPU-only mode, epsilon floor,
and random seed management.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os
import logging
import random
import numpy as np

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """
    Central configuration dataclass for the llmXive project.
    
    Attributes:
        CPU_ONLY (bool): If True, force all operations to CPU. Default: True.
        EPSILON_FLOOR (float): Minimum value for numerical stability. Default: 1e-6.
        RANDOM_SEED (int): Global random seed for reproducibility. Default: 42.
        DATA_DIR (str): Path to the data directory. Default: 'data'.
        CODE_DIR (str): Path to the code directory. Default: 'code'.
        LOG_LEVEL (str): Logging level. Default: 'INFO'.
        BATCH_SIZE (int): Default batch size for simulations. Default: 32.
        NUM_STEPS (int): Default number of steps in simulation. Default: 1000.
        SINKHORN_MAX_ITER (int): Maximum iterations for Sinkhorn solver. Default: 100.
        SINKHORN_TOL (float): Convergence tolerance for Sinkhorn solver. Default: 1e-5.
    """
    CPU_ONLY: bool = True
    EPSILON_FLOOR: float = 1e-6
    RANDOM_SEED: int = 42
    DATA_DIR: str = "data"
    CODE_DIR: str = "code"
    LOG_LEVEL: str = "INFO"
    BATCH_SIZE: int = 32
    NUM_STEPS: int = 1000
    SINKHORN_MAX_ITER: int = 100
    SINKHORN_TOL: float = 1e-5
    
    # Additional configuration for drift models
    DRIFT_TYPE: str = "sinusoidal"  # Options: "linear", "exponential", "sinusoidal"
    DRIFT_AMPLITUDE: float = 0.1
    DRIFT_FREQUENCY: float = 0.5
    
    # Simulation specific
    KL_THRESHOLD: float = 1.0  # Threshold for accumulated KL divergence
    LATENCY_BUDGET_MS: float = 50.0  # Maximum latency per token in milliseconds

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.EPSILON_FLOOR <= 0:
            raise ValueError(f"EPSILON_FLOOR must be positive, got {self.EPSILON_FLOOR}")
        
        if self.RANDOM_SEED < 0:
            raise ValueError(f"RANDOM_SEED must be non-negative, got {self.RANDOM_SEED}")
        
        if self.DRIFT_TYPE not in ["linear", "exponential", "sinusoidal"]:
            raise ValueError(f"DRIFT_TYPE must be 'linear', 'exponential', or 'sinusoidal', got {self.DRIFT_TYPE}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary representation."""
        return {
            "CPU_ONLY": self.CPU_ONLY,
            "EPSILON_FLOOR": self.EPSILON_FLOOR,
            "RANDOM_SEED": self.RANDOM_SEED,
            "DATA_DIR": self.DATA_DIR,
            "CODE_DIR": self.CODE_DIR,
            "LOG_LEVEL": self.LOG_LEVEL,
            "BATCH_SIZE": self.BATCH_SIZE,
            "NUM_STEPS": self.NUM_STEPS,
            "SINKHORN_MAX_ITER": self.SINKHORN_MAX_ITER,
            "SINKHORN_TOL": self.SINKHORN_TOL,
            "DRIFT_TYPE": self.DRIFT_TYPE,
            "DRIFT_AMPLITUDE": self.DRIFT_AMPLITUDE,
            "DRIFT_FREQUENCY": self.DRIFT_FREQUENCY,
            "KL_THRESHOLD": self.KL_THRESHOLD,
            "LATENCY_BUDGET_MS": self.LATENCY_BUDGET_MS,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config instance from dictionary."""
        return cls(
            CPU_ONLY=data.get("CPU_ONLY", True),
            EPSILON_FLOOR=data.get("EPSILON_FLOOR", 1e-6),
            RANDOM_SEED=data.get("RANDOM_SEED", 42),
            DATA_DIR=data.get("DATA_DIR", "data"),
            CODE_DIR=data.get("CODE_DIR", "code"),
            LOG_LEVEL=data.get("LOG_LEVEL", "INFO"),
            BATCH_SIZE=data.get("BATCH_SIZE", 32),
            NUM_STEPS=data.get("NUM_STEPS", 1000),
            SINKHORN_MAX_ITER=data.get("SINKHORN_MAX_ITER", 100),
            SINKHORN_TOL=data.get("SINKHORN_TOL", 1e-5),
            DRIFT_TYPE=data.get("DRIFT_TYPE", "sinusoidal"),
            DRIFT_AMPLITUDE=data.get("DRIFT_AMPLITUDE", 0.1),
            DRIFT_FREQUENCY=data.get("DRIFT_FREQUENCY", 0.5),
            KL_THRESHOLD=data.get("KL_THRESHOLD", 1.0),
            LATENCY_BUDGET_MS=data.get("LATENCY_BUDGET_MS", 50.0),
        )

    def apply_seed(self) -> None:
        """Apply the random seed to all relevant libraries."""
        logger.info(f"Applying random seed: {self.RANDOM_SEED}")
        random.seed(self.RANDOM_SEED)
        np.random.seed(self.RANDOM_SEED)
        # Torch is optional as it may not be installed
        try:
            import torch
            torch.manual_seed(self.RANDOM_SEED)
            if self.CPU_ONLY:
                torch.set_num_threads(1)
        except ImportError:
            logger.debug("PyTorch not available, skipping torch seed setting")

# Global config instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global config instance.
    
    Returns:
        Config: The global configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        logger.info("Created new global Config instance with default values")
    return _config_instance

def set_config(config: Optional[Config] = None, **kwargs) -> Config:
    """
    Set or update the global config instance.
    
    Args:
        config: Optional Config instance to set. If None, updates existing config with kwargs.
        **kwargs: Configuration parameters to update.
    
    Returns:
        Config: The updated global configuration instance.
    """
    global _config_instance
    
    if config is not None:
        _config_instance = config
        logger.info("Global Config instance updated with provided Config object")
    elif _config_instance is not None:
        # Update existing config with kwargs
        for key, value in kwargs.items():
            if hasattr(_config_instance, key):
                setattr(_config_instance, key, value)
                logger.info(f"Updated config.{key} = {value}")
            else:
                logger.warning(f"Config has no attribute '{key}', skipping")
    else:
        # Create new config with kwargs
        _config_instance = Config(**kwargs)
        logger.info(f"Created new global Config instance with kwargs: {kwargs}")
    
    # Apply seed if RANDOM_SEED was set
    if "RANDOM_SEED" in kwargs or config is not None:
        _config_instance.apply_seed()
    
    return _config_instance

def reset_config() -> None:
    """Reset the global config instance to defaults."""
    global _config_instance
    _config_instance = Config()
    logger.info("Global Config instance reset to defaults")

def load_config_from_env() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Config: Configuration instance with values from environment variables.
    """
    env_config = {}
    
    # Map environment variables to config attributes
    env_mappings = {
        "LLMXIVE_CPU_ONLY": "CPU_ONLY",
        "LLMXIVE_EPSILON_FLOOR": "EPSILON_FLOOR",
        "LLMXIVE_RANDOM_SEED": "RANDOM_SEED",
        "LLMXIVE_DATA_DIR": "DATA_DIR",
        "LLMXIVE_CODE_DIR": "CODE_DIR",
        "LLMXIVE_LOG_LEVEL": "LOG_LEVEL",
        "LLMXIVE_BATCH_SIZE": "BATCH_SIZE",
        "LLMXIVE_NUM_STEPS": "NUM_STEPS",
        "LLMXIVE_SINKHORN_MAX_ITER": "SINKHORN_MAX_ITER",
        "LLMXIVE_SINKHORN_TOL": "SINKHORN_TOL",
        "LLMXIVE_DRIFT_TYPE": "DRIFT_TYPE",
        "LLMXIVE_DRIFT_AMPLITUDE": "DRIFT_AMPLITUDE",
        "LLMXIVE_DRIFT_FREQUENCY": "DRIFT_FREQUENCY",
        "LLMXIVE_KL_THRESHOLD": "KL_THRESHOLD",
        "LLMXIVE_LATENCY_BUDGET_MS": "LATENCY_BUDGET_MS",
    }
    
    for env_key, config_key in env_mappings.items():
        value = os.getenv(env_key)
        if value is not None:
            # Type conversion based on attribute
            attr = getattr(Config, config_key)
            if isinstance(attr, bool):
                env_config[config_key] = value.lower() in ("true", "1", "yes")
            elif isinstance(attr, int):
                env_config[config_key] = int(value)
            elif isinstance(attr, float):
                env_config[config_key] = float(value)
            else:
                env_config[config_key] = value
            logger.debug(f"Loaded {config_key} from environment: {env_config[config_key]}")
    
    if env_config:
        logger.info(f"Loaded {len(env_config)} config values from environment")
        return Config(**env_config)
    else:
        logger.info("No environment variables found, using defaults")
        return Config()

if __name__ == "__main__":
    # Verification script for T009
    logger.info("=== Verifying T009: Config defaults ===")
    
    # Test 1: Load config and assert defaults
    config = get_config()
    assert config.CPU_ONLY is True, f"CPU_ONLY should be True, got {config.CPU_ONLY}"
    assert config.EPSILON_FLOOR == 1e-6, f"EPSILON_FLOOR should be 1e-6, got {config.EPSILON_FLOOR}"
    assert config.RANDOM_SEED == 42, f"RANDOM_SEED should be 42, got {config.RANDOM_SEED}"
    
    print("✓ All default values verified successfully")
    print(f"  CPU_ONLY: {config.CPU_ONLY}")
    print(f"  EPSILON_FLOOR: {config.EPSILON_FLOOR}")
    print(f"  RANDOM_SEED: {config.RANDOM_SEED}")
    
    # Test 2: Update config
    new_config = set_config(RANDOM_SEED=123, EPSILON_FLOOR=1e-8)
    assert new_config.RANDOM_SEED == 123, "RANDOM_SEED should be updated to 123"
    assert new_config.EPSILON_FLOOR == 1e-8, "EPSILON_FLOOR should be updated to 1e-8"
    
    print("✓ Config update verified successfully")
    
    # Test 3: Reset config
    reset_config()
    reset_config = get_config()
    assert reset_config.RANDOM_SEED == 42, "Config should be reset to default RANDOM_SEED"
    assert reset_config.EPSILON_FLOOR == 1e-6, "Config should be reset to default EPSILON_FLOOR"
    
    print("✓ Config reset verified successfully")
    
    # Test 4: Load from environment (if available)
    env_config = load_config_from_env()
    print(f"✓ Environment config loaded: {env_config.to_dict()}")
    
    print("\n=== T009 Verification Complete ===")