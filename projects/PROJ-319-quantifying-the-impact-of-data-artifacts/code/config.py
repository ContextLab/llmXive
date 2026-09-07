"""
Configuration module for the project.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the code is in `code/` directory relative to the root.
    """
    # If running as a script, __file__ is relative to the script location.
    # We assume the script is in code/config.py
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration."""
    root = get_project_root()
    return {
        "project_root": str(root),
        "saturation_range": (0.0, 0.5, 0.05),
        "noise_levels": [0.01, 0.05, 0.10],
        "default_n_images": 50,
        "random_seed": 42
    }

# Constants
SATURATION_MIN = 0.0
SATURATION_MAX = 0.5
SATURATION_STEP = 0.05
NOISE_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_IMAGES = 50
RANDOM_SEED = 42