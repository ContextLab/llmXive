import os
from pathlib import Path
from typing import Any, Dict, Union

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Seeds
RANDOM_SEED = 42
PCA_SEED = 42

# Paths
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"
DATA_LOGS_DIR = _PROJECT_ROOT / "data" / "logs"
FIGURES_DIR = _PROJECT_ROOT / "figures"

# Hyperparameters
VARIANCE_THRESHOLD = 0.001
PCA_RETENTION_DEFAULT = 0.95
SUBSET_SIZE_DEFAULT = 100
N_FOLDS_CV = 5
N_PERMUTATIONS = 1000
N_BOOTSTRAP_RESAMPLES = 1000
CONFIDENCE_LEVEL = 0.95

# Time and Resource constraints
MAX_WALL_CLOCK_SECONDS = 18000  # 5 hours
MAX_MEMORY_GB = 6
SENSITIVITY_BUDGET_SECONDS = 10800  # 3 hours

def get_paths() -> dict:
    """
    Return a dictionary of all important paths used in the pipeline.
    """
    return {
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "data_results": str(DATA_RESULTS_DIR),
        "data_logs": str(DATA_LOGS_DIR),
        "figures": str(FIGURES_DIR),
        "behavioral": str(DATA_RAW_DIR / "behavioral" / "hcp1200_behavioral_data.csv"),
        "predictions": str(DATA_PROCESSED_DIR / "predictions.npy"),
        "bootstrap_ci": str(DATA_RESULTS_DIR / "bootstrap_r2_ci.json"),
        "result_report": str(DATA_RESULTS_DIR / "ResultReport.json"),
        "log_file": str(DATA_LOGS_DIR / "pipeline_run.json"),
        "permutation_results": str(DATA_RESULTS_DIR / "permutation_results.json"),
        "sensitivity_results": str(DATA_RESULTS_DIR / "sensitivity_analysis.json"),
        "interpretation": str(DATA_RESULTS_DIR / "interpretation.json"),
        "plot_file": str(DATA_RESULTS_DIR / "brain_connectome.svg"),
    }

def ensure_dirs():
    """
    Create all necessary directories if they do not exist.
    """
    for path in [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        DATA_LOGS_DIR,
        FIGURES_DIR
    ]:
        path.mkdir(parents=True, exist_ok=True)
