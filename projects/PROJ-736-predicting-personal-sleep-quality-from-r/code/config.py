"""Configuration management for the sleep quality prediction pipeline."""
import os
import random
from pathlib import Path
from typing import Dict, Any, Union

def get_paths() -> Dict[str, str]:
    """
    Get all project paths relative to the project root.
    
    Returns:
        Dictionary of path names to absolute paths.
    """
    # Assume project root is the parent of the code directory
    code_dir = Path(__file__).parent
    project_root = code_dir.parent
    
    return {
        "project_root": str(project_root),
        "code": str(code_dir),
        "data_raw": str(project_root / "data" / "raw"),
        "data_raw_behavioral": str(project_root / "data" / "raw" / "behavioral"),
        "data_processed": str(project_root / "data" / "processed"),
        "data_results": str(project_root / "data" / "results"),
        "figures": str(project_root / "figures"),
        "logs": str(project_root / "data" / "logs"),
        "filtered_subjects": str(project_root / "data" / "processed" / "filtered_subjects.txt"),
        "hcp_behavioral_csv": str(project_root / "data" / "raw" / "behavioral" / "hcp1200_behavioral_data.csv"),
    }

def ensure_dirs(*paths: str) -> None:
    """
    Ensure that the given directories exist.
    
    Args:
        *paths: Directory paths to ensure exist.
    """
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def get_hyperparameter(name: str, default: Any = None) -> Any:
    """
    Get a hyperparameter value from environment variables or config.
    
    Args:
        name: Name of the hyperparameter.
        default: Default value if not found.
        
    Returns:
        The hyperparameter value.
    """
    # Check environment variable first
    env_val = os.environ.get(f"HYP_{name.upper()}")
    if env_val is not None:
        # Try to convert to appropriate type
        try:
            if '.' in env_val:
                return float(env_val)
            return int(env_val)
        except ValueError:
            return env_val
    
    # Default hardcoded values for the pipeline
    defaults = {
        "variance_threshold": 0.01,
        "pca_retention": 0.95,
        "subset_size": 100,
        "max_fd": 0.3,
        "n_splits": 5,
        "time_budget_seconds": 10800,  # 3 hours
    }
    
    return defaults.get(name, default)
