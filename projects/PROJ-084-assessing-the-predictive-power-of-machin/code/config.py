"""
Configuration module for PROJ-084.
Contains path constants, random seeds, and hyperparameter grids.
"""
import os
from pathlib import Path
from typing import Dict, List, Any

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
TESTS_DIR = PROJECT_ROOT / "tests"

# Raw data paths
USPTO_RAW_PATH = RAW_DIR / "uspto_raw.parquet"
DOWNLOAD_CHECKSUM_PATH = RESULTS_DIR / "download_checksum.txt"

# Processed data paths
CLEANED_REACTIONS_PATH = PROCESSED_DIR / "cleaned_reactions.parquet"
SCAFFOLD_GROUPS_PATH = PROCESSED_DIR / "scaffold_groups.parquet"
STRATIFIED_GROUPS_PATH = PROCESSED_DIR / "stratified_groups.csv"
VALIDATION_INDICES_PATH = PROCESSED_DIR / "validation_set_indices.csv"

# Results paths
SPLIT_LOG_PATH = RESULTS_DIR / "split_log.json"
TEST_METRICS_PATH = RESULTS_DIR / "test_metrics.json"
PER_CLASS_METRICS_PATH = RESULTS_DIR / "per_class_metrics.json"
PERMUTATION_IMPORTANCE_PATH = RESULTS_DIR / "permutation_importance.json"
SUBSTRUCTURE_IMPORTANCE_PATH = RESULTS_DIR / "substructure_importance.json"
DATA_QUALITY_PATH = RESULTS_DIR / "data_quality_report.json"
MEMORY_PROFILE_PATH = RESULTS_DIR / "memory_profile.log"
RUNTIME_PROFILE_PATH = RESULTS_DIR / "runtime_profile.json"
FINAL_REPORT_PATH = RESULTS_DIR / "final_report.json"
BEST_MODELS_DIR = RESULTS_DIR / "best_models"

# Random seeds
RANDOM_SEED = 42
NumpyRandomSeed = 42

# Hyperparameter grids
RF_GRID: Dict[str, List[Any]] = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, 30, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 2],
}

SVM_GRID: Dict[str, List[Any]] = {
    "C": [0.1, 1.0, 10.0],
    "kernel": ["linear", "rbf"],
    "gamma": ["scale", "auto"],
}

# Memory constraints
MAX_MEMORY_GB = 7.0

# Yield threshold for high-yield classification (SC-001)
YIELD_THRESHOLD = 70.0  # Empirically derived, can be adjusted

# Fingerprint dimensions
ECFP_DIMENSION = 2048
MACCS_DIMENSION = 167

def ensure_dirs():
    """Create all required directories if they don't exist."""
    dirs = [
        CODE_DIR,
        DATA_DIR,
        RAW_DIR,
        PROCESSED_DIR,
        RESULTS_DIR,
        TESTS_DIR,
        BEST_MODELS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return True
