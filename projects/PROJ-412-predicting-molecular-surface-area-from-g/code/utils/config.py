"""
Environment and project configuration loader.

This module handles loading configuration from environment variables,
defaulting to sensible project-relative paths if not specified.
"""

import os
from pathlib import Path
import yaml

# Default configuration values
DEFAULT_CONFIG = {
    "project_root": None,  # Will be derived from __file__
    "data_dir": "data",
    "results_dir": "results",
    "log_level": "INFO",
    "seed": 42,
}

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Assumes the project structure is:
    project_root/
        code/
            utils/
                config.py
    
    Returns:
        Path: Absolute path to the project root.
    """
    # Start from this file's location
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent.parent
    project_root = code_dir.parent
    
    # Verify it looks like a project root
    if not (project_root / "tasks.md").exists():
        # Fallback: look for tasks.md in parent directories
        for parent in current_file.parents:
            if (parent / "tasks.md").exists():
                return parent
        # If still not found, return the code_dir's parent
        return code_dir.parent
        
    return project_root

def get_data_dir() -> Path:
    """Get the path to the data directory."""
    return get_project_root() / os.getenv("DATA_DIR", DEFAULT_CONFIG["data_dir"])

def get_results_dir() -> Path:
    """Get the path to the results directory."""
    return get_project_root() / os.getenv("RESULTS_DIR", DEFAULT_CONFIG["results_dir"])

def load_env_config(config_path: str = None) -> dict:
    """
    Load configuration from environment variables and optional YAML file.
    
    Priority:
    1. Environment variables
    2. YAML config file (if provided)
    3. Default values
    
    Args:
        config_path: Optional path to a YAML configuration file.
        
    Returns:
        dict: Merged configuration dictionary.
    """
    project_root = get_project_root()
    config = DEFAULT_CONFIG.copy()
    config["project_root"] = str(project_root)
    
    # Load from YAML file if provided
    if config_path:
        yaml_path = Path(config_path)
        if not yaml_path.is_absolute():
            yaml_path = project_root / yaml_path
        
        if yaml_path.exists():
            with open(yaml_path, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
                config.update(yaml_config)
    
    # Override with environment variables
    env_mapping = {
        "DATA_DIR": "data_dir",
        "RESULTS_DIR": "results_dir",
        "LOG_LEVEL": "log_level",
        "SEED": "seed",
    }
    
    for env_var, config_key in env_mapping.items():
        env_val = os.getenv(env_var)
        if env_val is not None:
            # Convert types if necessary
            if config_key == "seed":
                try:
                    config[config_key] = int(env_val)
                except ValueError:
                    pass  # Keep default if invalid
            else:
                config[config_key] = env_val
    
    # Ensure paths are Path objects
    if isinstance(config["data_dir"], str):
        config["data_dir"] = project_root / config["data_dir"]
    if isinstance(config["results_dir"], str):
        config["results_dir"] = project_root / config["results_dir"]
    
    return config
