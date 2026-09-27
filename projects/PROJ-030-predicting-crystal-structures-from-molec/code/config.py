"""
Configuration management for the Crystal Structure Prediction pipeline.

This module centralizes all project paths, random seeds, and hyperparameters.
It provides functions to resolve absolute and relative paths based on the
project root, ensuring consistent artifact locations across different environments.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

# --- Project Root Resolution ---
# The project root is the directory containing 'code/', 'data/', 'tests/', etc.
# We detect it by looking for the standard directory structure.
_PROJECT_ROOT: Optional[Path] = None

def _resolve_project_root() -> Path:
    """
    Dynamically resolve the project root directory.
    Looks for the standard 'code' directory relative to the current file.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # Start from this file's location
    current_file = Path(__file__).resolve()
    
    # Try to find 'code' directory going up the tree
    # Standard structure: <root>/code/config.py
    if current_file.parent.name == 'code':
        _PROJECT_ROOT = current_file.parent.parent
    else:
        # Fallback: assume current working directory if structure is non-standard
        # or if running from a different context
        _PROJECT_ROOT = Path.cwd()
        
    # Verify the root contains expected directories
    if not (_PROJECT_ROOT / 'code').exists():
        # If we can't find 'code', we might be in a flat structure or misconfigured
        # For robustness, we assume the current directory is the root
        pass 
        
    return _PROJECT_ROOT

def get_project_root() -> Path:
    """Returns the resolved project root path."""
    return _resolve_project_root()

# --- Path Resolution Helpers ---

def get_path_absolute(relative_path: Union[str, Path]) -> Path:
    """
    Resolves a relative path (relative to project root) to an absolute Path.
    
    Args:
        relative_path: Path string or object relative to the project root.
        
    Returns:
        Absolute Path object.
    """
    root = get_project_root()
    return (root / relative_path).resolve()

def get_path_relative(absolute_path: Union[str, Path]) -> Path:
    """
    Resolves an absolute path to a path relative to the project root.
    
    Args:
        absolute_path: Absolute Path object or string.
        
    Returns:
        Path relative to the project root.
    """
    root = get_project_root()
    abs_p = Path(absolute_path).resolve()
    try:
        return abs_p.relative_to(root)
    except ValueError:
        # If the path is not under the project root, return the absolute path
        # or raise an error depending on strictness requirements.
        # Here we return the absolute path to avoid crashes, but log a warning.
        return abs_p

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensures the directory at the given path exists, creating it if necessary.
    
    Args:
        path: Path to the directory.
        
    Returns:
        The Path object for the directory.
    """
    p = Path(path)
    if not p.is_absolute():
        p = get_path_absolute(p)
    p.mkdir(parents=True, exist_ok=True)
    return p

# --- Configuration Constants ---

# Random Seeds
RANDOM_SEED: int = 42
Numpy_SEED: int = 42
PyTorch_SEED: int = 42  # If applicable later

# Hyperparameters
HYPERPARAMETERS: Dict[str, Any] = {
    "model": {
        "random_forest": {
            "n_estimators": 200,
            "max_depth": 20,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "max_features": "sqrt",
            "n_jobs": -1
        },
        "gradient_boosting": {
            "n_estimators": 150,
            "max_depth": 10,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "random_state": RANDOM_SEED
        },
        "ridge_regression": {
            "alpha": 1.0,
            "solver": "auto"
        }
    },
    "training": {
        "batch_size": 64,
        "timeout_seconds": 3600,  # 1 hour default timeout
        "max_samples_subset": 2000  # For timeout enforcement (FR-007)
    },
    "fingerprint": {
        "radius": 2,  # ECFP4
        "n_bits": 2048,
        "min_path": 1,
        "max_path": 7
    },
    "split": {
        "test_size": 0.2,
        "val_size": 0.1,
        "rare_space_group_threshold": 20
    }
}

# Target Sample Sizes (from Power Analysis T006b)
TARGET_SAMPLE_SIZE: int = 500  # Target scaffolds

# --- Path Definitions (Lazy Evaluation) ---
# We define functions to get paths to ensure they are resolved at runtime
# in case the project root changes or is set dynamically.

def get_path_data() -> Path:
    return get_path_absolute("data")

def get_path_processed_data() -> Path:
    return get_path_absolute("data/processed")

def get_path_results() -> Path:
    return get_path_absolute("data/results")

def get_path_validation() -> Path:
    return get_path_absolute("data/validation")

def get_path_models() -> Path:
    return get_path_absolute("data/models")

def get_path_logs() -> Path:
    return get_path_absolute("logs")

def get_path_figures() -> Path:
    return get_path_absolute("figures")

def get_path_code() -> Path:
    return get_path_absolute("code")

def get_path_tests() -> Path:
    return get_path_absolute("tests")

def get_path_specs() -> Path:
    return get_path_absolute("specs")

# Specific Artifact Paths
PATH_POLYMORPHIC_DATASET = get_path_absolute("data/processed/polymorphic_dataset.csv")
PATH_CRYSTAL_DATASET = get_path_absolute("data/processed/crystal_dataset.csv")
PATH_SPLIT_INDICES = get_path_absolute("data/processed/split_indices.json")
PATH_RF_MODEL = get_path_absolute("data/models/rf_model.pkl")
PATH_GB_MODEL = get_path_absolute("data/models/gb_model.pkl")
PATH_RIDGE_MODEL = get_path_absolute("data/models/ridge_model.pkl")
PATH_METRICS = get_path_absolute("data/results/model_metrics.json")
PATH_LOG_FILE = get_path_absolute("logs/pipeline.log")

# --- Configuration Dictionary ---

def get_config_dict() -> Dict[str, Any]:
    """
    Returns a dictionary representation of the current configuration.
    Useful for logging, saving configs, or passing to other modules.
    """
    return {
        "paths": {
            "project_root": str(get_project_root()),
            "data": str(get_path_data()),
            "processed": str(get_path_processed_data()),
            "results": str(get_path_results()),
            "models": str(get_path_models()),
            "logs": str(get_path_logs()),
            "figures": str(get_path_figures())
        },
        "seeds": {
            "random": RANDOM_SEED,
            "numpy": Numpy_SEED,
            "pytorch": PyTorch_SEED
        },
        "hyperparameters": HYPERPARAMETERS,
        "targets": {
            "sample_size": TARGET_SAMPLE_SIZE
        }
    }

# --- Main / CLI ---

def main():
    """
    CLI entry point to print current configuration.
    """
    config = get_config_dict()
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()
