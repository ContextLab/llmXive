import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

CONFIG_FILE = "config.yaml"

def get_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    Uses relative paths based on project root to avoid hardcoding.
    """
    if config_file is None:
        config_file = CONFIG_FILE
    
    config_path = Path(config_file)
    if not config_path.exists():
        # Default configuration
        return {
            "data_dir": "data",
            "code_dir": "code",
            "output_dir": "data/outputs",
            "log_level": "INFO"
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure paths are relative to project root
    if "data_dir" in config:
        config["data_dir"] = str(Path(config["data_dir"]).resolve().relative_to(Path.cwd().parent) if Path(config["data_dir"]).is_absolute() else config["data_dir"])
    
    return config

def ensure_directories(config: Optional[Dict[str, Any]] = None):
    """
    Create necessary directories based on configuration.
    """
    if config is None:
        config = get_config()
    
    directories = [
        config.get("data_dir", "data"),
        os.path.join(config.get("data_dir", "data"), "raw"),
        os.path.join(config.get("data_dir", "data"), "processed"),
        os.path.join(config.get("data_dir", "data"), "output"),
        config.get("output_dir", "data/outputs")
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
