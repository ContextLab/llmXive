import logging
import os
import sys
import hashlib
import json
from datetime import datetime

def get_logger(name):
    """Returns a logger with the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def log_structured_error(logger, error_type, message, details=None):
    """Logs a structured error message."""
    log_data = {"error_type": error_type, "message": message}
    if details:
        log_data["details"] = details
    logger.error(json.dumps(log_data))

def compute_file_checksum(filepath):
    """Computes the SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def init_seed_config(seed):
    """Initializes the random seed configuration."""
    os.environ['PYTHONRANDOMSEED'] = str(seed)

def set_random_seed(seed):
    """Sets the global random seed for reproducibility."""
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)

def get_global_seed():
    """Returns the global random seed from the environment."""
    try:
        return int(os.environ['PYTHONRANDOMSEED'])
    except (KeyError, ValueError):
        return None