import random
import os
import sys
from typing import Optional
import numpy as np
import argparse

_seed_initialized = False
_current_seed = None

def setup_logger_module(name: str):
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger_module(__name__)

def init_seed(seed: Optional[int] = None) -> int:
    """
    Initialize random seeds for reproducibility.
    If seed is None, generates a random one.
    Sets environment variable for other modules to detect.
    """
    global _seed_initialized, _current_seed
    
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    _current_seed = seed
    _seed_initialized = True
    
    random.seed(seed)
    np.random.seed(seed)
    
    os.environ["SEED_INITIALIZED"] = "true"
    os.environ["RANDOM_SEED"] = str(seed)
    
    logger.info(f"Seed initialized with value: {seed}")
    return seed

def get_seed() -> Optional[int]:
    """Return the current seed if initialized."""
    return _current_seed

def is_seed_initialized() -> bool:
    """Check if seed has been initialized."""
    return _seed_initialized

def add_seed_argument(parser: Optional[argparse.ArgumentParser] = None) -> Optional[argparse.ArgumentParser]:
    """
    Adds the --seed argument to an argparse parser.
    If parser is None, creates a new one and returns it.
    """
    if parser is None:
        parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--seed', 
        type=int, 
        default=None, 
        help='Random seed for reproducibility. If not provided, a random seed is generated.'
    )
    return parser
