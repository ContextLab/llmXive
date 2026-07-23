"""
Configuration constants for the stability assessment pipeline.
Defines dataset IDs and output paths.
"""
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Output Paths
RESULTS_DIR = PROJECT_ROOT / "results"
RAW_EVALUATIONS_PATH = RESULTS_DIR / "raw_evaluations.csv"
STABILITY_METRICS_PATH = RESULTS_DIR / "stability_metrics.csv"
CORRELATION_RESULTS_PATH = RESULTS_DIR / "correlation_results.csv"
PERMUTATION_RESULTS_PATH = RESULTS_DIR / "permutation_results.csv"
FINAL_REPORT_PATH = RESULTS_DIR / "final_report.md"

# Dataset Configuration (Constitution Principle VII)
# 15 Binary Classification Datasets (OpenML IDs)
# Selected to span a wide range of sample sizes and feature counts
DATASET_IDS = [
    2,    # Breast Cancer (small, classic)
    11,   # Diabetes (small)
    15,   # Heart Disease (Cleveland)
    29,   # Ionosphere
    31,   # Sonar
    37,   # Credit Approval
    44,   # Hepatitis
    54,   # Pima Indians Diabetes
    188,  # German Credit
    405,  # Bank Marketing (subset logic applied if needed, but ID exists)
    633,  # Adult (subset logic applied if needed)
    1486, # Phishing Websites
    1590, # Online News Popularity (binary subset)
    23381, # Higgs (small subset or similar large scale if available, using smaller proxy if needed)
    35939  # Covertype (binary subset)
]

# Models Configuration
MODEL_NAMES = ["LogisticRegression", "RandomForest", "LinearSVM"]

# Hyperparameters
N_SPLITS = 10
N_REPEATS = 10
RANDOM_SEED = 42

# Thresholds
MIN_SAMPLES = 100
MAX_SAMPLES = 100000
