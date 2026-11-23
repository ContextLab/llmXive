import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

logger = logging.getLogger(__name__)

class DataIngestionError(Exception):
    pass

class ModelTrainingError(Exception):
    pass

class AnalysisError(Exception):
    pass

SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15
MAX_TRIALS = 60
TRIAL_TIMEOUT = 300

DATA_PATHS = {
    "raw": "data/raw",
    "processed": "data/processed",
    "validation": "data/validation"
}

HYPERPARAM_BOUNDS = {
    "learning_rate": (0.01, 0.3),
    "max_depth": (3, 10),
    "n_estimators": (100, 1000)
}

def load_config() -> Dict[str, Any]:
    """Load configuration from environment or defaults."""
    config = {
        "SEED": SEED,
        "TRAIN_RATIO": TRAIN_RATIO,
        "VAL_RATIO": VAL_RATIO,
        "TEST_RATIO": TEST_RATIO,
        "MAX_TRIALS": MAX_TRIALS,
        "TRIAL_TIMEOUT": TRIAL_TIMEOUT,
        "DATA_PATHS": DATA_PATHS,
        "HYPERPARAM_BOUNDS": HYPERPARAM_BOUNDS
    }
    
    # Check for environment overrides
    if os.getenv("SPICE_URL"):
        config["SPICE_URL"] = os.getenv("SPICE_URL")
    if os.getenv("IL_SAPT_URL"):
        config["IL_SAPT_URL"] = os.getenv("IL_SAPT_URL")
        
    # Validate required keys if needed
    required_keys = ["SEED", "DATA_PATHS"]
    for key in required_keys:
        if key not in config:
            raise DataIngestionError(f"Missing required config key: {key}")
            
    return config
