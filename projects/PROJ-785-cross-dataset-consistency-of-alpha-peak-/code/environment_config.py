"""
Environment configuration management for dataset IDs and processing parameters.

This module provides centralized configuration loading, validation, and accessors
for the cross-dataset APF consistency study. It ensures all datasets, preprocessing
parameters, and analysis thresholds are defined in a single, validated source.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_project_root, get_data_path
from exceptions import DataIntegrityError, MissingMetadataError

# Default configuration file path relative to project root
DEFAULT_CONFIG_PATH = "state/environment_config.json"

# Default values for processing parameters
DEFAULT_ALPHA_BAND = {"low": 8.0, "high": 13.0}
DEFAULT_CONSISTENCY_THRESHOLD = 0.5  # Hz
DEFAULT_RANDOM_SEED = 42
DEFAULT_POWER_LINE_FREQUENCY = 60  # Hz (will be overridden by metadata)

# Dataset IDs for the study (validated list from T012.1)
DEFAULT_DATASET_IDS = [
    "ds003865",
    "ds003392",
    "ds003775",
    "ds004292",
    "ds004884"
]

# Processing pipeline parameters
PIPELINE_A_PARAMS = {
    "filter_low": 1.0,
    "filter_high": 45.0,
    "ica_reject": True,
    "ica_correlation_threshold": 0.8,
    "ica_variance_threshold": 0.15,
    "reference": "car"
}

PIPELINE_B_PARAMS = {
    "filter_low": 0.5,
    "filter_high": 40.0,
    "ica_reject": False,
    "reference": "mastoid"
}

def load_environment_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file. If None, uses the default path.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        DataIntegrityError: If the configuration file cannot be found or is invalid.
    """
    if config_path is None:
        config_path = os.path.join(get_project_root(), DEFAULT_CONFIG_PATH)
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        # Create a default configuration if it doesn't exist
        config = _create_default_config()
        save_environment_config(config, str(config_path))
        return config
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        raise DataIntegrityError(f"Invalid JSON in configuration file: {config_path}") from e
    except Exception as e:
        raise DataIntegrityError(f"Failed to load configuration file: {config_path}") from e

def save_environment_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save environment configuration to a JSON file.
    
    Args:
        config: Dictionary containing the configuration.
        config_path: Path to save the configuration file. If None, uses the default path.
    """
    if config_path is None:
        config_path = os.path.join(get_project_root(), DEFAULT_CONFIG_PATH)
    
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def _create_default_config() -> Dict[str, Any]:
    """
    Create a default configuration dictionary.
    
    Returns:
        Dictionary with default configuration values.
    """
    return {
        "dataset_ids": DEFAULT_DATASET_IDS,
        "alpha_band": DEFAULT_ALPHA_BAND,
        "consistency_threshold": DEFAULT_CONSISTENCY_THRESHOLD,
        "random_seed": DEFAULT_RANDOM_SEED,
        "power_line_frequency": DEFAULT_POWER_LINE_FREQUENCY,
        "pipelines": {
            "pipeline_a": PIPELINE_A_PARAMS,
            "pipeline_b": PIPELINE_B_PARAMS
        },
        "processing": {
            "max_subjects_per_batch": 10,
            "use_streaming": True,
            "memory_limit_gb": 14
        }
    }

def get_dataset_ids(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get the list of dataset IDs from the configuration.
    
    Args:
        config: Configuration dictionary. If None, loads the default config.
        
    Returns:
        List of dataset IDs.
        
    Raises:
        DataIntegrityError: If dataset IDs are missing or invalid.
    """
    if config is None:
        config = load_environment_config()
    
    if "dataset_ids" not in config:
        raise DataIntegrityError("Missing 'dataset_ids' in environment configuration")
    
    dataset_ids = config["dataset_ids"]
    
    if not isinstance(dataset_ids, list) or len(dataset_ids) == 0:
        raise DataIntegrityError("'dataset_ids' must be a non-empty list")
    
    if len(dataset_ids) < 3:
        raise DataIntegrityError(
            f"Dataset IDs list must contain at least 3 datasets (FR-001 constraint). "
            f"Found {len(dataset_ids)} datasets."
        )
    
    return dataset_ids

def get_processing_params(config: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get processing pipeline parameters from the configuration.
    
    Args:
        config: Configuration dictionary. If None, loads the default config.
        
    Returns:
        Dictionary containing pipeline parameters for 'pipeline_a' and 'pipeline_b'.
        
    Raises:
        DataIntegrityError: If pipeline parameters are missing or invalid.
    """
    if config is None:
        config = load_environment_config()
    
    if "pipelines" not in config:
        raise DataIntegrityError("Missing 'pipelines' in environment configuration")
    
    pipelines = config["pipelines"]
    
    if "pipeline_a" not in pipelines or "pipeline_b" not in pipelines:
        raise DataIntegrityError(
            "Both 'pipeline_a' and 'pipeline_b' must be defined in configuration"
        )
    
    return pipelines

def get_alpha_band(config: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Get the alpha frequency band bounds from the configuration.
    
    Args:
        config: Configuration dictionary. If None, loads the default config.
        
    Returns:
        Dictionary with 'low' and 'high' keys for the alpha band.
        
    Raises:
        DataIntegrityError: If alpha band is missing or invalid.
    """
    if config is None:
        config = load_environment_config()
    
    if "alpha_band" not in config:
        raise DataIntegrityError("Missing 'alpha_band' in environment configuration")
    
    alpha_band = config["alpha_band"]
    
    if "low" not in alpha_band or "high" not in alpha_band:
        raise DataIntegrityError(
            "Alpha band must have both 'low' and 'high' keys"
        )
    
    if alpha_band["low"] >= alpha_band["high"]:
        raise DataIntegrityError(
            f"Alpha band 'low' ({alpha_band['low']}) must be less than 'high' ({alpha_band['high']})"
        )
    
    return alpha_band

def get_consistency_threshold(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the consistency threshold for APF estimation methods.
    
    Args:
        config: Configuration dictionary. If None, loads the default config.
        
    Returns:
        Consistency threshold value in Hz.
        
    Raises:
        DataIntegrityError: If threshold is missing or invalid.
    """
    if config is None:
        config = load_environment_config()
    
    if "consistency_threshold" not in config:
        raise DataIntegrityError("Missing 'consistency_threshold' in environment configuration")
    
    threshold = config["consistency_threshold"]
    
    if not isinstance(threshold, (int, float)) or threshold <= 0:
        raise DataIntegrityError(
            f"'consistency_threshold' must be a positive number. Got: {threshold}"
        )
    
    return float(threshold)

def get_random_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the random seed for reproducibility.
    
    Args:
        config: Configuration dictionary. If None, loads the default config.
        
    Returns:
        Random seed value.
        
    Raises:
        DataIntegrityError: If seed is missing or invalid.
    """
    if config is None:
        config = load_environment_config()
    
    if "random_seed" not in config:
        raise DataIntegrityError("Missing 'random_seed' in environment configuration")
    
    seed = config["random_seed"]
    
    if not isinstance(seed, int):
        raise DataIntegrityError(
            f"'random_seed' must be an integer. Got: {type(seed).__name__}"
        )
    
    return seed

def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate the entire environment configuration.
    
    Args:
        config: Configuration dictionary. If None, loads the default config.
        
    Returns:
        True if configuration is valid.
        
    Raises:
        DataIntegrityError: If any part of the configuration is invalid.
    """
    if config is None:
        config = load_environment_config()
    
    # Validate each component
    get_dataset_ids(config)
    get_processing_params(config)
    get_alpha_band(config)
    get_consistency_threshold(config)
    get_random_seed(config)
    
    return True

def init_default_config() -> Dict[str, Any]:
    """
    Initialize and save the default configuration file.
    
    Returns:
        The default configuration dictionary.
    """
    config = _create_default_config()
    save_environment_config(config)
    return config