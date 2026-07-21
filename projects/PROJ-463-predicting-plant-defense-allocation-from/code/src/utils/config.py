"""
Configuration management for the Plant Defense Allocation Pipeline.

Provides centralized access to paths, seeds, thresholds, and gene lists.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import random

@dataclass
class Config:
    """Pipeline configuration."""
    # Paths
    data_root: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    traits_dir: str = "data/traits"
    manifests_dir: str = "data/manifests"
    synthetic_dir: str = "data/synthetic"
    figures_dir: str = "figures"
    
    # Seeds
    random_seed: int = 42
    
    # Thresholds
    min_replicates: int = 2
    max_missing_fraction: float = 0.30
    min_cv_reduction: float = 0.20
    fdr_threshold: float = 0.05
    log2fc_threshold: float = 1.0
    
    # Gene lists (from spec FR-003)
    housekeeping_genes: List[str] = field(default_factory=lambda: [
        "ACT", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
        "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1", "CYP96A2",
        "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
        "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13",
        "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
        "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27",
        "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
    ])
    
    trait_synthesis_genes: List[str] = field(default_factory=lambda: [
        "CYP79D16", "CYP79D15", "CYP79D17"
    ])
    
    # Other
    log_level: str = "INFO"
    max_workers: int = 4

# Singleton instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the singleton config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def reset_config() -> None:
    """Reset the config to defaults."""
    global _config
    _config = None

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    config = get_config()
    config.random_seed = seed
    random.seed(seed)
    if hasattr(__import__('numpy'), 'random'):
        __import__('numpy').random.seed(seed)

def get_data_path() -> Path:
    """Get the base data directory path."""
    return Path(get_config().data_root)

def get_threshold(key: str) -> float:
    """Get a threshold value by key."""
    config = get_config()
    thresholds = {
        "min_replicates": config.min_replicates,
        "max_missing_fraction": config.max_missing_fraction,
        "min_cv_reduction": config.min_cv_reduction,
        "fdr_threshold": config.fdr_threshold,
        "log2fc_threshold": config.log2fc_threshold
    }
    if key not in thresholds:
        raise KeyError(f"Unknown threshold: {key}")
    return thresholds[key]

def get_seed() -> int:
    """Get the random seed."""
    return get_config().random_seed

def get_housekeeping_genes() -> List[str]:
    """Get the list of housekeeping genes."""
    return get_config().housekeeping_genes

def get_trait_synthesis_genes() -> List[str]:
    """Get the list of trait synthesis genes to exclude."""
    return get_config().trait_synthesis_genes
