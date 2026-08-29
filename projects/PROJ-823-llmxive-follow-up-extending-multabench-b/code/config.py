"""
Global configuration and paths.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
FIGURES_DIR = DATA_DIR / "figures"
LOGS_DIR = DATA_DIR / "logs"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Random seeds for reproducibility
RANDOM_SEED = 42
SENSITIVITY_SEEDS = [42, 123, 456, 789, 101112]

def ensure_directories():
    """Ensure all required directories exist."""
    for d in [DATA_DIR, CODE_DIR, TESTS_DIR, ARTIFACTS_DIR, PROCESSED_DIR, RAW_DIR, FIGURES_DIR, LOGS_DIR, STATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)