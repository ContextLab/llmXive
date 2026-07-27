"""
Configuration management for the plant defense allocation pipeline.
Defines fixed parameters, paths, and gene lists.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import random
import numpy as np

@dataclass
class Config:
    """Configuration container for the pipeline."""
    # Paths
    data_root: str = "data"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    traits_dir: str = "data/traits"
    manifests_dir: str = "data/manifests"
    synthetic_dir: str = "data/synthetic"

    # Seeds
    seed: int = 42

    # Thresholds
    fdr_threshold: float = 0.05
    log2fc_threshold: float = 1.0
    min_replicates: int = 2
    trait_missing_threshold: float = 0.30

    # Fixed Gene Lists
    # Housekeeping genes for normalization (FR-003)
    housekeeping_genes: List[str] = field(default_factory=lambda: [
        "ACT2", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
        "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1", "CYP96A2",
        "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
        "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13",
        "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
        "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27",
        "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
    ])

    # Trait synthesis genes to exclude from predictors (FR-005)
    trait_synthesis_genes: List[str] = field(default_factory=lambda: [
        "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1", "CYP96A2",
        "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
        "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13",
        "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
        "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27",
        "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
    ])

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def reset_config():
    """Reset the global configuration to default."""
    global _config
    _config = None

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    get_config().seed = seed

def get_data_path() -> Path:
    """Get the root data path."""
    return Path(get_config().data_root)

def get_threshold(key: str) -> float:
    """Get a threshold value by key."""
    config = get_config()
    mapping = {
        "fdr": config.fdr_threshold,
        "log2fc": config.log2fc_threshold,
        "min_replicates": float(config.min_replicates),
        "trait_missing": config.trait_missing_threshold
    }
    return mapping.get(key, 0.0)

def get_seed() -> int:
    """Get the current seed."""
    return get_config().seed

def get_housekeeping_genes() -> List[str]:
    """Get the fixed list of housekeeping genes."""
    return get_config().housekeeping_genes

def get_trait_synthesis_genes() -> List[str]:
    """Get the fixed list of trait synthesis genes to exclude."""
    return get_config().trait_synthesis_genes
