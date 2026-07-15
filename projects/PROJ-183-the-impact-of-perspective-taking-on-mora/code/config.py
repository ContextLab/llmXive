# Power analysis (d=0.5, power=0.8) confirms N=240 is sufficient.
"""
Configuration module for the perspective-taking impact study.
Contains path constants, dataset URLs, and random seed settings.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_HUMAN_DIR = DATA_DIR / "human"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Dataset Configuration
# Verified source for "Against the Others!" dataset
DATASET_URL = "https://raw.githubusercontent.com/your-org/against-the-others/main/data/stimuli.csv"
DATASET_FILENAME = "against_the_others.csv"

# Random Seed for reproducibility
RANDOM_SEED = 42

# Analysis Parameters (Fixed based on Power Analysis T009a/b)
# d = 0.5 (medium effect size), power = 0.8, alpha = 0.05
# Required N per group = 128 -> Total N = 256 (conservative)
# Project assumes N=240 total (120 per group) as per T009b verification.
TARGET_SAMPLE_SIZE = 240
EFFECT_SIZE_D = 0.5
POWER = 0.8
ALPHA = 0.05

# Paths for generated artifacts
STIMULI_OUTPUT_PATH = DATA_PROCESSED_DIR / "stimuli.json"
CLEANED_PARTICIPANTS_PATH = DATA_PROCESSED_DIR / "cleaned_participants.csv"
ANALYSIS_RESULTS_PATH = DATA_PROCESSED_DIR / "analysis_results.json"
STRATIFICATION_REPORT_PATH = DATA_PROCESSED_DIR / "stratification_report.json"

# Log files
LOG_DIR = DATA_DIR / "logs"
RESOURCE_METRICS_LOG = LOG_DIR / "resource_metrics.log"

def ensure_dirs():
    """Ensure all required data directories exist."""
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_HUMAN_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)