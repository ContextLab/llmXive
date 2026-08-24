import os
import random
from pathlib import Path
from typing import Dict, Any

# Global configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
ARTIFACTS_MODELS_DIR = PROJECT_ROOT / "artifacts" / "models"
ARTIFACTS_REPORTS_DIR = PROJECT_ROOT / "artifacts" / "reports"
STATE_DIR = PROJECT_ROOT / "state"
TESTS_DIR = PROJECT_ROOT / "tests"

# Random seed
GLOBAL_SEED = 42

def ensure_dirs():
    """
    Ensures all required directories exist.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_ARTIFACTS_DIR,
        ARTIFACTS_MODELS_DIR,
        ARTIFACTS_REPORTS_DIR,
        STATE_DIR,
        TESTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_global_seed(seed: int):
    """
    Sets the global random seed for reproducibility.
    """
    global GLOBAL_SEED
    GLOBAL_SEED = seed
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

# Timeout constants (in seconds)
GITHUB_ACTIONS_TIMEOUT = 5 * 3600  # 5 hours
TRAINING_TIMEOUT = 4 * 3600  # 4 hours
TOTAL_PIPELINE_TIMEOUT = GITHUB_ACTIONS_TIMEOUT

# Runner constraints
MAX_MEMORY_GB = 6.5

# Dataset schema requirements
REQUIRED_COLUMNS = [
    "rolling_temperature",
    "grain_size",
    "composition",
    "process_type"
]

# Model output schema
MODEL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "model_type": {"type": "string"},
        "metrics": {
            "type": "object",
            "properties": {
                "r2": {"type": "number"},
                "mae": {"type": "number"},
                "rmse": {"type": "number"}
            }
        },
        "parameters": {"type": "object"}
    }
}

# Hyperparameter grids for modeling tasks
HYPERPARAMETER_GRIDS = {
    "linear_regression": {
        "fit_intercept": [True, False]
    },
    "random_forest": {
        "n_estimators": [100, 200],
        "max_depth": [10, 20, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "random_state": [GLOBAL_SEED]
    },
    "ridge_regression": {
        "alpha": [0.1, 1.0, 10.0],
        "fit_intercept": [True, False]
    }
}

def get_config() -> Dict[str, Any]:
    """
    Returns the current configuration dictionary.
    """
    return {
        "paths": {
            "raw": str(DATA_RAW_DIR),
            "processed": str(DATA_PROCESSED_DIR),
            "artifacts": str(DATA_ARTIFACTS_DIR),
            "models": str(ARTIFACTS_MODELS_DIR),
            "reports": str(ARTIFACTS_REPORTS_DIR),
            "state": str(STATE_DIR)
        },
        "seed": GLOBAL_SEED,
        "timeout": {
            "training": TRAINING_TIMEOUT,
            "pipeline": TOTAL_PIPELINE_TIMEOUT,
            "github_actions": GITHUB_ACTIONS_TIMEOUT
        },
        "constraints": {
            "max_memory_gb": MAX_MEMORY_GB
        },
        "hyperparameter_grids": HYPERPARAMETER_GRIDS
    }