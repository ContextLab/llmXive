"""
config.py

Global configuration module for the llmXive Orca follow-up project.
Contains paths, seeds, memory limits, and other hyperparameters.
"""

import os
from pathlib import Path
from typing import Optional

# Project root
_project_root = Path(__file__).resolve().parent.parent

# Paths
DATA_DIR = _project_root / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VALIDATION_DIR = DATA_DIR / "validation"
LOGS_DIR = _project_root / "logs"
FIGURES_DIR = _project_root / "figures"

# Hyperparameters
SEED = 42
OPTICAL_FLOW_THRESHOLD = 0.5
MAX_MEMORY_GB = 16
MEMORY_WARNING_THRESHOLD = 80
MEMORY_CRITICAL_THRESHOLD = 90

# Model settings
MODEL_NAME = "microsoft/Orca-1.3B"
LATENT_DIM = 1024
MAX_BATCH_SIZE = 16

# Ensure directories exist
def ensure_directories():
    """Creates necessary directories if they don't exist."""
    for dir_path in [RAW_DIR, PROCESSED_DIR, VALIDATION_DIR, LOGS_DIR, FIGURES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Helper to get config as a dict
def get_config() -> dict:
    """Returns a dictionary of configuration values."""
    return {
        "DATA_DIR": str(DATA_DIR),
        "RAW_DIR": str(RAW_DIR),
        "PROCESSED_DIR": str(PROCESSED_DIR),
        "VALIDATION_DIR": str(VALIDATION_DIR),
        "LOGS_DIR": str(LOGS_DIR),
        "FIGURES_DIR": str(FIGURES_DIR),
        "SEED": SEED,
        "OPTICAL_FLOW_THRESHOLD": OPTICAL_FLOW_THRESHOLD,
        "MAX_MEMORY_GB": MAX_MEMORY_GB,
        "MEMORY_WARNING_THRESHOLD": MEMORY_WARNING_THRESHOLD,
        "MEMORY_CRITICAL_THRESHOLD": MEMORY_CRITICAL_THRESHOLD,
        "MODEL_NAME": MODEL_NAME,
        "LATENT_DIM": LATENT_DIM,
        "MAX_BATCH_SIZE": MAX_BATCH_SIZE,
    }
