"""
Configuration management for the molecular interactions pipeline.
Handles environment variables and default constants.
"""
import os
import logging

# Load environment variables from .env file if present
from dotenv import load_dotenv
load_dotenv()

# Default constants
SEED = 42
MAX_TRIALS = 60
TRIAL_TIMEOUT = 300  # seconds

# Default data paths relative to project root
DATA_PATHS = {
    "raw": "data/raw",
    "processed": "data/processed",
    "validation": "data/validation",
    "models": "models",
    "contracts": "contracts",
    "logs": "logs"
}

# Hyperparameter search bounds for Optuna
HYPERPARAM_BOUNDS = {
    "max_depth": (3, 10),
    "eta": (0.01, 0.3),
    "gamma": (0, 10),
    "min_child_weight": (1, 10),
    "subsample": (0.5, 1.0),
    "colsample_bytree": (0.5, 1.0),
    "reg_alpha": (0, 10),
    "reg_lambda": (0, 10)
}

# Custom exceptions (defined here to be available to config loading and other modules)
class DataIngestionError(Exception):
    """Raised when data ingestion fails."""
    pass

class ModelTrainingError(Exception):
    """Raised when model training fails."""
    pass

class AnalysisError(Exception):
    """Raised when analysis fails."""
    pass

def load_config():
    """
    Loads configuration from .env file if present, otherwise uses defaults.
    Validates required keys.
    
    Returns:
        dict: Configuration dictionary with URLs, paths, and hyperparameters.
        
    Raises:
        DataIngestionError: If required environment variables are missing.
    """
    # Validate required keys
    required_keys = ["SPICE_URL", "IL_SAPT_URL", "IL_THERMO_URL"]
    missing = [key for key in required_keys if not os.getenv(key)]
    
    if missing:
        raise DataIngestionError(f"Missing required environment variables: {missing}")
    
    return {
        "spice_url": os.getenv("SPICE_URL"),
        "il_sapt_url": os.getenv("IL_SAPT_URL"),
        "il_thermo_url": os.getenv("IL_THERMO_URL"),
        "seed": SEED,
        "max_trials": MAX_TRIALS,
        "trial_timeout": TRIAL_TIMEOUT,
        "data_paths": DATA_PATHS,
        "hyperparam_bounds": HYPERPARAM_BOUNDS
    }