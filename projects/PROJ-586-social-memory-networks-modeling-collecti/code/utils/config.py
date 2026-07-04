"""Environment configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    seed: int = 42
    device: str = "cpu"
    log_level: str = "INFO"
    output_dir: str = "results"


# Global configuration instance
config = Config()


def set_seed(seed: int):
    """Sets the global random seed."""
    import random
    import numpy as np
    config.seed = seed
    random.seed(seed)
    np.random.seed(seed)


def get_config() -> Config:
    """Returns the global configuration."""
    return config
