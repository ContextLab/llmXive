"""
Configuration loader for the llmXive follow-up project.

Handles loading of YAML configuration files, specifically the seeds configuration.
Provides a global SEEDS list for reproducibility across experiments.
"""
import os
import yaml
from typing import List, Optional, Dict, Any

# Global configuration state
_seeds: Optional[List[int]] = None
_config_path: Optional[str] = None

def load_seeds_config(config_path: Optional[str] = None) -> List[int]:
    """
    Load the seeds configuration from a YAML file.
    
    Args:
        config_path: Path to the seeds.yaml file. If None, uses default path.
        
    Returns:
        List of integer seeds.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is invalid or missing required keys.
        TypeError: If seeds are not integers.
    """
    global _seeds, _config_path
    
    if _seeds is not None and config_path == _config_path:
        return _seeds
        
    if config_path is None:
        # Default path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config", "seeds.yaml")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Seeds configuration file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if config is None:
        raise ValueError(f"Seeds configuration file is empty: {config_path}")
    
    if "seeds" not in config:
        raise ValueError(f"Seeds configuration missing 'seeds' key: {config_path}")
    
    raw_seeds = config["seeds"]
    
    if not isinstance(raw_seeds, list):
        raise ValueError(f"Seeds must be a list, got {type(raw_seeds)}")
    
    if len(raw_seeds) == 0:
        raise ValueError("Seeds list cannot be empty")
    
    for i, seed in enumerate(raw_seeds):
        if not isinstance(seed, int):
            raise TypeError(f"Seed at index {i} must be an integer, got {type(seed)}: {seed}")
    
    _seeds = raw_seeds
    _config_path = config_path
    
    return _seeds

def get_seeds() -> List[int]:
    """
    Get the global SEEDS list, loading it if necessary.
    
    Returns:
        List of integer seeds.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is invalid or missing required keys.
    """
    if _seeds is None:
        load_seeds_config()
    return _seeds

def set_seeds(seeds: List[int]) -> None:
    """
    Manually set the global SEEDS list (useful for testing or dynamic overrides).
    
    Args:
        seeds: List of integer seeds to use.
    """
    global _seeds, _config_path
    
    if not isinstance(seeds, list):
        raise TypeError("Seeds must be a list")
    
    for i, seed in enumerate(seeds):
        if not isinstance(seed, int):
            raise TypeError(f"Seed at index {i} must be an integer, got {type(seed)}: {seed}")
    
    if len(seeds) == 0:
        raise ValueError("Seeds list cannot be empty")
    
    _seeds = seeds
    _config_path = None  # Mark as manually set

def reset_config() -> None:
    """Reset the global configuration state."""
    global _seeds, _config_path
    _seeds = None
    _config_path = None

# Export the global SEEDS list as a module-level variable
# This allows direct import: from config_loader import SEEDS
try:
    SEEDS = get_seeds()
except (FileNotFoundError, ValueError) as e:
    # If config is not found during import, SEEDS will be None
    # The actual error will be raised when get_seeds() is called
    SEEDS = None
