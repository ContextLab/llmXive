"""
Configuration management for the plant defense allocation pipeline.

Handles paths, seeds, thresholds, and gene lists as defined in the project specs.
Implements a singleton pattern for global configuration state.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

# Default thresholds and constants
DEFAULT_SEED = 42
DEFAULT_BATCH_CORRECTION_CV_THRESHOLD = 0.20  # 20% reduction required
DEFAULT_FDR_THRESHOLD = 0.05
DEFAULT_LOG2FC_THRESHOLD = 1.0
DEFAULT_MIN_REPLICATES = 2
DEFAULT_MIN_SPECIES_FOR_POWER = 15
DEFAULT_PERMUTATION_COUNT = 10000

# Housekeeping genes for batch correction stability analysis
# Source: FR-003 specification
DEFAULT_HOUSEKEEPING_GENES = [
    "ACT2", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1", "CYP96A1", "CYP96A2",
    "CYP96A3", "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6",
    "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13",
    "CYP71A14", "CYP71A15", "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20",
    "CYP71A21", "CYP71A22", "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27",
    "CYP71A28", "CYP71A29", "CYP71A30", "CYP71A31", "CYP71A32"
]

# Trait-synthesis genes to exclude from predictor sets (circularity prevention)
# Source: FR-005 specification
DEFAULT_TRAIT_SYNTHESIS_GENES = [
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1",
    "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5",
    "CYP71A6", "CYP71A7", "CYP71A8", "CYP71A9", "CYP71A10"
]

@dataclass
class Config:
    """Global configuration state for the pipeline."""
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent)
    data_raw: Path = field(default_factory=lambda: Path("data/raw"))
    data_processed: Path = field(default=lambda: Path("data/processed"))
    data_traits: Path = field(default=lambda: Path("data/traits"))
    data_manifests: Path = field(default=lambda: Path("data/manifests"))
    data_synthetic: Path = field(default=lambda: Path("data/synthetic"))
    figures: Path = field(default=lambda: Path("figures"))
    
    # Seeds
    random_seed: int = DEFAULT_SEED
    
    # Thresholds
    batch_correction_cv_threshold: float = DEFAULT_BATCH_CORRECTION_CV_THRESHOLD
    fdr_threshold: float = DEFAULT_FDR_THRESHOLD
    log2fc_threshold: float = DEFAULT_LOG2FC_THRESHOLD
    min_replicates: int = DEFAULT_MIN_REPLICATES
    min_species_for_power: int = DEFAULT_MIN_SPECIES_FOR_POWER
    permutation_count: int = DEFAULT_PERMUTATION_COUNT
    
    # Gene Lists
    housekeeping_genes: List[str] = field(default_factory=lambda: DEFAULT_HOUSEKEEPING_GENES)
    trait_synthesis_genes: List[str] = field(default_factory=lambda: DEFAULT_TRAIT_SYNTHESIS_GENES)
    
    # Mode
    mode: str = "real"  # "real" or "synthetic"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        result = asdict(self)
        # Convert Path objects to strings for JSON serialization
        for key, value in result.items():
            if isinstance(value, Path):
                result[key] = str(value)
        return result
    
    def save(self, path: Optional[Path] = None) -> Path:
        """Save configuration to a JSON file."""
        if path is None:
            path = self.project_root / "data" / "manifests" / "config.json"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from a JSON file."""
        if path is None:
            path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "manifests" / "config.json"
        
        if not path.exists():
            # Return default config if file doesn't exist
            return cls()
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Convert string paths back to Path objects
        for key in ["data_raw", "data_processed", "data_traits", "data_manifests", "data_synthetic", "figures"]:
            if key in data:
                data[key] = Path(data[key])
        
        # Handle project_root if present
        if "project_root" in data:
            data["project_root"] = Path(data["project_root"])
        
        return cls(**data)

# Singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config_instance
    _config_instance = None

def get_data_path(sub_path: Optional[str] = None) -> Path:
    """Get a path relative to the data root."""
    cfg = get_config()
    if sub_path:
        return cfg.project_root / "data" / sub_path
    return cfg.project_root / "data"

def get_threshold(name: str) -> Any:
    """Get a specific threshold value by name."""
    cfg = get_config()
    mapping = {
        "batch_correction_cv": cfg.batch_correction_cv_threshold,
        "fdr": cfg.fdr_threshold,
        "log2fc": cfg.log2fc_threshold,
        "min_replicates": cfg.min_replicates,
        "min_species": cfg.min_species_for_power,
        "permutations": cfg.permutation_count
    }
    if name not in mapping:
        raise ValueError(f"Unknown threshold: {name}")
    return mapping[name]

def get_seed() -> int:
    """Get the global random seed."""
    return get_config().random_seed

def get_housekeeping_genes() -> List[str]:
    """Get the list of housekeeping genes for batch correction."""
    return get_config().housekeeping_genes

def get_trait_synthesis_genes() -> List[str]:
    """Get the list of trait-synthesis genes to exclude from predictors."""
    return get_config().trait_synthesis_genes