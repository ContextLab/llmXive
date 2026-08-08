"""
config.py

Configuration loader for dataset URLs and hyperparameters.
Loads settings from projects/PROJ-438-the-effect-of-personalized-feedback-timi/config/config.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Determine the project root relative to this file
# Structure: projects/PROJ-438-.../code/config.py
# Config file is at: projects/PROJ-438-.../config/config.yaml
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

def load_config() -> Dict[str, Any]:
    """
    Loads the main configuration file from the project root.
    Returns an empty dict if the file does not exist (graceful degradation).
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}. "
                                f"Please ensure the config.yaml exists in the project root.")
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML configuration at {CONFIG_PATH}: {e}")

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieves a specific configuration value using dot-notation for nested keys.
    Example: get_config_value('oulad.min_learners_per_course')
    """
    config = load_config()
    
    # Handle dot-notation for nested keys
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def generate_default_config() -> Dict[str, Any]:
    """
    Returns a default configuration structure if the file is missing.
    Note: In production, this is primarily for reference or scaffolding.
    """
    return {
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "cache_dir": "data/cache",
            "checksums_dir": "data/checksums"
        },
        "oulad": {
            "url_students": "https://analyse.kmi.open.ac.uk/open_dataset/students",
            "url_events": "https://analyse.kmi.open.ac.uk/open_dataset/events",
            "min_learners_per_course": 50
        },
        "model": {
            "feedback_thresholds": {
                "immediate_hours": 2.0,
                "delayed_hours": 48.0
            },
            "cluster_robust": {
                "cluster_by": "course_id"
            }
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "data/processed/pipeline.log"
        }
    }

def get_oulad_urls() -> Dict[str, str]:
    """
    Convenience wrapper to retrieve OULAD download URLs.
    """
    return {
        "students": get_config_value('oulad.url_students'),
        "events": get_config_value('oulad.url_events')
    }

def get_feedback_thresholds() -> Dict[str, float]:
    """
    Convenience wrapper to retrieve feedback timing thresholds.
    Returns a dict with 'immediate_hours' and 'delayed_hours'.
    """
    return {
        "immediate_hours": get_config_value('model.feedback_thresholds.immediate_hours', 2.0),
        "delayed_hours": get_config_value('model.feedback_thresholds.delayed_hours', 48.0)
    }

def get_data_paths() -> Dict[str, Path]:
    """
    Returns resolved Path objects for data directories.
    """
    return {
        "raw": PROJECT_ROOT / get_config_value('data.raw_dir', 'data/raw'),
        "processed": PROJECT_ROOT / get_config_value('data.processed_dir', 'data/processed'),
        "cache": PROJECT_ROOT / get_config_value('data.cache_dir', 'data/cache'),
        "checksums": PROJECT_ROOT / get_config_value('data.checksums_dir', 'data/checksums')
    }