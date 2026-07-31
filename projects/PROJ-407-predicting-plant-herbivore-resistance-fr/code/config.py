"""
Configuration constants for the plant herbivore resistance prediction pipeline.

This module defines global constants used throughout the project for reproducibility,
resource constraints, and data paths.
"""

import os

# Reproducibility
RANDOM_SEED = 42

# Data paths (relative to project root)
DATA_ROOT = 'data'

# Statistical validation parameters
N_PERMUTATIONS = 1000

# Resource constraints (FR-009)
MAX_RUNTIME_HOURS = 6
MAX_MEMORY_GB = 7

# Derived paths
RAW_DATA_DIR = os.path.join(DATA_ROOT, 'raw')
INTERIM_DATA_DIR = os.path.join(DATA_ROOT, 'interim')
PROCESSED_DATA_DIR = os.path.join(DATA_ROOT, 'processed')
RESULTS_DIR = os.path.join(DATA_ROOT, 'results')

# Ensure directories exist (lazy initialization)
def ensure_directories():
    """Create data directories if they don't exist."""
    for directory in [RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR]:
        os.makedirs(directory, exist_ok=True)