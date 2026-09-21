import os
from pathlib import Path
from typing import List, Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
LOG_DIR = RESULTS_DIR / "logs"
TESTS_DIR = PROJECT_ROOT / "tests"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Random seed for reproducibility
SEED = 42

# Configuration constants
class Config:
    """Central configuration for all hyperparameters and settings."""
    
    # Data settings
    DATA_DIR = DATA_DIR
    DATA_RAW_DIR = DATA_RAW_DIR
    DATA_PROCESSED_DIR = DATA_PROCESSED_DIR
    
    # Results settings
    RESULTS_DIR = RESULTS_DIR
    FIGURES_DIR = FIGURES_DIR
    LOG_DIR = LOG_DIR
    
    # Model settings
    DEFAULT_MODEL_TYPE = "arima"
    VALID_MODEL_TYPES = ["arima", "prophet", "lstm"]
    
    # Evaluation settings
    CONFIDENCE_LEVELS = [0.80, 0.95]
    MAX_EPOCHS = 50
    EARLY_STOPPING_PATIENCE = 5
    LSTM_HIDDEN_UNITS = 32
    
    # Bootstrap settings
    BOOTSTRAP_RESAMPLES = 1000
    SIGNIFICANCE_LEVEL = 0.05
    
    # Conformal prediction settings
    CONFORMAL_CALIBRATION_SIZE = 0.2
    
    # Logging settings
    LOG_LEVEL = "INFO"
    
    # File paths (using constants, no hardcoded paths)
    COVERAGE_RESULTS_FILE = RESULTS_DIR / "coverage.csv"
    DISTRIBUTIONAL_METRICS_FILE = RESULTS_DIR / "distributional_metrics.csv"
    SIGNIFICANCE_RESULTS_FILE = RESULTS_DIR / "significance_test.csv"
    CONFORMAL_RESULTS_FILE = RESULTS_DIR / "conformal_results.csv"
    SAMPLE_METADATA_FILE = DATA_PROCESSED_DIR / "sample_metadata.json"
    SKIPPED_SERIES_LOG = RESULTS_DIR / "skipped_series.log"
    BENCHMARK_TIMING_FILE = RESULTS_DIR / "benchmark_timing.csv"

# Ensure directories exist
def ensure_dirs():
    """Create all necessary directories if they don't exist."""
    directories = [
        CODE_DIR,
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        LOG_DIR,
        TESTS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        if not directory.exists():
            raise FileNotFoundError(f"Failed to create directory: {directory}")
    
    return True

# Initialize directories on import
ensure_dirs()