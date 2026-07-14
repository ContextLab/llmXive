"""
Configuration management for the sleep quality prediction pipeline.
Handles paths, seeds, and hyperparameters.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Union

# Project root is the parent of the code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Fixed seed for reproducibility
SEED = 42
random.seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

def get_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of all critical paths in the project.
    
    Keys:
      - root: Project root
      - data: Root data directory
      - raw: Raw data directory
      - processed: Processed data directory
      - results: Results directory
      - behavioral_csv: Path to the HCP behavioral CSV
      - processed_features: Path to the preprocessed feature matrix
      - processed_labels: Path to the labels array
      - subject_ids: Path to subject IDs array
      - predictions: Path to save predictions
      - report: Path to the final JSON report
    """
    data_root = PROJECT_ROOT / "data"
    processed_root = data_root / "processed"
    results_root = data_root / "results"
    raw_root = data_root / "raw"
    behavioral_root = raw_root / "behavioral"
    
    return {
        "root": PROJECT_ROOT,
        "data": data_root,
        "raw": raw_root,
        "processed": processed_root,
        "results": results_root,
        "behavioral_csv": behavioral_root / "hcp1200_behavioral_data.csv",
        "processed_features": processed_root / "features.npy",
        "processed_labels": processed_root / "labels.npy",
        "subject_ids": processed_root / "subject_ids.npy",
        "predictions": processed_root / "predictions.npy",
        "report": results_root / "ResultReport.json",
        "plots": results_root / "plots",
        "logs": data_root / "logs"
    }


def ensure_dirs():
    """Creates all necessary directories if they do not exist."""
    paths = get_paths()
    for p in paths.values():
        if isinstance(p, Path):
            p.mkdir(parents=True, exist_ok=True)


def get_hyperparameter(key: str, default: Any = None) -> Any:
    """
    Retrieves a hyperparameter value.
    
    In a real implementation, this would read from a YAML/JSON config file.
    For this task, we return sensible defaults or values from environment variables.
    """
    # Default hyperparameters for the pipeline
    defaults = {
        "variance_threshold": 0.01,  # Low default to keep many features
        "pca_retention": 0.95,       # Retain 95% variance
        "cv_folds": 5,               # 5-fold CV
        "elasticnet_l1_ratio": 0.5,  # Balanced L1/L2
        "max_iter": 1000,            # Max iterations for solver
        "n_permutations": 1000,      # For permutation testing
        "bootstrap_resamples": 1000, # For bootstrap CI
        "subset_size": 100           # For permutation subset (T022)
    }
    
    if key in defaults:
        return defaults[key]
    
    # Check environment variable override
    env_val = os.environ.get(f"SLP_{key.upper()}", None)
    if env_val is not None:
        # Try to convert to int/float if possible
        try:
            if '.' in env_val:
                return float(env_val)
            return int(env_val)
        except ValueError:
            return env_val
    
    return default
