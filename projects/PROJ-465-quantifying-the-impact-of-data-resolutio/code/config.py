"""
Configuration Module.

Handles environment configuration and directory setup.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import os
from pathlib import Path
from typing import Optional

# Define project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
DERIVED_DATA_DIR = DATA_DIR / 'derived'
RESULTS_DIR = PROJECT_ROOT / 'results'
POSTERIORS_DIR = RESULTS_DIR / 'posteriors'
METRICS_DIR = RESULTS_DIR / 'metrics'

def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    """
    dirs = [
        DATA_DIR, RAW_DATA_DIR, DERIVED_DATA_DIR,
        RESULTS_DIR, POSTERIORS_DIR, METRICS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()
