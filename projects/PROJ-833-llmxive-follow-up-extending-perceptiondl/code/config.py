"""
code/config.py

Configuration module defining paths, random seeds, and hyperparameters.
"""

import os
import random
from pathlib import Path
from typing import List, Dict, Any

# Project Root
# Assuming the script is run from the project root or code directory
# We calculate relative to this file
_PROJECT_ROOT = Path(__file__).parent.parent
_DATA_ROOT = _PROJECT_ROOT / "data"
_STATE_ROOT = _PROJECT_ROOT / "state"
_CODE_ROOT = _PROJECT_ROOT / "code"

# Region Counts
REGION_COUNTS: List[int] = [25, 30, 35, 40, 45, 50]

# Random Seed
RANDOM_SEED: int = 42

# Thresholds
TIPPING_POINT_THRESHOLD: float = 0.9

def get_data_path() -> Path:
    """Return the data root path."""
    return _DATA_ROOT

def get_state_path() -> Path:
    """Return the state root path."""
    return _STATE_ROOT

def get_random_state() -> int:
    """Return the configured random seed."""
    return RANDOM_SEED

def ensure_directories(paths: List[Path]):
    """Ensure all given paths exist as directories."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def main():
    """Test config."""
    print(f"Data root: {get_data_path()}")
    print(f"Random seed: {get_random_state()}")

if __name__ == "__main__":
    main()
