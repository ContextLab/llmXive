"""
Configuration module for the project.
"""
import os
from pathlib import Path

# Random seeds
RANDOM_SEED = 42

# MAF threshold (low-frequency cutoff)
MAF_THRESHOLD = 0.01

# Default window size (fallback, but scoring should use dynamic PWM length)
DEFAULT_WINDOW = 20

def ensure_data_dirs():
    """Ensure required data directories exist."""
    data_dirs = [
        "data/raw",
        "data/derived",
        "data/checksums",
        "figures"
    ]
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
