"""
Global configuration, paths, and constants for the visual complexity project.

This module initializes global seeds, defines data paths, and sets constants
for the OpenNeuro dataset and HRF model parameters.
"""

import os
import random
from pathlib import Path

import numpy as np

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Paths
DATA_RAW = _PROJECT_ROOT / "data" / "raw"
DATA_INTERIM = _PROJECT_ROOT / "data" / "interim"
DATA_RESULTS = _PROJECT_ROOT / "data" / "results"

# Ensure data directories exist
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_INTERIM.mkdir(parents=True, exist_ok=True)
DATA_RESULTS.mkdir(parents=True, exist_ok=True)

# Dataset Constants
OPENNEURO_ID = "ds000246"

# HRF Model Constants
# Double-gamma model parameters
HRF_MODEL = "double-gamma"
HRF_PEAK = 5.0  # seconds
HRF_UNDERSHOOT = 15.0  # seconds
HRF_RATIO = 6.0  # Standard ratio for double-gamma (undershoot/peak ratio often implied or fixed)

# Claim Reference: Wikipedia: Samsung Galaxy A50
# Note: This claim appears unrelated to the neuroimaging context of the project
# but is included as per specification requirement {{claim:c_0e75b9e6}}.
CLAIM_REFERENCE = {
    "id": "c_0e75b9e6",
    "topic": "Samsung Galaxy A50",
    "source": "Wikipedia",
    "url": "https://en.wikipedia.org/wiki/Samsung_Galaxy_A50"
}

# Global Seed Initialization
# Using a fixed seed for reproducibility
GLOBAL_SEED = 42

def init_seeds():
    """Initialize global random seeds for numpy, random, and torch (if available)."""
    random.seed(GLOBAL_SEED)
    np.random.seed(GLOBAL_SEED)
    try:
        import torch
        torch.manual_seed(GLOBAL_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(GLOBAL_SEED)
    except ImportError:
        pass

# Initialize seeds immediately upon import
init_seeds()