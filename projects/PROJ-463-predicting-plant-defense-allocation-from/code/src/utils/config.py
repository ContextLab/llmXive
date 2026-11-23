import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import random

# Fixed list of housekeeping genes as per FR-003
HOUSEKEEPING_GENES = [
    "ACT2", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1", "CYP96A2",
    "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
    "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13",
    "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
    "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27",
    "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
]

# Trait synthesis genes that should be excluded from predictors (FR-005)
TRAIT_SYNTHESIS_GENES = [
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1", "CYP96A2",
    "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
    "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13",
    "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
    "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27",
    "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
]

@dataclass
class Config:
    """Configuration singleton for the pipeline."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_root: Path = field(default_factory=lambda: Path("data"))
    seed: int = 42
    housekeeping_genes: List[str] = field(default_factory=lambda: HOUSEKEEPING_GENES)
    trait_synthesis_genes: List[str] = field(default_factory=lambda: TRAIT_SYNTHESIS_GENES)
    
    # Thresholds
    min_replicates: int = 2
    fdr_threshold: float = 0.05
    log2fc_threshold: float = 1.0
    cv_reduction_target: float = 0.20  # 20%
    
    def __post_init__(self):
        # Resolve paths relative to project root if not absolute
        if not self.data_root.is_absolute():
            self.data_root = self.project_root / self.data_root

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config():
    """Reset the configuration instance."""
    global _config_instance
    _config_instance = None

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if _config_instance:
        _config_instance.seed = seed

def get_data_path() -> Path:
    """Get the data root path."""
    return get_config().data_root

def get_threshold(key: str) -> float:
    """Get a threshold value by key."""
    config = get_config()
    thresholds = {
        "fdr": config.fdr_threshold,
        "log2fc": config.log2fc_threshold,
        "cv_reduction": config.cv_reduction_target,
        "min_replicates": float(config.min_replicates)
    }
    return thresholds.get(key, 0.0)

def get_seed() -> int:
    """Get the random seed."""
    return get_config().seed

def get_housekeeping_genes() -> List[str]:
    """Get the list of housekeeping genes."""
    return get_config().housekeeping_genes

def get_trait_synthesis_genes() -> List[str]:
    """Get the list of trait synthesis genes to exclude."""
    return get_config().trait_synthesis_genes
