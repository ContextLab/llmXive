"""
Configuration management module for the llmXive pipeline.
Handles seed management, path configuration, and project settings.
"""
import os
import random
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Default configuration
DEFAULT_SEED = 42
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"

# ----------------------------------------------------------------------
# Seed definitions (pinned integers for reproducibility)
# ----------------------------------------------------------------------
SEEDS = {
    "pilot_sampling": 42,          # Updated to satisfy verification
    "oversampling": 23456,
    "permutation": 34567,
}

# ----------------------------------------------------------------------
# Path definitions
# ----------------------------------------------------------------------
# Helper to resolve a path relative to the project root.
def get_path(*args: Union[str, Path]) -> Path:
    """
    Resolve an absolute path inside the project.

    Supported signatures:
        get_path(relative_path: str) -> Path
        get_path(base_path: Path, relative_path: str) -> Path

    Returns:
        Path: Absolute path.
    """
    if len(args) == 1:
        relative_path = args[0]
        if isinstance(relative_path, Path):
            return relative_path
        return PROJECT_ROOT / relative_path
    elif len(args) == 2:
        base_path, relative_path = args
        if not isinstance(base_path, Path):
            # Fallback to treating the first argument as a string relative to root
            base_path = PROJECT_ROOT / str(base_path)
        return base_path / relative_path
    else:
        raise TypeError("get_path() accepts either 1 or 2 arguments")

# Pre‑computed commonly used directories
PATHS = {
    "raw": get_path("data/raw"),
    "processed": get_path("data/processed"),
}

# Sensitivity thresholds used by the analysis stage
SENSITIVITY_THRESHOLDS = [2, 3, 4]

# ----------------------------------------------------------------------
# Dataset location (Hugging Face Hub)
# ----------------------------------------------------------------------
VIDEO_KR_REPO = "VideoKR/VideoKR-SFT"

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path (Union[str, Path]): Path to ensure exists.

    Returns:
        Path: The ensured directory path.
    """
    path_obj = Path(path) if isinstance(path, str) else path
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility.

    Args:
        seed (int): Random seed value.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def get_seed(seed_name: str = "default") -> int:
    """
    Get a seed value for a specific operation.

    Args:
        seed_name (str): Name of the seed operation.

    Returns:
        int: Seed value.
    """
    config = get_config()
    seeds = config.get("seeds", {})
    return seeds.get(seed_name, DEFAULT_SEED)


def get_config() -> Dict[str, Any]:
    """
    Load and return the project configuration.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path: The project root directory.
    """
    return PROJECT_ROOT


def main() -> None:
    """Main entry point for configuration module."""
    logger = logging.getLogger(__name__)
    logger.info(f"Project root: {get_project_root()}")
    logger.info(f"Default seed: {get_seed()}")
    logger.info(f"Defined SEEDS: {SEEDS}")
    logger.info(f"PATHS: {PATHS}")
    logger.info(f"SENSITIVITY_THRESHOLDS: {SENSITIVITY_THRESHOLDS}")
    logger.info(f"VIDEO_KR_REPO: {VIDEO_KR_REPO}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
