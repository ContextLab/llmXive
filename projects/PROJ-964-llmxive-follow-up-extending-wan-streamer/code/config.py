"""
code/config.py - Global configuration for the project.

This file is updated by validate_logs.py (T009) to point to the fetched dataset.
"""
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Dataset Path - Updated by validate_logs.py
DATASET_PATH = None # Will be set by validate_logs.py

# Configuration Summary
def get_config_summary() -> dict:
    """
    Returns a summary of the current configuration.

    Returns:
        Dictionary with configuration details.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "dataset_path": str(DATASET_PATH) if DATASET_PATH else "Not set",
        "seed": 42,
    }

if __name__ == "__main__":
    print(get_config_summary())