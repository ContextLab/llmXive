"""
Utility functions for the grain boundary diffusivity project.
Provides helpers for checksumming, logging, and random seed setting.
"""
import hashlib
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import sys

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        level: Logging level.
        
    Returns:
        Configured logger.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def compute_sha256(filepath: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def set_random_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    # Note: numpy and torch seeds should be set in respective modules

def load_metadata(filepath: Path) -> Dict[str, Any]:
    """
    Load metadata from a YAML file.
    
    Args:
        filepath: Path to the metadata file.
        
    Returns:
        Dictionary of metadata.
    """
    if not filepath.exists():
        return {}
        
    with open(filepath, 'r') as f:
        return yaml.safe_load(f) or {}

def update_metadata_entry(metadata: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """
    Update a specific entry in the metadata dictionary.
    
    Args:
        metadata: Metadata dictionary.
        key: Key to update.
        value: New value.
        
    Returns:
        Updated metadata dictionary.
    """
    metadata[key] = value
    return metadata

def save_metadata(metadata: Dict[str, Any], filepath: Path) -> None:
    """
    Save metadata to a YAML file.
    
    Args:
        metadata: Metadata dictionary.
        filepath: Path to save the file.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def raise_data_insufficiency(retrieved: int, required: int, missing_features: Optional[list] = None) -> None:
    """
    Raise a DataInsufficiencyError and exit.
    
    Args:
        retrieved: Number of records retrieved.
        required: Minimum required records.
        missing_features: List of missing feature names.
    """
    from error_handling import exit_on_insufficiency
    exit_on_insufficiency(retrieved, required, missing_features)
