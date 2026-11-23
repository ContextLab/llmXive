"""
Configuration module for the llmXive project.
Handles dataset IDs, sample limits, and validation.
"""
import os
import yaml
from pathlib import Path
from typing import List, Tuple, Optional

# Default path to the configuration file
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def _load_config() -> dict:
    """Load the YAML configuration file."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_dataset_ids() -> Tuple[str, str]:
    """
    Retrieve the primary and fallback dataset IDs.
    
    Returns:
        Tuple of (primary_dataset_id, fallback_dataset_id)
    
    Raises:
        KeyError: If dataset IDs are not found in config.
    """
    config = _load_config()
    datasets = config.get("datasets", {})
    primary = datasets.get("primary")
    fallback = datasets.get("fallback_only")
    
    if not primary:
        raise KeyError("Missing 'datasets.primary' in config.yaml")
    if not fallback:
        raise KeyError("Missing 'datasets.fallback_only' in config.yaml")
        
    return primary, fallback

def get_sample_limit() -> int:
    """
    Retrieve the sample limit (N) for the study.
    
    Returns:
        Integer representing the maximum number of subjects.
    
    Raises:
        KeyError: If sample_limit is not found in config.
    """
    config = _load_config()
    limit = config.get("sample_limit")
    
    if limit is None:
        raise KeyError("Missing 'sample_limit' in config.yaml")
    
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("sample_limit must be a positive integer")
        
    return limit

def get_config_summary() -> dict:
    """
    Retrieve a summary of the current configuration.
    
    Returns:
        Dictionary containing primary, fallback, and limit.
    """
    primary, fallback = get_dataset_ids()
    limit = get_sample_limit()
    return {
        "primary_dataset": primary,
        "fallback_dataset": fallback,
        "sample_limit": limit
    }

def validate_config() -> bool:
    """
    Validate the configuration file exists and contains required keys.
    
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    try:
        get_dataset_ids()
        get_sample_limit()
        return True
    except (FileNotFoundError, KeyError, ValueError) as e:
        raise ValueError(f"Configuration validation failed: {e}")
