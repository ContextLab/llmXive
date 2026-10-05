"""
Configuration management for the Crystal Structure Prediction project.

Handles paths, seeds, and runtime configuration.
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
VALIDATION_DIR = DATA_DIR / "validation"
MODELS_DIR = DATA_DIR / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
FIGURES_DIR = DATA_DIR / "figures"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"
RAW_DIR = DATA_DIR / "raw"

# Seeds
DEFAULT_SEED = 42

def get_project_root() -> Path:
    """Returns the project root directory."""
    return PROJECT_ROOT

def get_path_absolute(*parts: Union[str, Path]) -> Path:
    """Returns an absolute path constructed from parts."""
    return PROJECT_ROOT / Path(*parts)

def get_path_relative(*parts: Union[str, Path]) -> Path:
    """Returns a path relative to the project root."""
    return Path(*parts)

def ensure_directory(path: Union[str, Path]) -> None:
    """Creates a directory if it does not exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)

def get_path_data(subpath: Optional[str] = None) -> Path:
    """Returns the data directory or a subpath within it."""
    if subpath:
        return DATA_DIR / subpath
    return DATA_DIR

def get_path_processed_data(filename: Optional[str] = None) -> Path:
    """
    Returns the processed data directory or a specific file within it.
    
    This function has been updated to accept an optional filename argument
    to satisfy the API contract required by multiple scripts (split.py, 
    validate_split.py, interpret.py, etc.).
    
    Args:
        filename: Optional filename to append to the processed directory.
                  If None, returns the directory path.
    
    Returns:
        Path: The path to the directory or the specific file.
    """
    if filename is None:
        return PROCESSED_DIR
    return PROCESSED_DIR / filename

def get_path_results(filename: Optional[str] = None) -> Path:
    """Returns the results directory or a specific file within it."""
    if filename is None:
        return RESULTS_DIR
    return RESULTS_DIR / filename

def get_path_validation(filename: Optional[str] = None) -> Path:
    """Returns the validation directory or a specific file within it."""
    if filename is None:
        return VALIDATION_DIR
    return VALIDATION_DIR / filename

def get_path_models(filename: Optional[str] = None) -> Path:
    """Returns the models directory or a specific file within it."""
    if filename is None:
        return MODELS_DIR
    return MODELS_DIR / filename

def get_path_logs(filename: Optional[str] = None) -> Path:
    """Returns the logs directory or a specific file within it."""
    if filename is None:
        return LOGS_DIR
    return LOGS_DIR / filename

def get_path_figures(filename: Optional[str] = None) -> Path:
    """Returns the figures directory or a specific file within it."""
    if filename is None:
        return FIGURES_DIR
    return FIGURES_DIR / filename

def get_path_code(filename: Optional[str] = None) -> Path:
    """Returns the code directory or a specific file within it."""
    if filename is None:
        return CODE_DIR
    return CODE_DIR / filename

def get_path_tests(filename: Optional[str] = None) -> Path:
    """Returns the tests directory or a specific file within it."""
    if filename is None:
        return TESTS_DIR
    return TESTS_DIR / filename

def get_path_specs(filename: Optional[str] = None) -> Path:
    """Returns the specs directory or a specific file within it."""
    if filename is None:
        return SPECS_DIR
    return SPECS_DIR / filename

def get_path_raw_data(filename: Optional[str] = None) -> Path:
    """Returns the raw data directory or a specific file within it."""
    if filename is None:
        return RAW_DIR
    return RAW_DIR / filename

def get_config_dict() -> Dict[str, Any]:
    """Returns a dictionary of the current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "results_dir": str(RESULTS_DIR),
        "validation_dir": str(VALIDATION_DIR),
        "models_dir": str(MODELS_DIR),
        "logs_dir": str(LOGS_DIR),
        "figures_dir": str(FIGURES_DIR),
        "seed": DEFAULT_SEED
    }

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def load_runtime_config() -> Dict[str, Any]:
    """Loads the runtime configuration from data/results/runtime_config.json."""
    runtime_config_path = RESULTS_DIR / "runtime_config.json"
    if runtime_config_path.exists():
        with open(runtime_config_path, 'r') as f:
            return json.load(f)
    return {}

def save_runtime_config(config: Dict[str, Any]) -> None:
    """Saves the runtime configuration to data/results/runtime_config.json."""
    ensure_directory(RESULTS_DIR)
    runtime_config_path = RESULTS_DIR / "runtime_config.json"
    with open(runtime_config_path, 'w') as f:
        json.dump(config, f, indent=4)

def create_parser() -> Any:
    """Creates an argument parser for the CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Crystal Structure Prediction Pipeline")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--sample-size", type=int, default=None, help="Sample size for testing")
    return parser

def main():
    """Main entry point for config module (for testing)."""
    print("Configuration loaded successfully.")
    print(get_config_dict())

if __name__ == "__main__":
    main()