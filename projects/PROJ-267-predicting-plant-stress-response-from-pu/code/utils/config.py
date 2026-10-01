import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data paths
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

# Results and logs paths
RESULTS_PATH = PROJECT_ROOT / "results"
LOG_PATH = PROJECT_ROOT / "logs"

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10 MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

# Random seeds
RANDOM_SEED = int(os.getenv('RANDOM_SEED', '42'))

# Species and stress constants
SPECIES_LIST = ['Arabidopsis', 'Rice', 'Wheat']
STRESS_CONDITIONS = ['drought', 'salinity', 'heat']

# Validation thresholds
REFERENCE_VALIDATOR_THRESHOLD = float(os.getenv('REFERENCE_VALIDATOR_THRESHOLD', '0.7'))
MIN_DETECTION_RATE = 0.5  # 50% detection rate threshold

def get_project_root() -> Path:
    """Get the project root directory."""
    return PROJECT_ROOT

def get_data_path() -> Path:
    """Get the data directory path."""
    return DATA_RAW_PATH

def get_results_path() -> Path:
    """Get the results directory path."""
    return RESULTS_PATH

def get_log_path() -> Path:
    """Get the logs directory path."""
    return LOG_PATH
