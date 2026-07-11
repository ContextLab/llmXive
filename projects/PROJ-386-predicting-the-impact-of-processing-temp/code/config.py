import os
import random
from pathlib import Path
from typing import Dict, Any

# Global configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
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
TRAINING_TIMEOUT = 4 * 3600  # 4 hours
TOTAL_PIPELINE_TIMEOUT = 5 * 3600  # 5 hours

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

def get_config() -> Dict[str, Any]:
    """
    Returns the current configuration dictionary.
    """
    return {
        "paths": {
            "raw": str(DATA_RAW_DIR),
            "processed": str(DATA_PROCESSED_DIR),
            "models": str(ARTIFACTS_MODELS_DIR),
            "reports": str(ARTIFACTS_REPORTS_DIR),
            "state": str(STATE_DIR)
        },
        "seed": GLOBAL_SEED,
        "timeout": {
            "training": TRAINING_TIMEOUT,
            "pipeline": TOTAL_PIPELINE_TIMEOUT
        },
        "constraints": {
            "max_memory_gb": MAX_MEMORY_GB
        }
    }