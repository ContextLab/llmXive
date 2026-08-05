"""
Configuration loading and validation utilities.

This module handles loading the project configuration from YAML files
and validating critical parameters like I-VT thresholds.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DEFAULT_IVT_THRESHOLD_MS = 100

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config if config else {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {config_path}: {e}")

def validate_ivt_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate I-VT specific configuration parameters.
    
    Checks:
    - ivt_duration_threshold must be present and be an integer
    - velocity and dispersion thresholds must NOT be present (spec mandates duration-only)
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check for forbidden parameters
    forbidden_keys = ['ivt_velocity_threshold', 'ivt_dispersion_threshold']
    for key in forbidden_keys:
        if key in config:
            return False, f"Forbidden parameter found in config: {key}. Spec mandates duration-only I-VT."
    
    # Check for required parameter
    if 'ivt_duration_threshold' not in config:
        return False, None  # Will use default, not an error
    
    threshold = config['ivt_duration_threshold']
    if not isinstance(threshold, int):
        return False, f"ivt_duration_threshold must be an integer, got {type(threshold).__name__}"
    
    if threshold <= 0:
        return False, f"ivt_duration_threshold must be positive, got {threshold}"
    
    return True, None

def get_validated_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a validated configuration, applying defaults where necessary.
    
    Args:
        config: Raw configuration dictionary.
        
    Returns:
        Validated configuration dictionary with defaults applied.
    """
    logger = logging.getLogger(__name__)
    
    # Validate
    is_valid, error_msg = validate_ivt_config(config)
    
    if not is_valid and error_msg:
        raise ValueError(error_msg)
    
    # Apply default if missing
    if 'ivt_duration_threshold' not in config:
        logger.warning(f"ivt_duration_threshold missing, using default: {DEFAULT_IVT_THRESHOLD_MS} ms")
        config['ivt_duration_threshold'] = DEFAULT_IVT_THRESHOLD_MS
    
    return config

def main():
    """Test function for config loading."""
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    config_path = Path("code/config.yaml")
    if config_path.exists():
        config = load_config(config_path)
        validated = get_validated_config(config)
        logger.info(f"Loaded config: {validated}")
    else:
        logger.info("Config file not found. Creating default structure.")

if __name__ == "__main__":
    main()
