"""
Deterministic random seed pinning utility.
"""
import random
import os
import numpy as np
import torch
import logging
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)

def pin_seed(seed: int):
    """
    Pin random seeds for reproducibility.

    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

def get_seed_from_env() -> int:
    """
    Get seed from environment variable.

    Returns:
        Seed value or default.
    """
    return int(os.environ.get('SEED', 42))

def ensure_deterministic():
    """
    Ensure deterministic behavior across runs.
    """
    logger.info("Ensuring deterministic behavior")
    # Placeholder for additional deterministic settings
