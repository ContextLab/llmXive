"""
Configuration management for the llmXive fatigue analysis pipeline.
Handles paths, random seeds, and hyperparameters.
"""
import os
import random
import numpy as np
from typing import Dict, Any, Optional
import json

# --- Project Root Paths ---
# Determine project root relative to this file's location (code/utils/config.py)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Directory Structure
DIRS = {
    "code": os.path.join(_PROJECT_ROOT, "code"),
    "data": os.path.join(_PROJECT_ROOT, "data"),
    "data_raw": os.path.join(_PROJECT_ROOT, "data", "raw"),
    "data_processed": os.path.join(_PROJECT_ROOT, "data", "processed"),
    "results": os.path.join(_PROJECT_ROOT, "results"),
    "results_plots": os.path.join(_PROJECT_ROOT, "results", "plots"),
    "specs": os.path.join(_PROJECT_ROOT, "specs"),
}

# Output File Paths
PATHS = {
    "validated_data": os.path.join(DIRS["data_raw"], "validated_data.csv"),
    "cleaned_data": os.path.join(DIRS["data_processed"], "cleaned_aluminum_fatigue.csv"),
    "feature_matrix": os.path.join(DIRS["data_processed"], "feature_matrix.csv"),
    "metrics": os.path.join(DIRS["results"], "metrics.json"),
    "anova_summary": os.path.join(DIRS["results"], "anova_summary.csv"),
    "sensitivity_proxy": os.path.join(DIRS["results"], "sensitivity_proxy_comparison.csv"),
    "exclusion_report": os.path.join(DIRS["results"], "exclusion_report.log"),
    "memory_profile": os.path.join(DIRS["results"], "memory_profile.log"),
    "data_source_report": os.path.join(DIRS["results"], "data_source_report.md"),
    "methodology_report": os.path.join(DIRS["results"], "methodology_report.md"),
    "synthetic_images_dir": os.path.join(DIRS["data_raw"], "synthetic_images"),
}

# --- Random Seeds ---
# Default seed for reproducibility
DEFAULT_SEED = 42

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets random seeds for numpy, python's random, and (optionally) torch.
    Ensures deterministic behavior across runs.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not required for this project, ignore if missing

# --- Hyperparameters & Config ---
HYPERPARAMETERS = {
    "model": {
        "max_estimators": 100,
        "max_depth": 10,
        "random_state": DEFAULT_SEED,
        "n_jobs": -1,  # Use all available CPU cores
    },
    "cv": {
        "n_folds": 5,
        "shuffle": True,
    },
    "feature_extraction": {
        "image_size": (512, 512),
        "glcm_distances": [1],
        "glcm_angles": [0],
    },
    "statistical": {
        "alpha": 0.05,
        "n_bootstrap": 1000,
        "correction_method": "bonferroni",  # Options: 'bonferroni', 'benjamini-hochberg'
    },
    "memory": {
        "max_ram_gb": 7.0,
    },
    "data": {
        "missing_threshold_impute": 0.20,  # 20%
        "min_records": 100,
        "synthetic_count": 150,
    }
}

def get_config_value(category: str, key: str, default: Any = None) -> Any:
    """
    Safely retrieve a configuration value by category and key.
    """
    try:
        return HYPERPARAMETERS[category][key]
    except (KeyError, TypeError):
        return default

def save_config(path: Optional[str] = None) -> str:
    """
    Saves the current hyperparameters to a JSON file.
    Defaults to results/config_snapshot.json if path is not provided.
    """
    if path is None:
        path = os.path.join(DIRS["results"], "config_snapshot.json")
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    config_data = {
        "seeds": {"default": DEFAULT_SEED},
        "hyperparameters": HYPERPARAMETERS,
        "paths": PATHS,
        "directories": DIRS
    }
    
    with open(path, 'w') as f:
        json.dump(config_data, f, indent=4)
    
    return path

# Initialize seed on module load for immediate availability
set_seed(DEFAULT_SEED)
