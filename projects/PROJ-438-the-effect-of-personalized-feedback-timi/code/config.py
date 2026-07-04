"""
config.py

Configuration loader for dataset URLs and hyperparameters.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"

def load_config() -> Dict[str, Any]:
    """
    Loads the main configuration file.
    """
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f) or {}

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieves a specific configuration value.
    """
    config = load_config()
    return config.get(key, default)

def generate_default_config() -> Dict[str, Any]:
    """
    Returns a default configuration structure.
    """
    return {
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed"
        },
        "oulad": {
            "url": "https://analyse.kmi.open.ac.uk/open_dataset",
            "min_learners_per_course": 50
        },
        "model": {
            "feedback_thresholds": {
                "immediate": 2.0,
                "delayed": 48.0
            }
        }
    }
