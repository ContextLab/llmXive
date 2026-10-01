"""
Configuration module for the project.
Defines paths, seeds, and thresholds.
"""
import os
from pathlib import Path

def get_path_env_override(key: str, default: str) -> str:
    """
    Retrieve a path from an environment variable, falling back to default.
    Resolves relative paths against the project root.
    """
    val = os.getenv(key, default)
    if not os.path.isabs(val):
        # Assume relative to project root if not absolute
        project_root = Path(__file__).resolve().parent.parent
        val = str(project_root / val)
    return val

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RESULTS_FIGURES = PROJECT_ROOT / "results" / "figures"
RESULTS_LOGS = PROJECT_ROOT / "results" / "logs"
RESULTS_STATS = PROJECT_ROOT / "results" / "stats"
TESTS_DIR = PROJECT_ROOT / "tests"
CODE_DIR = PROJECT_ROOT / "code"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Thresholds
DISTANCE_THRESHOLD_KM = 100.0
TEMPERATURE_MIN = -50.0
TEMPERATURE_MAX = 60.0
RESPONSE_TIME_MIN_MS = 100
RESPONSE_TIME_MAX_MS = 10000

# Statistical Configuration
AD_TEST_SEED = 42
AD_TEST_FRACTION = 0.1  # 10% sample for Anderson-Darling test

# Random Seeds
RANDOM_SEED = 42