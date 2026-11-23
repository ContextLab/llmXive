import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DERIVED_DATA_DIR = PROJECT_ROOT / "data" / "derived"

# Hyperparameters
m = 2
r_factor = 0.2
fd_threshold = 0.2
target_length = 120
atlas_n = 200
dataset_id = "ds000030"  # ADHD-200 dataset from OpenNeuro

# Device configuration (CPU-only)
device = "cpu"

# Configuration dictionary
CONFIG = {
    'm': m,
    'r_factor': r_factor,
    'fd_threshold': fd_threshold,
    'target_length': target_length,
    'atlas_n': atlas_n,
    'dataset_id': dataset_id,
    'device': device,
    'raw_data_dir': str(RAW_DATA_DIR),
    'processed_data_dir': str(PROCESSED_DATA_DIR),
    'derived_data_dir': str(DERIVED_DATA_DIR),
}