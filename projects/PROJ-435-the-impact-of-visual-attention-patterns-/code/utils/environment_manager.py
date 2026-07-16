"""
Environment configuration and random seed management for reproducibility.

This module handles:
1. Loading configuration from code/config.yaml
2. Setting global random seeds (numpy, random, os.environ)
3. Resolving project paths relative to the root
4. Basic logging setup
"""
import os
import random
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Global project root
# Assumes this file is at code/utils/environment_manager.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    Defaults to code/config.yaml relative to project root.
    """
    if config_path is None:
        config_path = _PROJECT_ROOT / "code" / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    Values from 'override' take precedence.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def setup_reproducibility(seed: int) -> None:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

def get_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Resolve absolute paths for data directories based on configuration.
    
    Args:
        config: Configuration dictionary containing 'paths'.
    
    Returns:
        Dictionary mapping path keys to absolute Path objects.
    """
    path_config = config.get("paths", {})
    resolved = {}
    
    # Default paths if not in config
    defaults = {
        "data_raw": "data/raw",
        "data_derived": "data/derived",
        "data_processed": "data/processed",
        "figures": "figures",
        "state": "state",
        "logs": "logs"
    }
    
    for key, default_rel in defaults.items():
        rel_path = path_config.get(key, default_rel)
        resolved[key] = _PROJECT_ROOT / rel_path
        # Ensure directories exist
        resolved[key].mkdir(parents=True, exist_ok=True)
    
    return resolved

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Retrieve a nested value from config using dot notation.
    
    Args:
        config: Configuration dictionary.
        key_path: Dot-separated path (e.g., 'algorithms.ivt.velocity_threshold').
        default: Default value if key not found.
    
    Returns:
        The value or default.
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Configure logging based on configuration settings.
    
    Args:
        config: Configuration dictionary containing 'logging'.
    
    Returns:
        Configured root logger.
    """
    log_config = config.get("logging", {})
    level_str = log_config.get("level", "INFO").upper()
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = log_config.get("file", "logs/pipeline.log")
    
    log_path = _PROJECT_ROOT / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level_str, logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """
    Entry point for testing environment setup.
    """
    config = load_config()
    print(f"Loaded config from: {_PROJECT_ROOT / 'code' / 'config.yaml'}")
    print(f"Random Seed: {config.get('random_seed')}")
    
    setup_reproducibility(config.get("random_seed", 42))
    paths = get_paths(config)
    
    print("Resolved Paths:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    logger = setup_logging(config)
    logger.info("Environment manager initialized successfully.")

if __name__ == "__main__":
    main()