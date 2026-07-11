"""
Configuration loader for the project.
Reads environment variables with defaults.
"""
import os
from typing import Optional, Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Returns:
        Dictionary containing configuration values.
    """
    return {
        "DATA_URL": os.getenv("DATA_URL", "https://example.com/data"),
        "DATA_PROCESSED_DIR": os.getenv("DATA_PROCESSED_DIR", "data/processed"),
        "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }
