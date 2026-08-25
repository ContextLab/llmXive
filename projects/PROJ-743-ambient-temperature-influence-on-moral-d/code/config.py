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
PATH_EXTERNAL_DATA = _PROJECT_ROOT / "data" / "external"
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
DATA_QUALITY_LOG_PATH = PATH_LOGS / "data_quality_log.json"
INGESTION_SUMMARY_LOG_PATH = PATH_LOGS / "ingestion_summary.log"
MORAL_MACHINE_RAW_PATH = PATH_RAW_DATA / "moral_machine.csv.gz"
ERA5_FULL_PATH = PATH_RAW_DATA / "era5_full.h5"
ERA5_SAMPLE_PATH = PATH_RAW_DATA / "era_sample.h5"
BOUNDING_BOX_PATH = PATH_EXTERNAL_DATA / "bounding_box.json"
MERGED_DATASET_PATH = PATH_PROCESSED_DATA / "merged_dataset.parquet"

# --- Random Seeds ---
# Fixed seed for reproducibility across the pipeline
RANDOM_SEED = 42

# --- Thresholds & Constants ---
# Maximum distance (km) allowed for matching Moral Machine records to ERA5 grid points
# Default: 100km as per FR-009
MAX_MATCH_DISTANCE_KM = 100.0

# Sensitivity Analysis Distance Thresholds (Configurable)
# Used in T035b for distance sensitivity analysis
DISTANCE_THRESHOLD_SHORT_KM = 25.0
DISTANCE_THRESHOLD_DEFAULT_KM = 100.0
DISTANCE_THRESHOLD_LONG_KM = 150.0

# Temporal interpolation constraints (FR-002, Edge Case: Missing Temp)
# Maximum gap in hours for which linear interpolation is permitted
MAX_TEMPORAL_GAP_HOURS = 2.0

# Response time filtering bounds (FR-002, FR-010)
MIN_RESPONSE_TIME_MS = 100
MAX_RESPONSE_TIME_MS = 10000

# Temperature thresholds (to be populated by T010b, defaults provided for safety)
# T010b will overwrite these based on 1st/99th percentile of real data
TEMPERATURE_COLD_THRESHOLD = -10.0  # Placeholder, will be updated
TEMPERATURE_HOT_THRESHOLD = 50.0    # Placeholder, will be updated

# Anderson-Darling Sample Fraction (T013a)
ANDERSON_DARLING_SAMPLE_FRACTION = 0.1

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