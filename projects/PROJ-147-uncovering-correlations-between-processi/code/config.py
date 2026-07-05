"""
Configuration for the research pipeline.
Includes hyperparameters, paths, and random seeds.
"""
import os
import yaml
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Data Subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Output Files
PIPELINE_LOG = DOCS_DIR / "pipeline.log"
PREDICTIONS_CSV = PROCESSED_DATA_DIR / "predictions.csv"
NEW_PREDICTIONS_CSV = PROCESSED_DATA_DIR / "new_predictions.csv"
EVAL_REPORT_JSON = PROCESSED_DATA_DIR / "evaluation_report.json"
SENSITIVITY_REPORT_JSON = PROCESSED_DATA_DIR / "sensitivity_report.json"
IMPORTANCE_PNG = FIGURES_DIR / "importance_plot.png"
GROUND_TRUTH_JSON = PROCESSED_DATA_DIR / "ground_truth.json"

# Hyperparameters
RANDOM_SEED = 42
N_SPLITS_CV = 5
MAX_TRAIN_TIME_MINUTES = 30
MIN_SAMPLES_PER_FAMILY = 50
MIN_FAMILIES = 3
IMPORTANCE_THRESHOLD = 0.10
R2_THRESHOLD = 0.01

# Flags
ENABLE_DOCKER = os.getenv("ENABLE_DOCKER", "false").lower() == "true"

def ensure_dirs():
    """Create all required directories if they do not exist."""
    for dir_path in [CODE_DIR, DATA_DIR, TESTS_DIR, DOCS_DIR, FIGURES_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_dirs()
    print(f"Project structure initialized at: {PROJECT_ROOT}")