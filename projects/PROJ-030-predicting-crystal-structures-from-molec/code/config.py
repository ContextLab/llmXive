"""
Module: code/config.py

Purpose:
Configuration management for paths, seeds, and hyperparameters.
Provides utility functions to retrieve absolute and relative paths.
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default paths relative to project root
PATHS = {
    "data": "data",
    "raw": "data/raw",
    "processed": "data/processed",
    "results": "data/results",
    "validation": "data/validation",
    "models": "data/models",
    "logs": "logs",
    "figures": "figures",
    "code": "code",
    "tests": "tests",
    "specs": "specs"
}

# Default seed
DEFAULT_SEED = 42

def get_project_root() -> Path:
    """Returns the project root directory."""
    return PROJECT_ROOT

def get_path_absolute(relative_path: str) -> Path:
    """Returns an absolute path given a relative path from project root."""
    return PROJECT_ROOT / relative_path

def get_path_relative(relative_path: str) -> Path:
    """Returns a path relative to the project root (as a Path object)."""
    return Path(relative_path)

def get_path_data() -> Path:
    """Returns the data directory."""
    return get_path_absolute(PATHS["data"])

def get_path_raw_data() -> Path:
    """Returns the raw data directory."""
    return get_path_absolute(PATHS["raw"])

def get_path_processed_data(filename: Optional[str] = None) -> Path:
    """
    Returns the processed data directory or a specific file path within it.
    
    Args:
        filename (Optional[str]): The name of the file. If None, returns the directory.
        
    Returns:
        Path: The directory path if filename is None, otherwise the full file path.
    """
    base = get_path_absolute(PATHS["processed"])
    if filename:
        return base / filename
    return base

def get_path_results() -> Path:
    """Returns the results directory."""
    return get_path_absolute(PATHS["results"])

def get_path_validation() -> Path:
    """Returns the validation directory."""
    return get_path_absolute(PATHS["validation"])

def get_path_models() -> Path:
    """Returns the models directory."""
    return get_path_absolute(PATHS["models"])

def get_path_logs() -> Path:
    """Returns the logs directory."""
    return get_path_absolute(PATHS["logs"])

def get_path_figures() -> Path:
    """Returns the figures directory."""
    return get_path_absolute(PATHS["figures"])

def get_path_code() -> Path:
    """Returns the code directory."""
    return get_path_absolute(PATHS["code"])

def get_path_tests() -> Path:
    """Returns the tests directory."""
    return get_path_absolute(PATHS["tests"])

def get_path_specs() -> Path:
    """Returns the specs directory."""
    return get_path_absolute(PATHS["specs"])

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensures the directory exists. Creates it if it doesn't.
    
    Args:
        path (Union[str, Path]): The path to ensure exists.
        
    Returns:
        Path: The path object.
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def set_seed(seed: int = DEFAULT_SEED):
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_runtime_config_path() -> Path:
    """Returns the path to the runtime configuration file."""
    return get_path_results() / "runtime_config.json"

def load_runtime_config() -> Dict[str, Any]:
    """Loads the runtime configuration from disk."""
    path = get_runtime_config_path()
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_runtime_config(config: Dict[str, Any]):
    """Saves the runtime configuration to disk."""
    path = get_runtime_config_path()
    ensure_directory(path)
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)

def get_config_dict() -> Dict[str, Any]:
    """Returns a dictionary of all path configurations."""
    return {
        "project_root": str(PROJECT_ROOT),
        "data": str(get_path_data()),
        "raw": str(get_path_raw_data()),
        "processed": str(get_path_processed_data()),
        "results": str(get_path_results()),
        "validation": str(get_path_validation()),
        "models": str(get_path_models()),
        "logs": str(get_path_logs()),
        "figures": str(get_path_figures())
    }

def create_parser() -> argparse.ArgumentParser:
    """Creates an argument parser with common arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Project Configuration Parser")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--output_dir", type=str, help="Output directory override")
    return parser

def main():
    """Main entry point for CLI testing."""
    import argparse
    parser = create_parser()
    args = parser.parse_args()
    set_seed(args.seed)
    print(f"Project Root: {get_project_root()}")
    print(f"Config: {get_config_dict()}")

if __name__ == "__main__":
    main()