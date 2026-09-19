"""
Configuration settings for the PROJ-386 pipeline.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any

# Base paths relative to project root (code/ is in project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_PATH = PROJECT_ROOT / "data" / "artifacts"
FIGURES_PATH = PROJECT_ROOT / "figures"
STATE_PATH = PROJECT_ROOT / "state"
STATE_PROJECTS_PATH = STATE_PATH / "projects"

# Ensure directories exist
def ensure_dirs():
    """Create all necessary directories if they don't exist."""
    dirs = [
        DATA_RAW_PATH,
        DATA_PROCESSED_PATH,
        ARTIFACTS_PATH,
        FIGURES_PATH,
        STATE_PATH,
        STATE_PROJECTS_PATH
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Global timeout for GitHub Actions
GITHUB_ACTIONS_TIMEOUT = int(os.getenv("GITHUB_ACTIONS_TIMEOUT", 5 * 3600))  # 5 hours default

# Hyperparameter grids
HYPERPARAM_GRIDS = {
    "baseline": {
        "fit_intercept": [True, False],
    },
    "rf": {
        "n_estimators": [50, 100, 200],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
    }
}

def set_global_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_config() -> Dict[str, Any]:
    """Return a dictionary of all configuration values."""
    return {
        "data_raw_path": str(DATA_RAW_PATH),
        "data_processed_path": str(DATA_PROCESSED_PATH),
        "artifacts_path": str(ARTIFACTS_PATH),
        "figures_path": str(FIGURES_PATH),
        "state_path": str(STATE_PATH),
        "github_actions_timeout": GITHUB_ACTIONS_TIMEOUT,
        "hyperparam_grids": HYPERPARAM_GRIDS,
    }
