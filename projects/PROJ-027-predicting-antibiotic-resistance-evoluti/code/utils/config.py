"""
Configuration management for the pipeline.
Loads settings from config.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List
from .logging import get_logger

logger = get_logger(__name__)

_config_cache = None

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if config_path is None:
        # Default path relative to project root
        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "code" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return {}

    try:
        with open(config_path, "r") as f:
            _config_cache = yaml.safe_load(f) or {}
        return _config_cache
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        return {}

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a value from the config dictionary using dot notation.
    """
    config = load_config()
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def get_paths() -> Dict[str, Path]:
    """
    Get configured paths as Path objects.
    """
    config = load_config()
    paths = config.get("paths", {})
    return {
        "raw_data_dir": Path(paths.get("raw_data_dir", "data/raw")),
        "processed_data_dir": Path(paths.get("processed_data_dir", "data/processed")),
        "models_dir": Path(paths.get("models_dir", "data/models")),
        "figures_dir": Path(paths.get("figures_dir", "figures")),
        "logs_dir": Path(paths.get("logs_dir", "logs")),
    }

def get_max_isolates() -> int:
    """
    Get the maximum number of isolates to process.
    """
    return get_config_value("max_isolates", 1000)

def get_random_seed() -> int:
    """
    Get the random seed for reproducibility.
    """
    return get_config_value("random_seed", 42)

def get_bio_project_ids() -> List[str]:
    """
    Get the list of BioProject IDs to download.
    """
    return get_config_value("bio_project_ids", [])
