"""
Configuration module for the project.
Defines paths, random seeds, constants, and dataset identifiers.
"""
import os
import random
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Constants
MISSINGNESS_THRESHOLD = 0.2  # Threshold for missing data handling

# Dataset configuration
# The specific OSF DOI for the StudentLife dataset
DATASET_OSF_DOI = "10.17605/OSF.IO/6Z5X9"

def get_path(directory: str) -> Path:
    """
    Get the absolute path to a directory relative to the project root.
    
    Args:
        directory (str): The name of the directory (e.g., 'raw', 'processed', 'code').
    
    Returns:
        Path: The absolute path to the directory.
    """
    valid_dirs = ['raw', 'processed', 'interim', 'code', 'tests', 'specs', 'figures']
    if directory not in valid_dirs:
        # Allow any subdirectory under 'data' or specific top-level dirs
        if directory.startswith('data/'):
            return PROJECT_ROOT / directory
        # Fallback for top-level dirs
        return PROJECT_ROOT / directory
    
    return PROJECT_ROOT / directory