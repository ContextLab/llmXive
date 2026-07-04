"""
Configuration loader for the gut microbiome and sleep quality study.
Reads environment variables with sensible defaults.
"""
import os
from typing import Any, Dict


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Returns:
        Dict containing:
            - DATA_URL: URL for the data source (default: None, must be set for real data)
            - RANDOM_SEED: Integer seed for reproducibility (default: 42)
            - LOG_LEVEL: Logging level string (default: 'INFO')
    """
    return {
        "DATA_URL": os.getenv("DATA_URL"),
        "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }