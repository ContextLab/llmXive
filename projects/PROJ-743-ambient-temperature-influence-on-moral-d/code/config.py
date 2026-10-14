"""
Configuration constants for the Ambient Temperature Influence project.
"""

import os
from pathlib import Path

def get_path_env_override(key: str, default: Path) -> Path:
    """Get a path from environment variable or return default."""
    return Path(os.getenv(key, default))

# Base directories
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
RESULTS_LOGS_DIR = Path("results/logs")

# Thresholds and parameters
DISTANCE_THRESHOLD_KM = 100  # km
TEMPERATURE_MIN = -50.0  # degrees Celsius
TEMPERATURE_MAX = 50.0   # degrees Celsius
RESPONSE_TIME_MIN_MS = 100   # milliseconds
RESPONSE_TIME_MAX_MS = 10000 # milliseconds

# Random seed for simulations
AD_TEST_SEED = 42
