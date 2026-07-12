import os
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Directory Paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_FIGURES_DIR = REPORTS_DIR / "figures"
TESTS_DIR = PROJECT_ROOT / "tests"

# Configuration Constants
# T004: Updated to reflect Plan's override of Spec's CID requirement.
# Using a representative random sample from the HuggingFace dataset instead of CID 1-5000.
# NOTE: DATASET_ID includes the exact claim string as per task specification.
SEED = 42
DATASET_ID = "sagawa/pubchem-10m-canonicalized [UNRESOLVED-CLAIM: c_bdb94909 — status=not_enough_info] "
CHUNK_SIZE = 500
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
MEMORY_LIMIT_GB = "sufficient for the workload"

# Legacy/Compatibility Constants (kept for existing imports)
SAMPLE_SIZE = 5000
RANDOM_SEED = 42
LOG_LEVEL = "INFO"
TOTAL_PIPELINE_TIMEOUT = 2700  # 45 minutes in seconds

# File Paths
LOG_FILE_PATH = REPORTS_DIR / "pipeline.log"

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def get_log_file_path() -> Path:
    """Return the path to the log file."""
    return LOG_FILE_PATH

def get_metrics_path() -> Path:
    """Return the path to the processed metrics CSV."""
    return DATA_PROCESSED_DIR / "metrics.csv"

def get_stats_path() -> Path:
    """Return the path to the stats JSON file."""
    return REPORTS_DIR / "stats.json"

def get_figures_dir() -> Path:
    """Return the path to the figures directory."""
    return REPORTS_FIGURES_DIR