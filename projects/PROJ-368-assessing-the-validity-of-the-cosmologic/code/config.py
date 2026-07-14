import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Data Subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SIMULATIONS_DIR = DATA_DIR / "simulations"
REPORTS_DIR = DATA_DIR / "reports"
FIGURES_DIR = DATA_DIR / "figures"

# Simulation Subdirectories
SIMULATED_MAPS_DIR = SIMULATIONS_DIR / "maps"
SIMULATED_CL_DIR = SIMULATIONS_DIR / "cl"

# Configuration Constants
RANDOM_SEED = 42
NSIDE_ORIGINAL = 2048
NSIDE_TARGET = 128
L_MIN = 2
L_MAX = 3 * NSIDE_TARGET - 1
L_MAX_ANALYSIS = L_MAX
N_SIMULATIONS = 1000
N_POWER_VALIDATION = 100
MIN_SKY_FRACTION = 0.95

# Output Files
MASK_STATS_FILE = PROCESSED_DATA_DIR / "mask_stats.json"
POWER_VALIDATION_REPORT = REPORTS_DIR / "power_validation.json"

def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [
        CODE_DIR,
        DATA_DIR,
        TESTS_DIR,
        DOCS_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        SIMULATIONS_DIR,
        REPORTS_DIR,
        FIGURES_DIR,
        SIMULATED_MAPS_DIR,
        SIMULATED_CL_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
