"""
Configuration management for dataset URLs and run parameters.

This module defines the central configuration for the cosmic ray analysis pipeline,
including URLs for data sources (AMS-02, NOAA), directory paths, and analysis
parameters (lags, thresholds, bootstrap iterations).
"""
import os

# --- Directory Paths ---
# Calculate project root relative to this file (code/utils/config.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DATA_CHECKSUMS_PATH = os.path.join(DATA_RAW_DIR, "checksums.txt")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")

# Ensure directories exist (idempotent check, creation handled by setup tasks if needed)
# We do not create them here to avoid side-effects on import, but we ensure paths are valid.
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# --- Dataset URLs ---
# AMS-02: Primary public repository mirror for cosmic ray flux data.
# Note: The actual fetch logic in fetch_ams02.py handles the specific file resolution
# and fallback mechanisms if the primary API is unavailable.
AMS02_BASE_URL = "https://www.ams02-online.org/ams02-data/"
# Fallback mirror for daily averaged flux data (protons, helium, CNO, Fe)
AMS02_MIRROR_URL = "https://github.com/ams02-public/data-mirror/raw/main/daily_flux/"

# NOAA/SWPC: Daily Sunspot Numbers
# Direct link to the official daily sunspot number CSV file
NOAA_SUNSPOT_URL = "https://www.swpc.noaa.gov/products/daily-sunspot-numbers"
# Fallback to the verified CSV file hosted on NOAA's server directly
NOAA_SUNSPOT_CSV_URL = "https://www.swpc.noaa.gov/ftp-dir/realtime/sunspot-number/SN_d_tot_V2.0.txt"

# --- Run Parameters ---
# Data Integrity & Coverage
MIN_COVERAGE_THRESHOLD = 0.50  # Minimum 50% data coverage required for analysis
MAX_GAP_DAYS = 30  # Gaps larger than 30 days are flagged as "Data Gap"

# Analysis Configuration
LAG_WINDOW_MONTHS = 12  # Correlation analysis window: -12 to +12 months
BOOTSTRAP_ITERATIONS = 1000  # Number of iterations for bootstrap resampling validation
SIGNIFICANCE_LEVEL = 0.01  # Threshold for p-value significance in correlations
MODEL_SIGNIFICANCE_LEVEL = 0.05  # Threshold for F-test p-value in model fitting

# Rigidity Bins (Standard AMS-02 bins for reference)
# These are used to filter or bin data if not explicitly provided in the source
RIGIDITY_BINS = [
    1.0, 2.0, 4.0, 8.0, 15.0, 30.0, 60.0, 120.0, 250.0, 500.0  # GV
]

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"