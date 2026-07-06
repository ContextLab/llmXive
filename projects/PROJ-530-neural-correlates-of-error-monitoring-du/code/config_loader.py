"""
Base configuration loader for the Neural Correlates of Error Monitoring project.

Handles loading of YAML configuration files, merging defaults with overrides,
and validating required keys.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .logging_config import get_logger

# Default configuration values
DEFAULT_CONFIG = {
    "project": {
        "name": "PROJ-530-neural-correlates-of-error-monitoring-du",
        "version": "0.1.0",
        "root_path": "projects/PROJ-530-neural-correlates-of-error-monitoring-du"
    },
    "data": {
        "raw_dir": "data/raw",
        "processed_dir": "data/processed",
        "zenodo_url": None,
        "checksum": None
    },
    "preprocessing": {
        "sample_rate": 500,
        "bandpass": {"low": 1.0, "high": 40.0},
        "notch": 60.0,
        "ica_components": 20,
        "eog_channels": ["EOG", "HEOG", "VEOG"],
        "mfn_window": {"pre": -0.2, "post": 0.8, "baseline": (-0.2, 0.0)},
        "analysis_window": {"start": 0.2, "end": 0.4}
    },
    "analysis": {
        "electrodes": ["FCz", "Cz", "Fz"],
        "error_threshold": 10.0,
        "sensitivity_thresholds": [5.0, 10.0, 15.0, 20.0],
        "vif_threshold": 5.0,
        "alpha": 0.05
    },
    "paths": {
        "results_models": "results/models",
        "results_figures": "results/figures",
        "results_diagnostics": "results/diagnostics",
        "code": "code",
        "tests": "tests"
    },
    "logging": {
        "level": "INFO",
        "file": "data/preprocessing.log",
        "console": True
    }
}

def load_config(
    config_path: Optional[Union[str, Path]] = None,
    project_root: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Load configuration from a YAML file, merging with defaults.
    
    Args:
        config_path: Path to the configuration YAML file. If None, looks for
                    'config.yaml' in the project root.
        project_root: Root directory of the project. If None, uses the current
                     working directory.
                     
    Returns:
        Merged configuration dictionary.
        
    Raises:
        FileNotFoundError: If config file is specified but doesn't exist.
        yaml.YAMLError: If config file contains invalid YAML.
    """
    logger = get_logger(__name__)
    
    # Determine project root
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)
        
    # Determine config file path
    if config_path is None:
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)
        
    # Load defaults
    config = DEFAULT_CONFIG.copy()
    
    # Override with file if it exists
    if config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                _deep_merge(config, file_config)
    else:
        logger.info(f"No configuration file found at {config_path}. Using defaults.")
        
    # Resolve relative paths to absolute paths
    config = _resolve_paths(config, project_root)
    
    return config

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge override dictionary into base dictionary.
    
    Args:
        base: Base dictionary to merge into.
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

def _resolve_paths(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """
    Resolve relative paths in config to absolute paths based on project root.
    
    Args:
        config: Configuration dictionary potentially containing relative paths.
        project_root: Project root directory.
        
    Returns:
        Configuration dictionary with absolute paths.
    """
    path_keys = [
        ("project", "root_path"),
        ("data", "raw_dir"),
        ("data", "processed_dir"),
        ("paths", "results_models"),
        ("paths", "results_figures"),
        ("paths", "results_diagnostics"),
        ("paths", "code"),
        ("paths", "tests"),
        ("logging", "file")
    ]
    
    for key_path in path_keys:
        current = config
        valid = True
        
        # Navigate to the nested key
        for k in key_path[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                valid = False
                break
                
        if valid and isinstance(current, dict) and key_path[-1] in current:
            value = current[key_path[-1]]
            if isinstance(value, str) and not os.path.isabs(value):
                current[key_path[-1]] = str(project_root / value)
                
    return config

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that required configuration keys are present and have valid values.
    
    Args:
        config: Configuration dictionary to validate.
        
    Raises:
        ValueError: If required keys are missing or invalid.
    """
    logger = get_logger(__name__)
    
    # Check required top-level sections
    required_sections = ["project", "data", "preprocessing", "analysis", "paths"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
            
    # Check project name
    if not config["project"].get("name"):
        raise ValueError("Project name is required")
        
    # Check data directories
    if not config["data"].get("raw_dir"):
        raise ValueError("Data raw directory is required")
        
    # Check preprocessing parameters
    if not config["preprocessing"].get("sample_rate"):
        raise ValueError("Sample rate is required for preprocessing")
        
    # Check analysis electrodes
    if not config["analysis"].get("electrodes"):
        raise ValueError("At least one electrode must be specified for analysis")
        
    logger.info("Configuration validation passed")

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from the configuration using a dot-separated key path.
    
    Args:
        config: Configuration dictionary.
        key_path: Dot-separated path to the key (e.g., "preprocessing.sample_rate").
        default: Default value if key is not found.
        
    Returns:
        Value at the key path or default.
    """
    keys = key_path.split(".")
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
            
    return current

def save_config(config: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary to save.
        output_path: Path to the output YAML file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def create_default_config(output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Create a default configuration and optionally save it to a file.
    
    Args:
        output_path: Path to save the configuration. If None, only returns the dict.
        
    Returns:
        Default configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()
    
    if output_path:
        save_config(config, output_path)
        
    return config

# Convenience function to get logger for this module
logger = get_logger(__name__)
