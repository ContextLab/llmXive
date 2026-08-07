"""
General utility functions for the pipeline.
"""
import logging
import os
import random
import sys
from typing import Dict, Optional
import numpy as np

def fix_seed(seed: int = 42) -> None:
    """
    Fix random seeds for reproducibility across libraries.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: PyTorch seed setting requires torch import, handled in specific modules if needed.

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a standard logger for the pipeline.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
