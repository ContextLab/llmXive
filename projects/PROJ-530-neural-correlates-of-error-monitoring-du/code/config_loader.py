"""
Configuration Loader Module

Handles loading, validation, and management of project configuration files.
Supports YAML-based configuration with defaults and type validation.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .logging_config import get_logger

# Default configuration structure
DEFAULT_CONFIG = {
    "project": {
        "name": "neural-correlates-error-monitoring",
        "version": "1.0.0",
        "seed": 42
    },
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "results_models": "results/models",
        "results_figures": "results/figures",
        "results_diagnostics": "results/diagnostics",
        "code": "code",
        "tests": "tests"
    },
    "preprocessing": {
        "filter_bandpass": [1.0, 40.0],
        "filter_notch": 50.0,
        "ica_components": 0.95,
        "mfn_window_start": 200,
        "mfn_window_end": 400,
        "baseline_window_start": -200,
        "baseline_window_end": 0
    },
    "analysis": {
        "electrodes": ["FCz", "Cz", "Fz"],
        "error_thresholds": [5, 10, 15, 20],
        "alpha": 0.05
    },
    "logging": {
        "level": "INFO",
        "file": "data/preprocessing.log",
        "console": True
    }
}

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file. If None, looks for
                    'config.yaml' in the current directory or uses defaults.
                    
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file doesn't exist and no defaults available.
        yaml.YAMLError: If the config file is malformed.
    """
    logger = get_logger(__name__)
    
    if config_path is None:
        config_path = Path("config.yaml")
    else:
        config_path = Path(config_path)
    
    if config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            # Merge with defaults to ensure all keys exist
            merged_config = _deep_merge(DEFAULT_CONFIG, config)
            return merged_config
    else:
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return DEFAULT_CONFIG.copy()

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate.
        
    Returns:
        True if valid, False otherwise.
        
    Note:
        Logs validation errors but does not raise exceptions.
    """
    logger = get_logger(__name__)
    is_valid = True
    
    # Check required sections
    required_sections = ["project", "paths", "preprocessing", "analysis", "logging"]
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required section: {section}")
            is_valid = False
    
    # Validate project settings
    if "project" in config:
        if "seed" in config["project"]:
            if not isinstance(config["project"]["seed"], int) or config["project"]["seed"] < 0:
                logger.error("Project seed must be a non-negative integer")
                is_valid = False
    
    # Validate preprocessing settings
    if "preprocessing" in config:
        if "filter_bandpass" in config["preprocessing"]:
            bp = config["preprocessing"]["filter_bandpass"]
            if not isinstance(bp, list) or len(bp) != 2 or bp[0] >= bp[1]:
                logger.error("filter_bandpass must be a list of two numbers [low, high] with low < high")
                is_valid = False
        
        if "mfn_window_start" in config["preprocessing"]:
            if config["preprocessing"]["mfn_window_start"] >= config["preprocessing"]["mfn_window_end"]:
                logger.error("mfn_window_start must be less than mfn_window_end")
                is_valid = False
    
    # Validate analysis settings
    if "analysis" in config:
        if "electrodes" in config["analysis"]:
            if not isinstance(config["analysis"]["electrodes"], list) or len(config["analysis"]["electrodes"]) == 0:
                logger.error("electrodes must be a non-empty list")
                is_valid = False
    
    return is_valid

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from the configuration using a dot-notation path.
    
    Args:
        config: Configuration dictionary.
        key_path: Dot-separated path to the value (e.g., "project.seed").
        default: Default value if the key is not found.
                
    Returns:
        The configuration value or the default.
    """
    keys = key_path.split(".")
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary to save.
        config_path: Path to the output file.
    """
    logger = get_logger(__name__)
    config_path = Path(config_path)
    
    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Configuration saved to {config_path}")

def create_default_config(output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Create a default configuration and optionally save it to a file.
    
    Args:
        output_path: Path to save the configuration. If None, only returns the dict.
        
    Returns:
        The default configuration dictionary.
    """
    logger = get_logger(__name__)
    config = DEFAULT_CONFIG.copy()
    
    if output_path:
        save_config(config, output_path)
        logger.info(f"Default configuration created at {output_path}")
    else:
        logger.info("Default configuration created (not saved)")
    
    return config

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary.
        override: Dictionary with values to override.
        
    Returns:
        Merged dictionary.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
