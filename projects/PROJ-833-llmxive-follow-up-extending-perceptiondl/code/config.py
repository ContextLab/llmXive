"""
Configuration module for the llmXive project.

Defines paths, random seeds, hyperparameters, and utility functions
for project setup and execution.
"""
import os
from pathlib import Path

# Project root directory (assumed to be the parent of this file's directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Random seeds for reproducibility
RANDOM_SEED = 42

# Hyperparameters for region counts (used in synthetic generation)
REGION_COUNTS = [20, 25, 30, 35, 40, 45, 50]

# Model configuration
MODEL_NAME = "PerceptionDLM"  # Supersedes Spec FR-003's LLaVA requirement per Plan Summary
MODEL_PRECISION = "FP16"  # Default precision for model loading

# Analysis configuration
BONFERRONI_ALPHA = 0.05
TIPPING_POINT_THRESHOLD = 0.95  # Configurable threshold for tipping point detection

def ensure_directories():
    """
    Creates the required data directory structure if it doesn't exist.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    try:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directories: {e}")
        return False

def get_data_path(subdir: str, filename: str) -> Path:
    """
    Constructs a full path to a file within the data directory structure.
    
    Args:
        subdir (str): The subdirectory ('raw', 'synthetic', or 'processed').
        filename (str): The name of the file.
        
    Returns:
        Path: The full path to the file.
        
    Raises:
        ValueError: If an invalid subdirectory is provided.
    """
    if subdir == "raw":
        return RAW_DATA_DIR / filename
    elif subdir == "synthetic":
        return SYNTHETIC_DATA_DIR / filename
    elif subdir == "processed":
        return PROCESSED_DATA_DIR / filename
    else:
        raise ValueError(f"Invalid subdirectory: {subdir}. Must be 'raw', 'synthetic', or 'processed'.")
