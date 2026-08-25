import os
import sys
import logging
import random
from pathlib import Path
from typing import Union, List, Tuple
import yaml

# Constants
SEED = 42
MISSINGNESS_THRESHOLD = 0.2
BOOTSTRAP_ITERATIONS = 1000
OSF_DOI_STRING = "10.17605/OSF.IO/XYZ" # Placeholder, to be replaced with actual DOI

# Ensure random seed
def set_random_seed(seed=SEED):
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def get_path(*parts: Union[str, Path]) -> Path:
    """
    Construct a path relative to the project root.
    Handles variable number of arguments and Path objects.
    """
    # Project root is assumed to be the parent of the 'code' directory
    # or the current working directory if run as a script in the project root.
    # We look for 'data' or 'specs' to anchor.
    current = Path.cwd()
    
    # Try to find project root by looking for 'code' directory upwards
    root = current
    while root != root.parent:
        if (root / "code").exists() and (root / "data").exists():
            break
        root = root.parent
    
    # If not found, default to current
    if root == current and not (root / "code").exists():
        root = current

    path_parts = [str(p) for p in parts]
    full_path = root / os.path.join(*path_parts)
    return full_path

def init_logger(name: str = "llmXive") -> logging.Logger:
    """Initialize a logger with stdout and file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        get_path("data", "raw"),
        get_path("data", "processed"),
        get_path("data", "interim"),
        get_path("specs", "001-physical-activity-levels-and-mood-variab", "contracts"),
        get_path("state", "projects")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def update_state_artifact_hash(state_path: str, key: str, value: str):
    """
    Update the state YAML file with a new artifact hash.
    Handles nested keys like 'artifact_hashes.data_raw_bronze'.
    """
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    # Navigate to the nested key
    keys = key.split('.')
    current = state
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)