import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_SIMULATIONS_DIR = PROJECT_ROOT / "data" / "simulations"
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Ensure directories exist
def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_SIMULATIONS_DIR,
        DATA_REPORTS_DIR,
        CODE_DIR,
        TESTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

# Constants
NSIDE_HIGH = 2048
NSIDE_LOW = 128
MASK_RETENTION_THRESHOLD = 0.95
SIMULATION_COUNT = 1000
RANDOM_SEED = 42

# Filename constants
# Data files
RAW_MAP_FILENAME = "raw_n2048.fits"
RAW_MASK_FILENAME = "raw_mask.fits"
PROCESSED_MAP_FILENAME = "processed_n128.fits"
MASKED_MAP_FILENAME = "masked_n2048.fits"
MASK_STATS_FILENAME = "mask_stats.json"
MASK_VALIDATION_FILENAME = "mask_validation_report.json"

# Analysis results
FULL_SKY_CL_FILENAME = "full_sky_cl.npy"
HEMISPHERE_CL_FILENAME = "hemisphere_cl.npy"
NULL_DISTRIBUTION_FILENAME = "null_distribution.npy"
POWER_VALIDATION_FILENAME = "power_validation.json"
FINAL_RESULTS_FILENAME = "final_results.json"
SENSITIVITY_REPORT_FILENAME = "sensitivity_report.json"

# Planck data URLs
PLANCK_URL_BASE = "https://pla.esa.int/ftp/pla/pla/products/CMB/SMICA"
COMMANDER_MASK_URL = "https://pla.esa.int/ftp/pla/pla/products/Masks/COM_Mask_R3.011_CMB.fits"
COMMANDER_MASK_FILENAME = "COM_Mask_R3.011_CMB.fits"

# Thresholds for sensitivity analysis
THRESHOLD_VALUES = [0.01, 0.05, 0.1, 0.2]
