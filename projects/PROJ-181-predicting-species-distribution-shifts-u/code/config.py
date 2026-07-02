"""
Configuration module for the Species Distribution Shifts project.

Defines all paths, thresholds, random seeds, and parallelism settings.
"""
import os
from pathlib import Path

# Project Root (assumed to be the directory containing 'code/')
# If this script is run from 'code/', we go up one level.
# If run as a module, we try to find the project root relative to this file.
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent

# --- Directory Paths ---
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_ARTIFACTS_DIR = DATA_DIR / "artifacts"
TESTS_DIR = PROJECT_ROOT / "tests"
METRICS_DIR = PROJECT_ROOT / "metrics"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
STATE_DIR = PROJECT_ROOT / "state"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Ensure directories exist (optional safety check, but good for config)
# We do not create them here to avoid side effects on import, 
# but we define the paths correctly.

# --- Random Seeds ---
# Global random seed for reproducibility across numpy, pandas, sklearn
RND_SEED = 42

# --- Parallelism Configuration ---
# Number of jobs for parallel processing (CPU only, per FR-003)
# Set to 2 as per task requirement to limit resource usage
N_JOBS = 2

# --- Thresholds & Hyperparameters ---

# Spatial thinning minimum distance (in degrees/decimal degrees)
# Corresponds to FR-002. Approx 10km at equator is ~0.1 degrees.
SPATIAL_THIN_DISTANCE_DEG = 0.1

# Minimum records for training (T016b)
MIN_TRAINING_RECORDS = 10

# Minimum records for testing/evaluation (FR-006 / T033b)
MIN_TESTING_RECORDS = 100

# KDE Bandwidth for bias layer (in degrees)
# 10km approx 0.1 degrees
KDE_BANDWIDTH_DEG = 0.1

# Occurrence data year ranges
HISTORICAL_START_YEAR = 1970
HISTORICAL_END_YEAR = 2000
RECENT_START_YEAR = 2005
RECENT_END_YEAR = 2020

# GBIF API Configuration
GBIF_BASE_URL = "https://api.gbif.org/v1/occurrence/search"
GBIF_MAX_RESULTS_PER_REQUEST = 300  # GBIF max is usually 300 or 1000, using safe 300

# Climate Data
# Path to the future CMIP6 raster (relative to data/raw)
CMIP6_FUTURE_RASTER_PATH = DATA_RAW_DIR / "cmip6_future.tif"

# Model Evaluation Thresholds
AUC_THRESHOLD = 0.7
TSS_THRESHOLD = 0.4

# Power Analysis Defaults
POWER_TARGET = 0.8
ALPHA = 0.05
EFFECT_SIZE = 0.5

# Sensitivity Analysis Thresholds
SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.1]

# Logging defaults
LOG_LEVEL = "INFO"
LOG_FILE_NAME = "pipeline.log"