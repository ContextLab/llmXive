import os
from pathlib import Path

# Random Seed
RANDOM_SEED = 42

# Directory Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
SPECS_DIR = PROJECT_ROOT / "specs"
CONTRACTS_DIR = SPECS_DIR / "contracts"

# Ensure directories exist
def ensure_directories():
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, CONTRACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Lichess dataset URL (standard Lichess dataset identifier on HuggingFace)
LICHESS_DATASET_URL = "Lichess/lichess_db_standard_rated"

# Additional configuration constants
SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000  # Approximate bytes per game for size estimation
USE_MOVE_5 = False  # Whether to compute material imbalance at move 5

# Dataset verification thresholds
DATASET_SAMPLE_SIZE = 1000  # Number of games to sample for verification
DATASET_MOVE_TIME_MISSING_THRESHOLD = 5.0  # Percentage threshold to HALT (5%)