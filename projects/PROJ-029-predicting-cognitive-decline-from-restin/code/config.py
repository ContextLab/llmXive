"""
Configuration management for the cognitive decline prediction pipeline.

Loads configuration from environment variables and default values.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    "data": {
        "raw": str(Path("data/raw")),
        "processed": str(Path("data/processed")),
        "artifacts": str(Path("data/artifacts"))
    },
    "logs": {
        "dir": str(Path("data/logs")),
        "level": "INFO"
    },
    "random_seed": 42,
    "runtime_limit_seconds": 10800,  # 3 hours
    "memory_limit_gb": 7,
    "max_subjects": 100,
    "atlas": {
        "aal_path": os.getenv("AAL_ATLAS_PATH", "")  # Can be set via environment variable
    },
    "fsl": {
        "enabled": os.getenv("FSL_ENABLED", "true").lower() == "true"
    }
}

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns
    -------
    Dict[str, Any]
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if set
    if os.getenv("DATA_RAW_DIR"):
        config["data"]["raw"] = os.getenv("DATA_RAW_DIR")
    if os.getenv("DATA_PROCESSED_DIR"):
        config["data"]["processed"] = os.getenv("DATA_PROCESSED_DIR")
    if os.getenv("AAL_ATLAS_PATH"):
        config["atlas"]["aal_path"] = os.getenv("AAL_ATLAS_PATH")
    
    return config

# Set up directories
LOG_DIR = Path(DEFAULT_CONFIG["logs"]["dir"])
LOG_LEVEL = DEFAULT_CONFIG["logs"]["level"]
DATA_RAW_DIR = Path(DEFAULT_CONFIG["data"]["raw"])
DATA_PROCESSED_DIR = Path(DEFAULT_CONFIG["data"]["processed"])
DATA_ARTIFACTS_DIR = Path(DEFAULT_CONFIG["data"]["artifacts"])