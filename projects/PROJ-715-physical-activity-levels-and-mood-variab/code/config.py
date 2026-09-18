import os
import sys
import logging
import random
from pathlib import Path
from typing import Union, List, Tuple
import yaml
import shutil

# Configuration Constants
SEED = 42
MISSINGNESS_THRESHOLD = 0.2
BOOTSTRAP_ITERATIONS = 1000
OSF_DOI = "10.17605/OSF.IO/5B1A9"

def set_random_seed(seed: int = SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds are set in their respective modules

def get_path(*parts: Union[str, Path]) -> str:
    """
    Construct a path relative to the project root.
    Handles variable number of arguments and list/tuple inputs.
    """
    # Determine project root. Assuming this file is in code/config.py
    # Root is two levels up.
    current_file = Path(__file__).resolve()
    root = current_file.parent.parent
    
    path_parts = []
    for p in parts:
        if isinstance(p, (list, tuple)):
            path_parts.extend(p)
        else:
            path_parts.append(str(p))
    
    full_path = root / Path(*path_parts)
    return str(full_path)

def init_logger(name: str):
    """Initialize a logger with standard formatting."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

def ensure_dirs(*paths: str):
    """Ensure directories exist."""
    for p in paths:
        os.makedirs(p, exist_ok=True)

def update_state_artifact_hash(state_path: str, key: str, value: str):
    """
    Update the state YAML file with a new artifact hash.
    Reads the file, updates the specific key under artifact_hashes, and writes back atomically.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    
    # Read existing state
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes'][key] = value
    
    # Atomic write
    temp_path = state_path + '.tmp'
    with open(temp_path, 'w') as f:
        yaml.dump(state, f)
    
    shutil.move(temp_path, state_path)
    logging.getLogger(__name__).info(f"Updated state hash for {key}")
