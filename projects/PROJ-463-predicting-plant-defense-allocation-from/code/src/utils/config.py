import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import random

@dataclass
class Config:
    """
    Configuration singleton for the plant defense allocation pipeline.
    
    Attributes:
        data_root: Root directory for all data files
        seed: Random seed for reproducibility
        housekeeping_genes: Fixed list of housekeeping genes for normalization
        trait_synthesis_genes: Genes to exclude from predictors to prevent bias
    """
    data_root: str = "data"
    seed: int = 42
    
    # Fixed list of housekeeping genes as defined in FR-003
    housekeeping_genes: List[str] = field(default_factory=lambda: [
        "ACT2", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
        "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1",
        "CYP96A2", "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4",
        "CYP71A5", "CYP71A6", "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10",
        "CYP71A11", "CYP71A12", "CYP71A13", "CYP71A14", "CYP71A15", "CYP71A16",
        "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20", "CYP71A21", "CYP71A22",
        "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27", "CYP71A28",
        "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
    ])
    
    # Trait synthesis genes to exclude from predictors (FR-005)
    trait_synthesis_genes: List[str] = field(default_factory=lambda: [
        "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1",
        "CYP96A1", "CYP96A2", "CYP96A3",
        "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
        "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12",
        "CYP71A13", "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18",
        "CYP71A19", "CYP71A20", "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24",
        "CYP71A25", "CYP71A26", "CYP71A27", "CYP71A28", "CYP71A29", "CYP71A30",
        "CYP71A31", "CYP71A32"
    ])
    
    _instance: Optional['Config'] = None

    @classmethod
    def get_instance(cls) -> 'Config':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton instance."""
        cls._instance = None

def get_config() -> Config:
    """Get the configuration singleton."""
    return Config.get_instance()

def reset_config():
    """Reset the configuration singleton."""
    Config.reset()

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    config = get_config()
    config.seed = seed
    random.seed(seed)

def get_data_path() -> Path:
    """Get the data root path as a Path object."""
    config = get_config()
    return Path(config.data_root)

def get_threshold(name: str, default: float = 0.05) -> float:
    """Get a threshold value from config (placeholder for future expansion)."""
    # For now, return defaults as thresholds are not yet stored in config
    return default

def get_seed() -> int:
    """Get the current random seed."""
    config = get_config()
    return config.seed

def get_housekeeping_genes() -> List[str]:
    """Get the list of housekeeping genes."""
    config = get_config()
    return config.housekeeping_genes.copy()

def get_trait_synthesis_genes() -> List[str]:
    """Get the list of trait synthesis genes to exclude."""
    config = get_config()
    return config.trait_synthesis_genes.copy()
