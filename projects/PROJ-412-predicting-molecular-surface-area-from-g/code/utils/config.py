import os
from pathlib import Path
import yaml

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the project root is the parent of the 'code' directory.
    """
    current_file = Path(__file__).resolve()
    # Navigate up two levels: code/utils -> code -> project_root
    return current_file.parent.parent

def get_data_dir() -> Path:
    """
    Get the data directory path.
    """
    return get_project_root() / "data"

def get_results_dir() -> Path:
    """
    Get the results directory path.
    """
    return get_project_root() / "results"

def load_env_config(config_path: str = None) -> dict:
    """
    Load environment configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. If None, uses default location.
        
    Returns:
        Dictionary containing configuration.
    """
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    if not Path(config_path).exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}
