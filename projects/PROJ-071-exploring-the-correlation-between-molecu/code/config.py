"""
Configuration management for the pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def get_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml or return defaults.
    """
    # Default configuration
    config = {
        "project_root": str(Path(__file__).parent.parent),
        "data_dir": str(Path(__file__).parent.parent / "data"),
        "code_dir": str(Path(__file__).parent),
        "results_dir": str(Path(__file__).parent.parent / "results"),
    }

    # Try to load from config.yaml if it exists
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            custom_config = yaml.safe_load(f)
            if custom_config:
                config.update(custom_config)

    return config

def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    """
    config = get_config()
    dirs = [
        config["data_dir"],
        config["data_dir"] + "/raw",
        config["data_dir"] + "/processed",
        config["data_dir"] + "/output",
        config["results_dir"],
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)