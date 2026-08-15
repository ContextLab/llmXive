"""
Configuration management for the Sensitivity Analysis Pipeline.

This module handles loading dataset configurations, random seeds, and
global constants like sample size tiers.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Global Constants
SAMPLE_SIZE_TIERS = [10, 25, 50, 75, 90]
RANDOM_SEED = 42
MAX_ROWS_SUBSAMPLE = 100_000

# Default config file path
DEFAULT_CONFIG_PATH = "data/configs/datasets.yaml"

def get_config_path() -> Path:
    """Resolve the path to the path to the configuration file."""
    if os.path.exists(DEFAULT_CONFIG_PATH):
        return Path(DEFAULT_CONFIG_PATH)
    # Fallback to project root relative path if running from different context
    fallback = Path("data/configs/datasets.yaml")
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Configuration file not found at {DEFAULT_CONFIG_PATH}")

def load_dataset_configs() -> Dict[str, Any]:
    """
    Load all dataset configurations from the YAML file.

    Returns:
        Dictionary mapping dataset_id to configuration dict.
    """
    config_path = get_config_path()
    logger.info(f"Loading dataset configs from {config_path}")
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return data.get("datasets", {})

def get_dataset_config(dataset_id: str) -> Dict[str, Any]:
    """
    Retrieve configuration for a specific dataset.

    Args:
        dataset_id: The identifier for the dataset.

    Returns:
        Configuration dictionary for the dataset.

    Raises:
        ValueError: If dataset_id is not found.
    """
    configs = load_dataset_configs()
    if dataset_id not in configs:
        raise ValueError(f"Dataset configuration not found for ID: {dataset_id}")
    return configs[dataset_id]

def get_sample_size_tier_counts(total_rows: int) -> Dict[int, int]:
    """
    Calculate the number of rows for each sample size tier.

    Args:
        total_rows: Total number of rows in the dataset.

    Returns:
        Dictionary mapping tier percentage to row count.
    """
    return {tier: int(total_rows * (tier / 100.0)) for tier in SAMPLE_SIZE_TIERS}

def get_random_seed() -> int:
    """Get the global random seed."""
    return RANDOM_SEED
