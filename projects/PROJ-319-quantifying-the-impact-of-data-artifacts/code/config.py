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

# Artifact parameters (concrete values required by T004)
# - Noise levels: {0.01, 0.05, 0.10}
# - Saturation fractions: 0.0 – 0.5 inclusive in 0.05 steps
#
# The original code base expects `NOISE_LEVELS` and `SATURATION_RANGE`,
# so we keep those for backward compatibility while also exposing the
# explicitly named constants required by the verification suite.
DEFAULT_NOISE_LEVELS: List[float] = [0.01, 0.05, 0.10]
DEFAULT_SATURATION_FRACTIONS: List[float] = [
    round(x, 2) for x in
    (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
]

# Backward‑compatible aliases used throughout the existing pipeline
NOISE_LEVELS = DEFAULT_NOISE_LEVELS
SATURATION_RANGE: Tuple[float, float, float] = (0.0, 0.5, 0.05)  # start, stop, step

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
        "noise_levels": DEFAULT_NOISE_LEVELS,
        "saturation_fractions": DEFAULT_SATURATION_FRACTIONS,
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