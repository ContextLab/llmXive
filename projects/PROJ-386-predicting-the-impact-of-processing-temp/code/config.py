"""
Configuration module for the llmXive pipeline.
Defines paths, timeouts, and hyperparameter grids.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_ARTIFACTS_DIR = DATA_DIR / "artifacts"
STATE_DIR = PROJECT_ROOT / "state"
STATE_PROJECTS_DIR = STATE_DIR / "projects"

# Ensure directories exist
def ensure_dirs():
    """Create necessary directories if they don't exist."""
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_ARTIFACTS_DIR, STATE_PROJECTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Global seed
def set_global_seed(seed=42):
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If numpy and torch are available, set their seeds too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# Configuration dictionary
def get_config() -> Dict[str, Any]:
    """
    Return the configuration dictionary.
    Includes paths, timeouts, and hyperparameter grids.
    """
    ensure_dirs()
    set_global_seed()

    # Default dataset URLs (these should be real, verified URLs)
    # For the purpose of this project, we assume these are set correctly.
    # If not, the pipeline will fail with a clear error.
    # We use a placeholder for now, but in a real scenario, these would be NOMAD/OpenML URLs.
    # Example: "https://nomad-laboratory.de/api/v1/..."
    # Since we cannot fabricate data, we rely on the user to set these or use a real source.
    # For T039, we assume the config is set up correctly.
    default_urls = [
        "https://raw.githubusercontent.com/llmXive/data/main/alloy_data.csv" # Placeholder, replace with real URL
    ]

    # If the placeholder is used and no real data is available, the pipeline will fail.
    # This is intentional to prevent fabrication.
    # In a real deployment, these URLs would be replaced with actual data sources.

    config = {
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "code_dir": str(CODE_DIR),
            "data_dir": str(DATA_DIR),
            "data_raw_dir": str(DATA_RAW_DIR),
            "data_processed_dir": str(DATA_PROCESSED_DIR),
            "data_artifacts_dir": str(DATA_ARTIFACTS_DIR),
            "state_dir": str(STATE_DIR),
            "state_projects_dir": str(STATE_PROJECTS_DIR),
        },
        "timeout": {
            "global": int(os.getenv("GITHUB_ACTIONS_TIMEOUT", 18000)), # 5 hours default
        },
        "dataset": {
            "urls": os.getenv("DATASET_URLS", ",".join(default_urls)).split(","),
            "ingestion_output": "data/raw/ingested_data.csv",
        },
        "hyperparameters": {
            "baseline": {
                "fit_intercept": True,
                "normalize": False,
            },
            "rf": {
                "n_estimators": [50, 100, 200],
                "max_depth": [None, 10, 20],
                "min_samples_split": [2, 5],
                "min_samples_leaf": [1, 2],
            }
        }
    }

    return config

# Initialize config on import
ensure_dirs()
set_global_seed()
CONFIG = get_config()