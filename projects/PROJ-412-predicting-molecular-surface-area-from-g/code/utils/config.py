"""
Configuration utilities for the project.
"""
import os
from pathlib import Path
import yaml

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Assumes the code is run from the project root or a subdirectory.
    """
    # Look for a marker file or assume the parent of 'code' is root
    current = Path(__file__).resolve()
    # Traverse up until we find a directory that looks like root
    # A simple heuristic: the directory containing 'code', 'data', 'tests'
    parent = current.parent.parent
    if (parent / "code").exists() and (parent / "data").exists() and (parent / "tests").exists():
        return parent
    # Fallback to current working directory
    return Path.cwd()

def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_results_dir() -> Path:
    """Returns the path to the results directory."""
    return get_project_root() / "results"

def load_env_config(config_path: str = None):
    """
    Loads configuration from a YAML file or environment variables.
    """
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}
