import os
from typing import List, Tuple, Optional
import yaml
from pathlib import Path

CONFIG_PATH = Path("config.yaml")

def get_dataset_ids() -> List[str]:
    """
    Reads dataset IDs from config.yaml.
    Returns [primary_id, fallback_id]
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file {CONFIG_PATH} not found. "
                                "Please create config.yaml with dataset IDs.")
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    datasets = config.get('datasets', {})
    primary = datasets.get('primary')
    fallback = datasets.get('fallback_only')
    
    if not primary:
        raise ValueError("Primary dataset ID not found in config.yaml")
    
    if fallback:
        return [primary, fallback]
    return [primary]

def get_sample_limit() -> int:
    """
    Reads the sample limit (N) from config.yaml.
    """
    if not CONFIG_PATH.exists():
        # Default fallback if config missing, though we expect it to exist
        return 10
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('sample_limit', 10)

def get_fallback_condition() -> bool:
    """
    Returns True if fallback dataset usage is enabled.
    """
    if not CONFIG_PATH.exists():
        return False
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('allow_fallback', True)

def get_config_summary() -> dict:
    """
    Returns a summary of the current configuration.
    """
    if not CONFIG_PATH.exists():
        return {"error": "config.yaml not found"}
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_config() -> bool:
    """
    Validates that required config keys exist.
    """
    try:
        get_dataset_ids()
        get_sample_limit()
        return True
    except Exception as e:
        print(f"Config validation failed: {e}")
        return False
