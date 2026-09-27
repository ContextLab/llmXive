"""
Configuration module for the llmXive project.
Defines project paths, random seeds, and artifact parameters.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Project Root
def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    # Try to find the project root by looking for 'data/' and 'code/' siblings
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / 'data').is_dir() and (current / 'code').is_dir():
            return current
        current = current.parent
    # Fallback: assume current working directory if structure not found
    return Path.cwd()

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a dictionary summarizing the current configuration.
    """
    root = get_project_root()
    return {
        "project_root": str(root),
        "data_dir": str(root / "data"),
        "code_dir": str(root / "code"),
        "logs_dir": str(root / "logs"),
        "random_seed": 42,
        "noise_levels": [0.01, 0.05, 0.10],
        "saturation_range": {"start": 0.0, "end": 0.5, "step": 0.05},
        "default_n_images": 50
    }

# Constants
RANDOM_SEED = 42
NOISE_LEVELS = [0.01, 0.05, 0.10]
SATURATION_START = 0.0
SATURATION_END = 0.5
SATURATION_STEP = 0.05
DEFAULT_N_IMAGES = 50
