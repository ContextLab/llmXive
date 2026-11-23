"""
Environment configuration management for the GFA pipeline.

This module manages environment variables including random seeds and paths.
It provides a central `load_config()` function to validate and load configuration.

Note: The dataset URL is a fixed constant per spec assumptions and is NOT stored
in this config file (see code/config/environment.py for runtime environment handling).
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Fixed constants per spec assumptions (NOT stored in config)
# The dataset URL is a fixed constant per spec assumptions.
DATASET_URL = "https://huggingface.co/datasets/GFA-D2/pilot_flags"
DATASET_REPOSITORY = "GFA-D2/pilot_flags"

# Required environment keys
REQUIRED_KEYS = {
    "RANDOM_SEED": int,
    "PROJECT_ROOT": str,
    "DATA_RAW_DIR": str,
    "DATA_PROCESSED_DIR": str,
    "STATE_DIR": str,
    "OUTPUT_DIR": str,
}

DEFAULT_VALUES = {
    "RANDOM_SEED": 42,
    "PROJECT_ROOT": str(Path(__file__).parent.parent.parent),
    "DATA_RAW_DIR": "data/raw",
    "DATA_PROCESSED_DIR": "data/processed",
    "STATE_DIR": "state",
    "OUTPUT_DIR": "output",
}


def _resolve_path(base: Path, path_str: str) -> Path:
    """Resolve a path string relative to the base directory if it's not absolute."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return base / p


def load_config() -> Dict[str, Any]:
    """
    Load and validate environment configuration.

    Reads environment variables, applies defaults, validates types, and returns
    a configuration dictionary.

    Returns:
        Dict[str, Any]: Validated configuration dictionary with keys:
            - random_seed (int)
            - paths (Dict[str, Path]): Contains project_root, data_raw, data_processed, state, output
            - dataset_url (str): Fixed constant from spec assumptions

    Raises:
        ConfigurationError: If required keys are missing or have invalid types.
    """
    from utils.logger import get_logger, ConfigurationError

    logger = get_logger(__name__)

    config: Dict[str, Any] = {}

    # Load random seed
    seed_str = os.getenv("RANDOM_SEED", str(DEFAULT_VALUES["RANDOM_SEED"]))
    try:
        config["random_seed"] = int(seed_str)
    except ValueError:
        raise ConfigurationError(f"RANDOM_SEED must be an integer, got: {seed_str}")

    # Initialize paths relative to project root
    project_root_str = os.getenv("PROJECT_ROOT", DEFAULT_VALUES["PROJECT_ROOT"])
    project_root = Path(project_root_str).resolve()

    config["paths"] = {
        "project_root": project_root,
        "data_raw": _resolve_path(project_root, os.getenv("DATA_RAW_DIR", DEFAULT_VALUES["DATA_RAW_DIR"])),
        "data_processed": _resolve_path(project_root, os.getenv("DATA_PROCESSED_DIR", DEFAULT_VALUES["DATA_PROCESSED_DIR"])),
        "state": _resolve_path(project_root, os.getenv("STATE_DIR", DEFAULT_VALUES["STATE_DIR"])),
        "output": _resolve_path(project_root, os.getenv("OUTPUT_DIR", DEFAULT_VALUES["OUTPUT_DIR"])),
    }

    # Validate that required directories are specified
    for key, expected_type in REQUIRED_KEYS.items():
        if key not in os.environ and key not in DEFAULT_VALUES:
            raise ConfigurationError(f"Required environment key '{key}' is missing and has no default.")

    # Ensure directories exist
    for path_name, path_obj in config["paths"].items():
        path_obj.mkdir(parents=True, exist_ok=True)
        logger.log_info(f"Ensured directory exists: {path_obj}")

    # Add fixed constants
    config["dataset_url"] = DATASET_URL
    config["dataset_repository"] = DATASET_REPOSITORY

    logger.log_info(f"Configuration loaded successfully with random_seed={config['random_seed']}")
    return config


def initialize_random_seeds(seed: Optional[int] = None) -> None:
    """
    Initialize random seeds for reproducibility.

    Args:
        seed: Random seed value. If None, uses value from environment or default 42.
    """
    if seed is None:
        try:
            config = load_config()
            seed = config["random_seed"]
        except ConfigurationError:
            seed = DEFAULT_VALUES["RANDOM_SEED"]

    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def main() -> None:
    """Main entry point for testing configuration loading."""
    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.log_info("Testing configuration loading...")

    try:
        config = load_config()
        logger.log_info(f"Configuration: {config}")
        logger.log_info("Random seeds initialized")
        initialize_random_seeds()
        logger.log_info("SUCCESS: Configuration loaded and seeds initialized")
    except Exception as e:
        logger.log_error(f"FAILED: {e}")
        raise


if __name__ == "__main__":
    main()