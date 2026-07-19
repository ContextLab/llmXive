"""
Configuration module for the project.
Handles loading environment variables and defining constants.
"""
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom Exception Hierarchy
class DataIngestionError(Exception):
    """Raised when data ingestion fails."""
    pass

class ModelTrainingError(Exception):
    """Raised when model training fails."""
    pass

class AnalysisError(Exception):
    """Raised when analysis fails."""
    pass

# Default Configuration
SEED = 42
MAX_TRIALS = 60
TRIAL_TIMEOUT = 300  # seconds
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Default Data Paths
DATA_PATHS = {
    "SPICE_URL": os.getenv("SPICE_URL", "https://huggingface.co/datasets/SPICE-IL/SPICE-IL/resolve/main/train.parquet"),
    "IL_SAPT_URL": os.getenv("IL_SAPT_URL", ""),
    "DFT_VALIDATION_URL": os.getenv("DFT_VALIDATION_URL", ""),
    "ILTHERMO_URL": os.getenv("ILTHERMO_URL", "")
}

# Hyperparameter Bounds for Optuna
HYPERPARAM_BOUNDS = {
    "max_depth": (3, 10),
    "eta": (0.01, 0.3),
    "gamma": (0, 1),
    "subsample": (0.6, 1.0),
    "colsample_bytree": (0.6, 1.0),
    "min_child_weight": (1, 10),
    "reg_alpha": (0, 10),
    "reg_lambda": (0, 10)
}

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.
    
    Returns:
        Dictionary containing configuration.
        
    Raises:
        DataIngestionError: If required environment variables are missing.
    """
    # Validate required keys
    required_keys = ["SPICE_URL"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        # Allow defaults for some, but log warning
        logger.warning(f"Missing environment variables (using defaults where possible): {missing_keys}")
    
    config = {
        "SEED": int(os.getenv("SEED", SEED)),
        "MAX_TRIALS": int(os.getenv("MAX_TRIALS", MAX_TRIALS)),
        "TRIAL_TIMEOUT": int(os.getenv("TRIAL_TIMEOUT", TRIAL_TIMEOUT)),
        "TRAIN_RATIO": float(os.getenv("TRAIN_RATIO", TRAIN_RATIO)),
        "VAL_RATIO": float(os.getenv("VAL_RATIO", VAL_RATIO)),
        "TEST_RATIO": float(os.getenv("TEST_RATIO", TEST_RATIO)),
        "DATA_PATHS": DATA_PATHS,
        "HYPERPARAM_BOUNDS": HYPERPARAM_BOUNDS
    }
    
    return config
