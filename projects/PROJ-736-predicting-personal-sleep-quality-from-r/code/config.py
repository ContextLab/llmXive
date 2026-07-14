"""Configuration module for the sleep quality prediction pipeline."""
import os
import random
from pathlib import Path
from typing import Dict, Any, Union

# Set random seeds for reproducibility
RANDOM_SEED = 42
np_seed = 42  # Will be set when numpy is imported

def get_paths() -> Dict[str, str]:
    """Get all project paths.
    
    Returns:
        Dictionary of path names to absolute paths
    """
    base_dir = Path(__file__).parent.parent
    
    paths = {
        "base": str(base_dir),
        "code": str(base_dir / "code"),
        "data": str(base_dir / "data"),
        "data_raw": str(base_dir / "data" / "raw"),
        "data_processed": str(base_dir / "data" / "processed"),
        "data_results": str(base_dir / "data" / "results"),
        "data_features": str(base_dir / "data" / "processed" / "features"),
        "data_logs": str(base_dir / "data" / "logs"),
        "figures": str(base_dir / "data" / "results"),
        "raw": str(base_dir / "data" / "raw"),
        "processed": str(base_dir / "data" / "processed"),
        "logs": str(base_dir / "data" / "logs"),
        "behavioral": str(base_dir / "data" / "raw" / "behavioral" / "hcp1200_behavioral_data.csv"),
        "filtered_subjects": str(base_dir / "data" / "processed" / "filtered_subjects.json"),
    }
    
    return paths

def ensure_dirs() -> None:
    """Ensure all required directories exist."""
    paths = get_paths()
    for path_key in ["data_raw", "data_processed", "data_results", "data_logs", "data_features", "figures"]:
        os.makedirs(paths[path_key], exist_ok=True)

def get_hyperparameter(name: str, default: Any = None) -> Any:
    """Get a hyperparameter value.
    
    Args:
        name: Parameter name
        default: Default value if not found
        
    Returns:
        Parameter value or default
    """
    # Default hyperparameters
    hyperparameters = {
        "variance_threshold": 0.01,  # Low default as specified
        "pca_retention": 0.95,  # Default PCA retention
        "subset_size": 100,  # Default subset size for permutation test
        "n_folds": 5,  # Default CV folds
        "max_iter": 1000,  # Default max iterations for ElasticNet
        "alpha_range": [0.001, 0.01, 0.1, 1.0],  # Default alpha range
        "l1_ratio": 0.5,  # Default L1 ratio for ElasticNet
    }
    
    return hyperparameters.get(name, default)

def set_seeds() -> None:
    """Set random seeds for reproducibility."""
    random.seed(RANDOM_SEED)
    try:
        import numpy as np
        np.random.seed(np_seed)
    except ImportError:
        pass
