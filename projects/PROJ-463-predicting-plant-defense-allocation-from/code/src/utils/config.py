"""
Configuration management for the plant defense allocation pipeline.

Provides a centralized configuration system for paths, random seeds,
statistical thresholds, and biological constants (housekeeping/trait-synthesis genes).
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

# Singleton instance holder
_config_instance: Optional["Config"] = None

# Default biological constants derived from FR-003 and FR-005
DEFAULT_HOUSEKEEPING_GENES: List[str] = [
    "ACT2", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1",
    "CYP96A1", "CYP96A2", "CYP96A3",
    "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6", "CYP71A7",
    "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13", "CYP71A14",
    "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
    "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26",
    "CYP71A27", "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
]

DEFAULT_TRAIT_SYNTHESIS_GENES: List[str] = [
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1",
    "CYP96A1", "CYP96A2", "CYP96A3",
    "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6", "CYP71A7",
    "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13", "CYP71A14",
    "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
    "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26",
    "CYP71A27", "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
]

@dataclass
class Config:
    """
    Central configuration dataclass.
    
    Attributes:
        project_root: Absolute path to the project root directory.
        data_root: Absolute path to the data directory.
        seed: Random seed for reproducibility.
        fdr_threshold: False Discovery Rate threshold for DE analysis.
        log2fc_threshold: Log2 Fold Change threshold for DE analysis.
        min_replicates: Minimum number of replicates required for a study.
        cv_reduction_target: Target coefficient of variation reduction for batch correction.
        housekeeping_genes: List of housekeeping gene identifiers.
        trait_synthesis_genes: List of gene identifiers to exclude from predictors.
        min_species_count: Minimum number of species required for power analysis.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data")
    seed: int = 42
    fdr_threshold: float = 0.05
    log2fc_threshold: float = 1.0
    min_replicates: int = 2
    cv_reduction_target: float = 0.20  # 20% reduction
    housekeeping_genes: List[str] = field(default_factory=lambda: DEFAULT_HOUSEKEEPING_GENES)
    trait_synthesis_genes: List[str] = field(default_factory=lambda: DEFAULT_TRAIT_SYNTHESIS_GENES)
    min_species_count: int = 15

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return asdict(self)

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to a JSON file."""
        if path is None:
            path = self.project_root / "config.json"
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        # Convert string paths back to Path objects
        if "project_root" in data:
            data["project_root"] = Path(data["project_root"])
        if "data_root" in data:
            data["data_root"] = Path(data["data_root"])
        return cls(**data)

def get_config() -> Config:
    """
    Get the global configuration singleton.
    Initializes with defaults if not already set.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config_instance
    _config_instance = None

def get_data_path() -> Path:
    """Get the configured data root path."""
    return get_config().data_root

def get_threshold(metric: str = "fdr") -> float:
    """
    Get a specific threshold value.
    
    Args:
        metric: The metric name ('fdr', 'log2fc', 'cv_reduction').
    
    Returns:
        The threshold value.
    """
    cfg = get_config()
    if metric == "fdr":
        return cfg.fdr_threshold
    elif metric == "log2fc":
        return cfg.log2fc_threshold
    elif metric == "cv_reduction":
        return cfg.cv_reduction_target
    else:
        raise ValueError(f"Unknown threshold metric: {metric}")

def get_seed() -> int:
    """Get the configured random seed."""
    return get_config().seed

def get_housekeeping_genes() -> List[str]:
    """Get the list of housekeeping genes."""
    return get_config().housekeeping_genes

def get_trait_synthesis_genes() -> List[str]:
    """Get the list of trait synthesis genes to exclude."""
    return get_config().trait_synthesis_genes
