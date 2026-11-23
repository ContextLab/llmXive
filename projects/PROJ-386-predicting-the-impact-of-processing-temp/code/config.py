import os
import random
from pathlib import Path
from typing import Dict, Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_STATE_DIR = STATE_DIR / "projects"

# Ensure directories exist
def ensure_dirs():
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_ARTIFACTS_DIR, STATE_DIR, PROJECT_STATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Configuration
CONFIG = {
    "GITHUB_ACTIONS_TIMEOUT": 5 * 3600,  # 5 hours in seconds
    "RANDOM_SEED": 42,
    "DATASET_URLS": [
        # Placeholder - actual URLs should be configured or fetched from environment
        # In a real scenario, these would be populated by T044/T013
        "https://example.com/dataset.csv" 
    ],
    "HYPERPARAMETER_GRIDS": {
        "rf": {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20],
            "min_samples_split": [2, 5]
        },
        "baseline": {
            "fit_intercept": [True, False]
        }
    }
}

def set_global_seed(seed: int = None):
    if seed is None:
        seed = CONFIG.get("RANDOM_SEED", 42)
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds would be set in their respective modules

def get_config() -> Dict[str, Any]:
    return CONFIG

# Initialize directories on import
ensure_dirs()
set_global_seed()