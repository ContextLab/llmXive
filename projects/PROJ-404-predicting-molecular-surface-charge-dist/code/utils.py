"""
Utility functions for seed setting and logging.
Backward compatibility shim if utils/utils.py is not found or if imported directly.
"""
import random
import logging
from typing import Optional
import numpy as np
import torch
import sys

def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across random, numpy, and torch.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger