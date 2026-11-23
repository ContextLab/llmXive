"""
Environment configuration and management for the llmXive pipeline.

This module centralizes access to environment variables (like OPENNEURO_API_KEY)
and provides utilities for resolving project paths.
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default relative paths from project root
DEFAULT_PATHS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "results": "results",
    "code": "code",
    "tests": "tests",
    "figures": "results/plots",
    "config": "code/config.yaml",
}

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Looks for the PROJECT_ROOT environment variable first.
    If not set, assumes the current working directory is the project root.
    
    Returns:
        Path: The absolute path to the project root.
    """
    root_env = os.getenv("PROJECT_ROOT")
    if root_env:
        root = Path(root_env)
        if not root.is_absolute():
            root = Path.cwd() / root
    else:
        root = Path.cwd()
    
    if not root.exists():
        raise FileNotFoundError(f"Project root directory not found: {root}")
    
    logger.debug(f"Project root identified at: {root}")
    return root.resolve()

def get_openneuro_api_key() -> str:
    """
    Retrieve the OpenNeuro API key from environment variables.
    
    Checks for 'OPENNEURO_API_KEY'. If not found, raises a clear error
    instructing the user to set the variable.
    
    Returns:
        str: The API key.
        
    Raises:
        ValueError: If the API key is not set in the environment.
    """
    key = os.getenv("OPENNEURO_API_KEY")
    if not key:
        raise ValueError(
            "OPENNEURO_API_KEY environment variable is not set. "
            "Please export OPENNEURO_API_KEY='your_key_here' before running the pipeline."
        )
    logger.debug("OpenNeuro API key loaded from environment.")
    return key

def get_path(name: str, relative_to: Optional[Path] = None) -> Path:
    """
    Resolve a named path relative to the project root.
    
    Args:
        name: The key name from DEFAULT_PATHS (e.g., 'data_raw', 'results').
        relative_to: Optional base path. Defaults to get_project_root().
        
    Returns:
        Path: The resolved absolute path.
        
    Raises:
        KeyError: If the path name is not defined in DEFAULT_PATHS.
    """
    if relative_to is None:
        relative_to = get_project_root()
    
    if name not in DEFAULT_PATHS:
        raise KeyError(f"Path name '{name}' not found in DEFAULT_PATHS. Available: {list(DEFAULT_PATHS.keys())}")
    
    path_str = DEFAULT_PATHS[name]
    return (relative_to / path_str).resolve()

def ensure_directory(path: Optional[Path] = None, name: Optional[str] = None) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Explicit Path object to ensure.
        name: Name of the path to resolve from DEFAULT_PATHS (used if path is None).
        
    Returns:
        Path: The absolute path to the directory.
        
    Raises:
        ValueError: If neither path nor name is provided.
    """
    if path is None:
        if name is None:
            raise ValueError("Must provide either 'path' or 'name' to ensure_directory.")
        path = get_path(name)
    
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path

def validate_environment() -> None:
    """
    Validate that all critical environment variables and paths are set.
    
    Performs a check on:
    - OPENNEURO_API_KEY
    - Project root existence
    
    Raises:
        ValueError: If validation fails.
    """
    logger.info("Validating environment configuration...")
    
    # Check API key
    try:
        get_openneuro_api_key()
        logger.info("✓ OPENNERO_API_KEY is set.")
    except ValueError as e:
        logger.error(f"✗ Environment Validation Failed: {e}")
        raise
    
    # Check project root
    try:
        root = get_project_root()
        logger.info(f"✓ Project root exists: {root}")
    except FileNotFoundError as e:
        logger.error(f"✗ Environment Validation Failed: {e}")
        raise
    
    # Check required directories exist (create if missing, but log)
    required_dirs = ["data_raw", "data_processed", "results", "code", "tests"]
    for dir_name in required_dirs:
        try:
            ensure_directory(name=dir_name)
            logger.debug(f"  - {dir_name}: OK")
        except Exception as e:
            logger.warning(f"  - {dir_name}: Could not ensure ({e})")
    
    logger.info("Environment validation complete.")

def main():
    """
    CLI entry point to validate environment and print configuration.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    try:
        validate_environment()
        print("\nConfiguration Summary:")
        print(f"  Project Root: {get_project_root()}")
        print(f"  Data Raw:     {get_path('data_raw')}")
        print(f"  Data Processed: {get_path('data_processed')}")
        print(f"  Results:      {get_path('results')}")
        print(f"  API Key Set:  {'Yes' if os.getenv('OPENNEURO_API_KEY') else 'No'}")
        print("\nEnvironment is ready.")
    except (ValueError, FileNotFoundError) as e:
        print(f"\nError: {e}")
        exit(1)

if __name__ == "__main__":
    main()
