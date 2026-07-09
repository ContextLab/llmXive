"""
Configuration module for the Neural Synchrony and Attention Switching project.

Defines paths, random seeds, and hyperparameters for the pipeline.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-498-investigating-the-relationship-between-n"

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_METRICS = DATA_DIR / "metrics"
DATA_TRIAL_LEVEL = DATA_DIR / "trial_level"

CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
LOGS_DIR = PROJECT_ROOT / "logs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SPECS_DIR = PROJECT_ROOT / "specs"

# Specific Output Paths
LOG_FILE = LOGS_DIR / "processing.log"
EXCLUSIONS_FILE = DATA_DIR / "exclusions.csv"
DATA_GAP_REPORT = DATA_DIR / "data_gap_report.json"
RUNTIME_LOG = DATA_DIR / "metrics" / "runtime_log.json"
SYNCHRONY_METRICS = DATA_DIR / "metrics" / "synchrony_metrics.csv"
CORRELATION_RESULTS = DATA_DIR / "metrics" / "correlation_results.json"
TRIAL_LEVEL_ANALYSIS = DATA_DIR / "metrics" / "trial_level_analysis.json"
SENSITIVITY_REPORT = DATA_DIR / "metrics" / "sensitivity_report.json"
RESULTS_SUMMARY = PROJECT_ROOT / "results_summary.md"
PER_TRIAL_SYNCHRONY = DATA_DIR / "trial_level" / "per_trial_synchrony.csv"

# Random Seeds
RANDOM_SEED = 42
NP_SEED = 42

# Hyperparameters
# Bandpass filter settings
FILTER_LOW_FREQ = 1.0  # Hz
FILTER_HIGH_FREQ = 45.0  # Hz (Upper limit as per task requirement)

# Notch filter settings
NOTCH_FREQ = 50.0  # Hz (Default to 50Hz, can be adjusted for 60Hz if needed)

# Epoching settings
EPOCH_TMIN = -1.0  # seconds (pre-stimulus)
EPOCH_TMAX = 2.0  # seconds (post-stimulus, +2000ms as per task requirement)
BASELINE = (None, 0)  # Baseline correction from start to 0ms (pre-stim)

# Pre-stimulus window for synchrony calculation (relative to stimulus onset)
# Task specifies pre-stim to 0ms, so we use the full pre-stimulus epoch for calculation
PRE_STIM_START = -1.0  # Start of pre-stim window in seconds
PRE_STIM_END = 0.0     # End of pre-stim window in seconds

# Frequency bands for analysis (Hz)
THETA_BAND = (4, 8)
GAMMA_BAND = (30, 45)  # Upper limit 45Hz as per task requirement

# Artifact removal thresholds
KURTOSIS_THRESHOLD = 5.0
SPECTRAL_PEAK_THRESHOLD_HZ = 30.0  # Hz
MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_PERCENT = 50.0

# Memory constraints
MAX_RSS_GB = 6.5
MAX_RUNTIME_HOURS = 4  # Several hours as per task requirement

# Statistical parameters
PERMUTATION_ITERATIONS = 1000
SIGNIFICANCE_LEVEL = 0.05

# Ensure directories exist upon import (optional safety, usually done by setup_dirs.py)
def ensure_directories():
    """Create all necessary directories if they don't exist."""
    for dir_path in [
        DATA_RAW, DATA_PROCESSED, DATA_METRICS, DATA_TRIAL_LEVEL,
        CODE_DIR, TESTS_DIR, LOGS_DIR, CONTRACTS_DIR
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize directories immediately
ensure_directories()