"""
Environment configuration management for reproducible research.

This module handles:
- PYTHONHASHSEED configuration
- Random seed initialization for numpy, random, and torch (if available)
- Validation of seed environment
- Default configuration file creation
"""

import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# Try to import torch for reproducibility if available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

DEFAULT_SEED = 42
SEED_ENV_VAR = "RANDOM_SEED"
HASH_SEED_ENV_VAR = "PYTHONHASHSEED"

def load_environment_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment configuration from a YAML file or return defaults.
    
    Args:
        config_path: Path to the configuration file. If None, uses default location.
        
    Returns:
        Dictionary containing environment configuration.
    """
    default_config = {
        "random_seed": DEFAULT_SEED,
        "python_hash_seed": True,
        "hash_seed_value": DEFAULT_SEED,
        "deterministic_mode": True
    }
    
    if config_path is None:
        config_path = Path("config/environment_config.yaml")
    
    if not config_path.exists():
        return default_config
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
            # Merge with defaults
            return {**default_config, **loaded_config}
    except Exception as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return default_config

def set_python_hash_seed(seed_value: Optional[int] = None) -> int:
    """
    Set PYTHONHASHSEED environment variable for reproducible hashing.
    
    Args:
        seed_value: The seed value to use. If None, uses default seed.
        
    Returns:
        The seed value that was set.
    """
    if seed_value is None:
        seed_value = DEFAULT_SEED
    
    os.environ[HASH_SEED_ENV_VAR] = str(seed_value)
    return seed_value

def set_random_seeds(seed: Optional[int] = None) -> int:
    """
    Set random seeds for all relevant libraries.
    
    Args:
        seed: The seed value to use. If None, uses default seed.
        
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed
    np.random.seed(seed)
    
    # Set PyTorch's seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Set environment variable for reproducibility
    os.environ[SEED_ENV_VAR] = str(seed)
    
    return seed

def validate_seed_environment() -> Dict[str, Any]:
    """
    Validate that the seed environment is correctly configured.
    
    Returns:
        Dictionary with validation results.
    """
    results = {
        "python_hash_seed_set": False,
        "python_hash_seed_value": None,
        "random_seed_set": False,
        "random_seed_value": None,
        "numpy_seed_set": False,
        "numpy_seed_value": None,
        "torch_seed_set": False if not TORCH_AVAILABLE else None,
        "torch_seed_value": None if not TORCH_AVAILABLE else None,
        "is_valid": True,
        "warnings": []
    }
    
    # Check PYTHONHASHSEED
    hash_seed = os.environ.get(HASH_SEED_ENV_VAR)
    if hash_seed is not None:
        results["python_hash_seed_set"] = True
        try:
            results["python_hash_seed_value"] = int(hash_seed)
        except ValueError:
            results["warnings"].append(f"Invalid PYTHONHASHSEED value: {hash_seed}")
    else:
        results["warnings"].append("PYTHONHASHSEED not set")
    
    # Check random seed
    random_seed = os.environ.get(SEED_ENV_VAR)
    if random_seed is not None:
        results["random_seed_set"] = True
        try:
            results["random_seed_value"] = int(random_seed)
        except ValueError:
            results["warnings"].append(f"Invalid RANDOM_SEED value: {random_seed}")
    
    # Note: We cannot directly check numpy/torch internal seeds,
    # but we can verify they were initialized if the module was imported
    results["numpy_seed_set"] = True  # Assumed if numpy is imported
    if TORCH_AVAILABLE:
        results["torch_seed_set"] = True
    
    # Overall validity
    if not results["python_hash_seed_set"]:
        results["is_valid"] = False
    
    return results

def initialize_environment(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialize the environment with proper seeds and hash settings.
    
    Args:
        config: Optional configuration dictionary. If None, loads from default config.
        
    Returns:
        Dictionary with initialization results.
    """
    if config is None:
        config = load_environment_config()
    
    results = {
        "seed": DEFAULT_SEED,
        "hash_seed": DEFAULT_SEED,
        "torch_initialized": False,
        "warnings": []
    }
    
    # Set random seed
    seed = config.get("random_seed", DEFAULT_SEED)
    results["seed"] = set_random_seeds(seed)
    
    # Set PYTHONHASHSEED if enabled
    if config.get("python_hash_seed", True):
        hash_seed_value = config.get("hash_seed_value", DEFAULT_SEED)
        results["hash_seed"] = set_python_hash_seed(hash_seed_value)
    else:
        results["warnings"].append("PYTHONHASHSEED not set as per configuration")
    
    # Check torch
    if TORCH_AVAILABLE:
        results["torch_initialized"] = True
    
    # Validate
    validation = validate_seed_environment()
    if not validation["is_valid"]:
        results["warnings"].extend(validation["warnings"])
    
    return results

def create_default_config_file(output_path: Optional[Path] = None) -> Path:
    """
    Create a default environment configuration file.
    
    Args:
        output_path: Path to write the configuration file. If None, uses default location.
        
    Returns:
        Path to the created configuration file.
    """
    if output_path is None:
        output_path = Path("config/environment_config.yaml")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "random_seed": DEFAULT_SEED,
        "python_hash_seed": True,
        "hash_seed_value": DEFAULT_SEED,
        "deterministic_mode": True,
        "description": "Environment configuration for reproducible research"
    }
    
    import yaml
    with open(output_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    return output_path

# Convenience function for quick initialization
def init(seed: Optional[int] = None, set_hash_seed: bool = True) -> int:
    """
    Quick initialization function for common use cases.
    
    Args:
        seed: Optional seed value. If None, uses default.
        set_hash_seed: Whether to set PYTHONHASHSEED.
        
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    if set_hash_seed:
        set_python_hash_seed(seed)
    
    set_random_seeds(seed)
    return seed
