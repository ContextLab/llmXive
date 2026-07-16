"""
Base configuration module for the Ambient Temperature Influence on Moral Decision Speed project.

Defines project paths, random seeds, and default thresholds used across the pipeline.
"""

import os
from pathlib import Path

# --- Project Root & Paths ---
# Determine project root relative to this file (assumed to be at code/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory constants
PATH_RAW_DATA = _PROJECT_ROOT / "data" / "raw"
PATH_PROCESSED_DATA = _PROJECT_ROOT / "data" / "processed"
PATH_RESULTS = _PROJECT_ROOT / "results"
PATH_LOGS = PATH_RESULTS / "logs"
PATH_FIGURES = PATH_RESULTS / "figures"
PATH_STATS = PATH_RESULTS / "stats"
PATH_STATE = _PROJECT_ROOT / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
PATH_SPECS = _PROJECT_ROOT / "specs"

# File paths
LOG_FILE_PATH = PATH_LOGS / "pipeline.log"
EXCLUSION_LOG_PATH = PATH_LOGS / "exclusion_log.csv"
DATA_VALIDATION_LOG_PATH = PATH_LOGS / "data_validation_log.txt"
DEMOGRAPHIC_GAP_LOG_PATH = PATH_LOGS / "demographic_gap_log.txt"
LIMITATIONS_REPORT_PATH = PATH_LOGS / "limitations.md"
MODEL_RESULTS_PATH = PATH_STATS / "model_results.json"
NONLINEARITY_COMPARISON_PATH = PATH_STATS / "nonlinearity_comparison.json"

# --- Random Seeds ---
# Fixed seed for reproducibility across the pipeline
RANDOM_SEED = 42

# --- Thresholds & Constants ---
# Maximum distance (km) allowed for matching Moral Machine records to ERA5 grid points
# Default: 100km as per FR-009
MAX_MATCH_DISTANCE_KM = 100.0

# Temporal interpolation constraints (FR-002, Edge Case: Missing Temp)
# Maximum gap in hours for which linear interpolation is permitted
MAX_TEMPORAL_GAP_HOURS = 2.0

# Response time filtering bounds (FR-002, FR-010)
MIN_RESPONSE_TIME_MS = 100
MAX_RESPONSE_TIME_MS = 10000

# --- Environment Overrides ---
# Allow overriding paths via environment variables for testing/CI
def get_path_env_override(name: str, default: Path) -> Path:
    """Retrieve a path from environment variable if set, else return default."""
    env_val = os.getenv(name)
    if env_val:
        return Path(env_val)
    return default

# Example usage (commented out):
# PATH_RAW_DATA = get_path_env_override("RAW_DATA_PATH", PATH_RAW_DATA)