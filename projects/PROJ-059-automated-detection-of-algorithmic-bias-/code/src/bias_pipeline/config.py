"""
Configuration management for the Bias Detection Pipeline.

Loads project-specific settings from the YAML state file and defines
global constants required for pipeline execution.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from .utils import PipelineError, setup_logging

# Logger setup
logger = setup_logging(__name__)

# Global constant derived from methodology correction
# Threshold for determining if a citation title overlaps significantly
CITATION_TITLE_OVERLAP_THRESHOLD = 0.85

# Default paths relative to project root
DEFAULT_CONFIG_PATH = Path("state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_project_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the project configuration from the YAML state file.
    
    Args:
        config_path: Optional path to the config YAML. Defaults to 
                     state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml
                     
    Returns:
        Dict containing the project configuration.
        
    Raises:
        PipelineError: If the config file is missing or invalid.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    full_path = PROJECT_ROOT / config_path
    
    if not full_path.exists():
        error_msg = f"Configuration file not found: {full_path}"
        logger.error(error_msg)
        raise PipelineError(error_msg)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise PipelineError("Configuration file must contain a top-level dictionary.")
        
        logger.info(f"Successfully loaded configuration from {full_path}")
        return config
        
    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML in configuration file: {e}"
        logger.error(error_msg)
        raise PipelineError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error loading configuration: {e}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

def get_methodology_config() -> Dict[str, Any]:
    """
    Retrieve the methodology section of the configuration.
    
    Returns:
        Dict with methodology parameters.
    """
    config = load_project_config()
    return config.get("methodology", {})

def get_data_sources() -> Dict[str, str]:
    """
    Retrieve the data sources section of the configuration.
    
    Returns:
        Dict with data source paths.
    """
    config = load_project_config()
    return config.get("data_sources", {})

def get_limits() -> Dict[str, Any]:
    """
    Retrieve the execution limits section of the configuration.
    
    Returns:
        Dict with execution limits.
    """
    config = load_project_config()
    return config.get("limits", {})

def get_flags() -> Dict[str, bool]:
    """
    Retrieve the feature flags section of the configuration.
    
    Returns:
        Dict with feature flags.
    """
    config = load_project_config()
    return config.get("flags", {})

# Initialize global config on import (optional, can be lazy)
# For robustness, we define a lazy loader pattern in usage rather than global state mutation
# unless explicitly needed.
_cached_config: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration, caching it after the first load.
    
    Returns:
        The configuration dictionary.
    """
    global _cached_config
    if _cached_config is None:
        _cached_config = load_project_config()
    return _cached_config