import os
from pathlib import Path

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent

# Noise thresholds (dB)
# Low noise: < 45 dB
# High noise: > 70 dB
# Moderate noise: 45 - 70 dB
NOISE_THRESHOLD_LOW = 45.0
NOISE_THRESHOLD_HIGH = 70.0

# Statistical parameters
# Median Absolute Deviation (MAD) threshold for outlier removal
MAD_OUTLIER_THRESHOLD = 3.5

# Random seed for reproducibility
RANDOM_SEED = 42

# File paths
RAW_DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(ROOT_DIR, "data", "processed")
RESULTS_DIR = os.path.join(ROOT_DIR, "data", "results")
CONTRACTS_DIR = os.path.join(ROOT_DIR, "contracts")
FIGURES_DIR = os.path.join(ROOT_DIR, "figures")
FIXTURES_DIR = os.path.join(ROOT_DIR, "fixtures")

# Ensure directories exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CONTRACTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(FIXTURES_DIR, exist_ok=True)