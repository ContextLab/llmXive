"""
Environment variable management and local path resolution for the llmXive pipeline.

This module handles:
1. Loading and validating the OPENNEURO_API_KEY environment variable.
2. Resolving local paths relative to the project root.
3. Providing a central configuration interface for path-based operations.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)

# Project root is two levels up from this file (code/ -> projects/PROJ-118/ -> root)
# However, standard convention for this project is that code/ is at root level.
# Let's determine the project root dynamically based on the presence of known directories.
_PROJECT_ROOT = None

def _find_project_root() -> Path:
    """
    Dynamically locate the project root by searching for known directories.
    Starts from the current file's directory and moves up.
    """
    current = Path(__file__).resolve()
    # Search up to 5 levels
    for _ in range(5):
        if (current / "data").exists() and (current / "code").exists():
            return current
        current = current.parent
    # Fallback: assume current working directory is project root
    return Path.cwd()

def get_project_root() -> Path:
    """Returns the project root path."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        _PROJECT_ROOT = _find_project_root()
    return _PROJECT_ROOT

def get_openneuro_api_key() -> str:
    """
    Retrieves the OPENNEURO_API_KEY from the environment.
    
    Raises:
        RuntimeError: If the API key is not set.
    
    Returns:
        str: The API key string.
    """
    api_key = os.getenv("OPENNEURO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENNEURO_API_KEY environment variable is not set. "
            "Please set it before running the download pipeline. "
            "Example: export OPENNEURO_API_KEY='your_key_here'"
        )
    return api_key

def get_path(key: str) -> Path:
    """
    Resolves a logical path key to an absolute Path object.
    
    Args:
        key (str): Logical key (e.g., 'raw_data', 'processed_data', 'results').
    
    Returns:
        Path: Absolute path to the resource.
    
    Raises:
        ValueError: If the key is not recognized.
    """
    root = get_project_root()
    path_map = {
        "raw_data": root / "data" / "raw",
        "processed_data": root / "data" / "processed",
        "results": root / "results",
        "code": root / "code",
        "tests": root / "tests",
        "figures": root / "results" / "plots",
        "config": root / "code" / "config.yaml",
        "metrics": root / "results" / "metrics.csv",
        "stats": root / "results" / "statistics.json",
        "rejected_log": root / "data" / "processed" / "rejected_participants.log",
    }
    
    if key not in path_map:
        raise ValueError(f"Unknown path key: {key}. Available keys: {list(path_map.keys())}")
    
    return path_map[key]

def ensure_directory(path_key: str) -> Path:
    """
    Ensures the directory for a given path key exists, creating it if necessary.
    
    Args:
        path_key (str): Logical key for the directory.
    
    Returns:
        Path: The absolute path to the directory.
    """
    path = get_path(path_key)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path

def get_config() -> Dict[str, Any]:
    """
    Loads the configuration file if it exists.
    
    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    import yaml
    config_path = get_path("config")
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}. Returning empty dict.")
        return {}
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}

def validate_environment() -> bool:
    """
    Validates that all critical environment variables and paths are set.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        _ = get_openneuro_api_key()
        _ = get_project_root()
        # Ensure critical directories exist
        ensure_directory("raw_data")
        ensure_directory("processed_data")
        ensure_directory("results")
        return True
    except RuntimeError as e:
        logger.error(f"Environment validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during environment validation: {e}")
        return False

# Utility for scripts that need a quick check
def main():
    """Simple CLI entry point to validate environment."""
    if validate_environment():
        print("Environment validation successful.")
        print(f"Project Root: {get_project_root()}")
        print(f"Raw Data Path: {get_path('raw_data')}")
        print(f"Processed Data Path: {get_path('processed_data')}")
        try:
            key = get_openneuro_api_key()
            print(f"API Key found (length: {len(key)}).")
        except RuntimeError as e:
            print(f"API Key error: {e}")
    else:
        print("Environment validation failed.")
        exit(1)

if __name__ == "__main__":
    main()