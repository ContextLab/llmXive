import os
import random
from pathlib import Path
import numpy as np

# Global seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Dataset ID
DATASET_ID = "ds000246"

# HRF Model Parameters (Friston et al., 1998)
HRF_MODEL = "double-gamma"
HRF_PEAK = 5.0  # seconds
HRF_UNDERSHOOT = 15.0  # seconds

def init_seeds():
    """Initialize random seeds for reproducibility."""
    random.seed(SEED)
    np.random.seed(SEED)

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
