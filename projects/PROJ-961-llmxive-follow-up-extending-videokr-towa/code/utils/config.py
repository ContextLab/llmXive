"""
Configuration management module for the llmXive pipeline.
Handles seed management, path configuration, and project settings.
"""
import os
import random
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Default configuration
DEFAULT_SEED = 42
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: The project root directory.
    """
    return PROJECT_ROOT


def get_path(relative_path: str) -> Path:
    """
    Get an absolute path relative to the project root.
    
    Args:
        relative_path (str): Relative path from project root.
        
    Returns:
        Path: Absolute path.
    """
    return PROJECT_ROOT / relative_path


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
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_seed(seed_name: str = 'default') -> int:
    """
    Get a seed value for a specific operation.
    
    Args:
        seed_name (str): Name of the seed operation.
        
    Returns:
        int: Seed value.
    """
    config = get_config()
    seeds = config.get('seeds', {})
    return seeds.get(seed_name, DEFAULT_SEED)


def get_config() -> Dict[str, Any]:
    """
    Load and return the project configuration.
    
    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def main() -> None:
    """Main entry point for configuration module."""
    logger = logging.getLogger(__name__)
    logger.info(f"Project root: {get_project_root()}")
    logger.info(f"Default seed: {get_seed()}")


if __name__ == "__main__":
    import logging
    main()
