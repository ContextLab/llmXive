import functools
import logging
import os
import sys
import time
import tracemalloc

def set_seed(seed):
    """Sets the random seed for reproducibility."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    import random
    random.seed(seed)
    import numpy as np
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    logging.info(f"Random seed set to {seed}")

def setup_logging(log_file="log.txt"):
    """Sets up basic logging to a file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )

def profile_memory(func):
    """Decorator to profile memory usage of a function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        try:
            result = func(*args, **kwargs)
        finally:
            current, peak = tracemalloc.get_traced_memory()
            logging.info(f"Memory usage: Current {current / 10**6:.2f} MB, Peak {peak / 10**6:.2f} MB")
            tracemalloc.stop()
        return result

    return wrapper
