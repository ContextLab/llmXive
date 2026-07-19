"""
Configuration management for the simulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal
import os
import yaml

# T065: Define Configuration Matrix
# Explicitly defines the configuration matrix as a list of dictionaries.
# Each dictionary represents a configuration block containing distribution types,
# scaling methods, and test types to be iterated over in the simulation loop.
CONFIG_MATRIX = [
    {
        "distribution_types": ["Normal", "Skewed", "Heteroscedastic"],
        "scaling_methods": ["standardization", "minmax", "robust"],
        "test_types": ["t-test", "anova", "chi-squared"]
    }
]

@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""
    config_id: str = "default"
    distribution_type: str = "normal"
    scaling_method: str = "standardization"
    test_type: str = "t-test"
    n_samples: int = 1000
    mean_diff: float = 0.0
    variance: float = 1.0
    skewness: float = 0.0
    kurtosis: float = 3.0
    seed: Optional[int] = None
    target_iterations: int = 10000

    def __post_init__(self):
        if self.seed is None:
            import random
            self.seed = random.randint(0, 2**31 - 1)

def get_default_config() -> SimulationConfig:
    """Return a default configuration."""
    return SimulationConfig()

def load_config_from_yaml(path: str) -> SimulationConfig:
    """Load configuration from a YAML file."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return SimulationConfig(**data)

def save_config_to_yaml(config: SimulationConfig, path: str):
    """Save configuration to a YAML file."""
    with open(path, 'w') as f:
        yaml.dump(dataclass_to_dict(config), f)

def dataclass_to_dict(obj):
    """Convert dataclass to dictionary."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: dataclass_to_dict(v) for k, v in vars(obj).items()}
    elif isinstance(obj, list):
        return [dataclass_to_dict(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    else:
        return obj
