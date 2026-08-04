"""
Configuration manager for seed management and hyperparameters.
"""
import yaml
import os
import random
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict, replace

@dataclass
class TestSetConfig:
    """Configuration for test set separation."""
    seed: int = 42
    budget: int = 1000
    num_runs: int = 5

@dataclass
class Config:
    """Main configuration container."""
    seed: int = 42
    budget: int = 1000
    test_set: TestSetConfig = field(default_factory=TestSetConfig)
    shift_config: Optional[Dict[str, Any]] = None

def get_config(config_path: str) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Config object.
    """
    if not os.path.exists(config_path):
        # Return default config if file not found
        return Config()

    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)

    return Config(
        seed=data.get('seed', 42),
        budget=data.get('budget', 1000),
        test_set=TestSetConfig(**data.get('test_set', {})),
        shift_config=data.get('shift_config')
    )

def set_seed(seed: int):
    """
    Set random seeds for reproducibility.

    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    np.random.seed(seed)

def validate_config(config: Config) -> bool:
    """
    Validate the configuration.

    Args:
        config: Configuration to validate.

    Returns:
        True if valid, False otherwise.
    """
    return config.budget > 0 and config.seed >= 0
