"""
Configuration utilities for the sleep quality prediction pipeline.
Provides functions to retrieve standard paths, ensure directories exist,
and access global hyperparameters and seeds.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Global random seed for reproducibility
RANDOM_SEED: int = 42

# Hyperparameters for modeling pipeline
# Variance threshold: keep features with variance > this value
# Set to a low default to retain more features initially
VARIANCE_THRESHOLD: float = 0.01

# PCA variance retention thresholds for sensitivity analysis
PCA_RETENTION_THRESHOLDS: list[float] = [0.95, 0.90, 0.85]

# Number of subjects to use for permutation test subset (approximation)
PERMUTATION_SUBSET_SIZE: int = 100

# Maximum framewise displacement threshold (mm) for subject exclusion
MAX_FD_MM: float = 0.3

# ElasticNet hyperparameter search ranges
ELASTICNET_ALPHAS: list[float] = [0.001, 0.01, 0.1, 1.0, 10.0]
ELASTICNET_L1_RATIOS: list[float] = [0.1, 0.3, 0.5, 0.7, 0.9]

# Cross-validation settings
N_CV_FOLDS: int = 5
N_PERMUTATIONS: int = 1000
N_BOOTSTRAP_RESAMPLES: int = 1000

# Resource constraints
MAX_RAM_GB: float = 6.0
MAX_WALL_CLOCK_HOURS: float = 5.0
SENSITIVITY_ANALYSIS_TIME_BUDGET_HOURS: float = 3.0

# Paths
def get_paths() -> Dict[str, Path]:
    """
    Return a dictionary with all important filesystem paths used by the pipeline.

    Keys:
        - project_root: Path to the repository root (parent of the ``code`` directory).
        - raw_dir: Directory where raw HCP data should be stored.
        - processed_dir: Directory for processed feature matrices and predictions.
        - logs_dir: Directory for JSON log files.
        - log_file: Full path to the pipeline log file.
        - behavioral_file: Path to the HCP behavioural CSV (downloaded by ``download_hcp``).
    """
    # ``code`` directory is the location of this file.
    code_dir = Path(__file__).resolve().parent
    project_root = code_dir.parent

    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    logs_dir = project_root / "data" / "logs"
    log_file = logs_dir / "pipeline_run.json"
    behavioral_file = raw_dir / "behavioral" / "hcp1200_behavioral_data.csv"

    return {
        "project_root": project_root,
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "logs_dir": logs_dir,
        "log_file": log_file,
        "behavioral_file": behavioral_file,
    }
    return paths


def ensure_dirs() -> None:
    """
    Create all directories required by the pipeline if they do not already exist.
    This function is idempotent and safe to call multiple times.
    """
    paths = get_paths()
    for key in ["raw_dir", "processed_dir", "logs_dir"]:
        dir_path = paths[key]
        dir_path.mkdir(parents=True, exist_ok=True)


def get_hyperparameters() -> Dict[str, Any]:
    """
    Return a dictionary of all hyperparameters used in the pipeline.
    Useful for logging and reproducibility.
    """
    return {
        "random_seed": RANDOM_SEED,
        "variance_threshold": VARIANCE_THRESHOLD,
        "pca_retention_thresholds": PCA_RETENTION_THRESHOLDS,
        "permutation_subset_size": PERMUTATION_SUBSET_SIZE,
        "max_fd_mm": MAX_FD_MM,
        "elasticnet_alphas": ELASTICNET_ALPHAS,
        "elasticnet_l1_ratios": ELASTICNET_L1_RATIOS,
        "n_cv_folds": N_CV_FOLDS,
        "n_permutations": N_PERMUTATIONS,
        "n_bootstrap_resamples": N_BOOTSTRAP_RESAMPLES,
        "max_ram_gb": MAX_RAM_GB,
        "max_wall_clock_hours": MAX_WALL_CLOCK_HOURS,
        "sensitivity_analysis_time_budget_hours": SENSITIVITY_ANALYSIS_TIME_BUDGET_HOURS,
    }