from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Config:
    """Configuration container for the project."""
    seed: int = 42
    data_dir: str = "data"
    code_dir: str = "code"
    output_dir: str = "data/output"
    model_dir: str = "data/model"
    log_level: int = logging.INFO
    # Add other config parameters as needed

def get_seed() -> int:
    """Get the random seed from environment or default."""
    seed_str = os.getenv("RANDOM_SEED", "42")
    try:
        return int(seed_str)
    except ValueError:
        return 42


def set_random_seed(seed: Optional[int] = None) -> None:
    """Set random seed for reproducibility across libraries."""
    if seed is None:
        seed = get_seed()

    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set seed
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


# Import logging here to avoid circular dependency if Config uses it,
# though Config uses int for log_level.
import logging
