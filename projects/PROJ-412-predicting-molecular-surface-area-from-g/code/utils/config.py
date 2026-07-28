import os
from pathlib import Path
import yaml

def get_project_root():
    """
    Returns the root directory of the project.
    Assumes the project root is two levels up from this file (code/utils/).
    """
    return Path(__file__).resolve().parent.parent.parent

def get_data_dir():
    """
    Returns the path to the data directory.
    """
    return get_project_root() / "data"

def get_results_dir():
    """
    Returns the path to the results directory.
    """
    return get_project_root() / "results"

def load_env_config():
    """
    Loads configuration from a config.yaml file if it exists, otherwise returns defaults.
    """
    config_path = get_project_root() / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}