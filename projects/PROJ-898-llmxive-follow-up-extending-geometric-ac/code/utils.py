"""
Utility functions for the llmXive project.
"""
import hashlib
import logging
import os
import random
from typing import Optional, Union

import numpy as np
import torch

logger = logging.getLogger("llmxive")


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def set_deterministic_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across numpy, torch, and python.

    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # For deterministic behavior in torch
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def compute_sha256(data: Union[str, bytes]) -> str:
    """
    Compute the SHA-256 hash of the given data.

    Args:
        data: String or bytes to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()
