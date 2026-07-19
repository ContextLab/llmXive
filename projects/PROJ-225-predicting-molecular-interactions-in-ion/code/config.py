import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DataIngestionError(Exception):
    """Custom exception for data ingestion errors."""
    pass

class ModelTrainingError(Exception):
    """Custom exception for model training errors."""
    pass

class AnalysisError(Exception):
    """Custom exception for analysis errors."""
    pass

def load_config():
    """Load configuration from environment variables and defaults."""
    config = {
        "SPICE_URL": os.getenv("SPICE_URL", "https://example.com/spice"),
        "IL_SAPT_URL": os.getenv("IL_SAPT_URL", "https://example.com/il-sapt"),
        "IL_THERMO_URL": os.getenv("IL_THERMO_URL", "https://example.com/il-thermo"),
        "DATA_PATHS": {
            "raw": "data/raw",
            "processed": "data/processed",
            "validation": "data/validation"
        },
        "HYPERPARAM_BOUNDS": {
            "max_depth": (3, 10),
            "eta": (0.01, 0.3),
            "gamma": (0, 10)
        },
        "MAX_TRIALS": int(os.getenv("MAX_TRIALS", 60)),
        "TRIAL_TIMEOUT": int(os.getenv("TRIAL_TIMEOUT", 300))
    }
    return config
