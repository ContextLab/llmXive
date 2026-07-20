import os
from typing import Optional, Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Load base configuration from environment variables with defaults.

    Returns a dictionary containing:
    - DATA_URL: The URL for the primary data source (default: None, must be set)
    - RANDOM_SEED: Random seed for reproducibility (default: 42)
    - LOG_LEVEL: Logging level for the application (default: 'INFO')
    """
    config: Dict[str, Any] = {}

    # DATA_URL: No default; must be provided via environment variable
    data_url = os.getenv("DATA_URL")
    if data_url is None:
        raise ValueError(
            "Environment variable DATA_URL is not set. "
            "Please set DATA_URL to the verified data source URL."
        )
    config["DATA_URL"] = data_url

    # RANDOM_SEED: Default to 42
    random_seed_str = os.getenv("RANDOM_SEED", "42")
    try:
        config["RANDOM_SEED"] = int(random_seed_str)
    except ValueError:
        raise ValueError(
            f"RANDOM_SEED environment variable must be an integer, got: {random_seed_str}"
        )

    # LOG_LEVEL: Default to 'INFO'
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        raise ValueError(
            f"Invalid LOG_LEVEL: {log_level}. Must be one of {valid_levels}"
        )
    config["LOG_LEVEL"] = log_level

    return config
