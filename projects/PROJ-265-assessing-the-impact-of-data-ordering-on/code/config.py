"""
Configuration module for project settings, seeds, and path management.

Centralizes all configuration values to ensure reproducibility and consistency.
"""
import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np


# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"


# Random seeds for reproducibility
DATA_SEED = 42
BOOTSTRAP_SEED = 123
SHUFFLE_SEED = 456


def ensure_directories() -> None:
    """Create all required project directories if they don't exist."""
    directories = [
        RESULTS_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        CODE_DIR,
        TESTS_DIR
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_data_seed() -> int:
    """Get the data generation seed."""
    return DATA_SEED


def get_bootstrap_seed() -> int:
    """Get the bootstrap resampling seed."""
    return BOOTSTRAP_SEED


def get_shuffle_seed() -> int:
    """Get the shuffle operation seed."""
    return SHUFFLE_SEED


def get_project_root() -> Path:
    """Get the project root directory path."""
    return PROJECT_ROOT


def get_results_dir() -> Path:
    """Get the results directory path."""
    return RESULTS_DIR


def get_data_dir() -> Path:
    """Get the data directory path."""
    return DATA_DIR
