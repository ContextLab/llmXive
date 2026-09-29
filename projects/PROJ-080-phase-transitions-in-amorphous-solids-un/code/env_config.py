import os
from pathlib import Path
from typing import Optional
import hashlib
import json
from datasets import load_dataset

def check_environment_variable(var_name: str) -> bool:
    """Check if an environment variable is set."""
    return var_name in os.environ

def get_cache_dir() -> Path:
    """Get the cache directory for datasets."""
    cache_dir = Path.home() / ".cache" / "huggingface"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_dataset_path(dataset_name: str) -> Path:
    """Get the path for a dataset."""
    return Path("data") / "raw" / dataset_name

def verify_source_integrity(dataset_name: str) -> bool:
    """Verify the integrity of a dataset source."""
    # Placeholder for integrity check logic
    return True

def load_verified_dataset(dataset_name: str, config: Optional[Dict] = None):
    """
    Load a verified dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset
        config: Optional configuration dictionary
    
    Returns:
        Loaded dataset or None if failed
    """
    try:
        if config:
            dataset = load_dataset(dataset_name, **config)
        else:
            dataset = load_dataset(dataset_name)
        return dataset
    except Exception as e:
        return None

def get_dataset_config() -> Dict:
    """Get dataset configuration."""
    return {
        "trust_remote_code": True,
        "split": "train"
    }
