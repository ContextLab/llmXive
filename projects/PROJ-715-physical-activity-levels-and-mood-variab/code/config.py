"""
Configuration module for the Physical Activity and Mood Variability project.

This module defines paths, random seeds, constants, and dataset identifiers.
"""

import os
import random
from pathlib import Path

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random seed for reproducibility
RANDOM_SEED = 42

# Missingness threshold for derived features
MISSINGNESS_THRESHOLD = 0.2

# StudentLife Dataset Configuration
# DOI: 10.17605/OSF.IO/4GJ7K
STUDENTLIFE_DOI = "10.17605/OSF.IO/4GJ7K"
# SHA256 checksum of the StudentLife.zip file (to be verified and updated if necessary)
# This is a placeholder; the actual checksum must be obtained from the source.
# For the purpose of this task, we will leave it as None or a placeholder.
# In a real scenario, you would calculate the checksum of the downloaded file and hardcode it.
STUDENTLIFE_EXPECTED_SHA256 = None  # Replace with actual checksum once verified

def get_path(key: str) -> Path:
    """
    Returns the absolute path for a given key.

    Args:
        key (str): The key for the path (e.g., 'data/raw', 'data/processed', 'code').

    Returns:
        Path: The absolute path.
    """
    path_mapping = {
        "data/raw": _PROJECT_ROOT / "data" / "raw",
        "data/processed": _PROJECT_ROOT / "data" / "processed",
        "data/interim": _PROJECT_ROOT / "data" / "interim",
        "code": _PROJECT_ROOT / "code",
        "tests": _PROJECT_ROOT / "tests",
        "specs": _PROJECT_ROOT / "specs",
    }
    
    if key not in path_mapping:
        raise ValueError(f"Unknown path key: {key}")
    
    return path_mapping[key]

# Set random seeds
random.seed(RANDOM_SEED)
os.environ['PYTHONHASHSEED'] = str(RANDOM_SEED)
