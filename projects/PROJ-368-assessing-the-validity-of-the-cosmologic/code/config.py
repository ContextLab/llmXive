import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_SIMULATIONS_DIR = PROJECT_ROOT / "data" / "simulations"
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Ensure directories exist
def ensure_directories():
    """Create all necessary data directories if they don't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Configuration constants
RANDOM_SEED = 42
NSIDE_HIGH = 2048
NSIDE_LOW = 128
N_SIMULATIONS = 1000
L_MIN = 2
L_MAX = 128
MASK_RETENTION_THRESHOLD = 0.95  # Minimum sky fraction required for mask validation

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

# Reports
FINAL_RESULTS_FILENAME = "final_results.json"
SENSITIVITY_REPORT_FILENAME = "sensitivity_report.json"
POWER_VALIDATION_FILENAME = "power_validation.json"
SPEC_ALIGNMENT_LOG_FILENAME = "spec_alignment_log.txt"

# Simulations
SIMULATION_PREFIX = "simulation_"
SIMULATION_EXTENSION = ".fits"

# URLs for Planck data (ESA Archive)
PLANCK_SMICA_URL = "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CMB_ILU_SMICA_R3.011_Nside2048_Fullsky.fits"
PLANCK_MASK_URL = "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_Mask_R3.011_CMB.fits"