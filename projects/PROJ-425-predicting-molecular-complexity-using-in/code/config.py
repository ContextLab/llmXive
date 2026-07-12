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
SAMPLE_SIZE = 5000
CHUNK_SIZE = 500
RANDOM_SEED = 42
LOG_LEVEL = "INFO"
TIMEOUT_SECONDS = 30  # Per molecule metric computation timeout
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