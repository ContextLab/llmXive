"""
Configuration management for the project.
Handles random seeds, runtime limits, and CPU constraints.
"""
import os
import random
from typing import Optional, Union

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_TIMEOUT_SECONDS = 300
CPU_ONLY_DEFAULT = True

class Config:
    """Global configuration holder."""
    seed: int = DEFAULT_SEED
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    cpu_only: bool = CPU_ONLY_DEFAULT

    @classmethod
    def set_seed(cls, seed: int):
        cls.seed = seed
        random.seed(seed)
        # If numpy is available, set its seed too
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass

    @classmethod
    def get_seed(cls) -> int:
        return cls.seed

    @classmethod
    def get_timeout_seconds(cls) -> int:
        return cls.timeout_seconds

    @classmethod
    def is_cpu_only(cls) -> bool:
        return cls.cpu_only

    @classmethod
    def enforce_cpu_only(cls, force: bool = True):
        cls.cpu_only = force

# Initialize default seed
Config.set_seed(DEFAULT_SEED)

def get_seed() -> int:
    return Config.get_seed()

def set_seed(seed: int):
    Config.set_seed(seed)

def get_timeout_seconds() -> int:
    return Config.get_timeout_seconds()

def is_cpu_only() -> bool:
    return Config.is_cpu_only()

def enforce_cpu_only(force: bool = True):
    Config.enforce_cpu_only(force)