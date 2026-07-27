"""
Module: config

Purpose:
    Manages project configuration, seed management, and path resolution.
    This module centralizes access to project root and configuration files.

Functions:
    - get_project_root: Returns the project root directory.
    - get_path: Resolves a path relative to the project root.
    - ensure_dir: Ensures a directory exists.
    - set_seed: Sets the random seed for reproducibility.
    - get_config: Loads and returns the configuration dictionary.
    - main: Entry point for the script.
"""
import os
import random
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

def get_project_root() -> Path:
    """
    Returns the project root directory.

    Returns:
        Path: The project root path.
    """
    return Path(__file__).resolve().parents[2]

def get_path(key: str, default: Optional[str] = None) -> Path:
    """
    Resolves a path relative to the project root using config.

    Args:
        key (str): Key in config file.
        default (Optional[str]): Default path if key not found.

    Returns:
        Path: Resolved path.
    """
    config = get_config()
    path_str = config.get(key, default)
    if path_str is None:
        raise KeyError(f"Configuration key '{key}' not found.")
    return get_project_root() / path_str

def ensure_dir(path: Path):
    """
    Ensures a directory exists, creating it if necessary.

    Args:
        path (Path): Path to the directory.
    """
    path.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int):
    """
    Sets the random seed for reproducibility.

    Args:
        seed (int): The seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config() -> Dict[str, Any]:
    """
    Loads and returns the configuration dictionary.

    Returns:
        Dict[str, Any]: Configuration data.
    """
    config_path = get_project_root() / "config.json"
    if not config_path.exists():
        # Return a default config if file missing for safety
        return {
            "data": {
                "videokr_sft_filename": "videokr_sft.csv",
                "knowledge_graph_filename": "knowledge_graph.json"
            }
        }
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    """
    Main entry point for the config script.
    Prints current configuration.
    """
    config = get_config()
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()
