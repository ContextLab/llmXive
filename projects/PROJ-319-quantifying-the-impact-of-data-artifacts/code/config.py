"""
Project configuration, paths, and constants.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Random seeds for reproducibility
RANDOM_SEED = 42
NPY_SEED = 42

# Default paths relative to project root
DEFAULT_DATA_DIR = "data"
DEFAULT_CODE_DIR = "code"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_TESTS_DIR = "tests"
DEFAULT_DOCS_DIR = "docs"

# Artifact parameters (derived from T037a decision)
NOISE_LEVELS = [0.01, 0.05, 0.10]
SATURATION_RANGE = (0.0, 0.5, 0.05)  # start, stop, step

# Synthetic generation defaults
DEFAULT_N_IMAGES = 50
DEFAULT_FWHM = 2.0  # pixels

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    # Try to find the root by looking for a known file or directory
    # We assume the project root contains 'tasks.md' or 'requirements.txt'
    current = Path.cwd()
    while current != current.parent:
        if (current / "tasks.md").exists() or (current / "requirements.txt").exists():
            return current
        current = current.parent
    
    # Fallback: assume current directory is root if no marker found
    return Path.cwd()

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration.
    """
    root = get_project_root()
    return {
        "project_root": str(root),
        "random_seed": RANDOM_SEED,
        "npy_seed": NPY_SEED,
        "noise_levels": NOISE_LEVELS,
        "saturation_range": {
            "start": SATURATION_RANGE[0],
            "stop": SATURATION_RANGE[1],
            "step": SATURATION_RANGE[2]
        },
        "default_n_images": DEFAULT_N_IMAGES,
        "default_fwhm": DEFAULT_FWHM,
        "paths": {
            "data": str(root / DEFAULT_DATA_DIR),
            "code": str(root / DEFAULT_CODE_DIR),
            "logs": str(root / DEFAULT_LOGS_DIR),
            "tests": str(root / DEFAULT_TESTS_DIR),
            "docs": str(root / DEFAULT_DOCS_DIR)
        }
    }
