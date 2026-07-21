"""
Configuration management for the plant defense allocation pipeline.

Handles paths, random seeds, analysis thresholds, and biological constants
(housekeeping genes, trait synthesis genes) as defined in the project specs.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import random

# Biological Constants (from FR-003 and project specs)
DEFAULT_HOUSEKEEPING_GENES = [
    "ACT", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1", "PP2A", "SAND",
    "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1",
    "CYP96A1", "CYP96A2", "CYP96A3",
    "CYP71A1", "CYP71A2", "CYP71A3", "CYP71A4", "CYP71A5", "CYP71A6", "CYP71A7", "CYP71A8",
    "CYP71A9", "CYP71A10", "CYP71A11", "CYP71A12", "CYP71A13", "CYP71A14", "CYP71A15",
    "CYP71A16", "CYP71A17", "CYP71A18", "CYP71A19", "CYP71A20", "CYP71A21", "CYP71A22",
    "CYP71A23", "CYP71A24", "CYP71A25", "CYP71A26", "CYP71A27", "CYP71A28", "CYP71A29",
    "CYP71A30", "CYP71A31", "CYP71A32"
]

TRAIT_SYNTHESIS_GENES = [
    "CYP79D16", "CYP79D15", "CYP79D17",
    "CYP83A1", "CYP83B1",
    "CYP71A1"
    # Added based on typical defense synthesis pathways mentioned in specs
]

@dataclass
class Config:
    """
    Central configuration container.
    All paths are resolved relative to the project root unless absolute.
    """
    # Project Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_root: Path = field(default_factory=lambda: Path("data"))
    src_root: Path = field(default_factory=lambda: Path("src"))
    
    # Derived Paths (resolved at runtime)
    raw_data_dir: Path = field(init=False)
    processed_data_dir: Path = field(init=False)
    traits_dir: Path = field(init=False)
    manifests_dir: Path = field(init=False)
    synthetic_data_dir: Path = field(init=False)
    
    # Randomness
    seed: int = 42
    
    # Analysis Thresholds
    fdr_threshold: float = 0.05
    log2fc_threshold: float = 1.0
    min_replicates: int = 2
    missing_trait_threshold: float = 0.30
    cv_reduction_target: float = 0.20
    jaccard_similarity_threshold: float = 0.75
    
    # Biological Lists
    housekeeping_genes: List[str] = field(default_factory=lambda: DEFAULT_HOUSEKEEPING_GENES)
    trait_synthesis_genes: List[str] = field(default_factory=lambda: TRAIT_SYNTHESIS_GENES)
    
    # Paths for specific outputs
    post_qc_species_list_path: Path = field(init=False)
    trait_fallback_summary_path: Path = field(init=False)
    pathway_mappings_path: Path = field(init=False)
    aggregated_features_path: Path = field(init=False)
    
    def __post_init__(self):
        """Resolve relative paths to absolute paths based on project_root."""
        # Ensure project_root is absolute
        if not self.project_root.is_absolute():
            self.project_root = Path.cwd() / self.project_root
        
        # Define data subdirectories
        self.raw_data_dir = self.project_root / self.data_root / "raw"
        self.processed_data_dir = self.project_root / self.data_root / "processed"
        self.traits_dir = self.project_root / self.data_root / "traits"
        self.manifests_dir = self.project_root / self.data_root / "manifests"
        self.synthetic_data_dir = self.project_root / self.data_root / "synthetic"
        
        # Define output file paths
        self.post_qc_species_list_path = self.processed_data_dir / "post_qc_species_list.json"
        self.trait_fallback_summary_path = self.processed_data_dir / "trait_fallback_summary.json"
        self.pathway_mappings_path = self.processed_data_dir / "pathway_mappings.json"
        self.aggregated_features_path = self.processed_data_dir / "aggregated_features.csv"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a serializable dictionary."""
        d = asdict(self)
        # Convert Path objects to strings for JSON serialization
        for k, v in d.items():
            if isinstance(v, Path):
                d[k] = str(v)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary."""
        # Convert string paths back to Path objects
        for k in ["project_root", "data_root", "src_root", 
                  "raw_data_dir", "processed_data_dir", "traits_dir", 
                  "manifests_dir", "synthetic_data_dir",
                  "post_qc_species_list_path", "trait_fallback_summary_path",
                  "pathway_mappings_path", "aggregated_features_path"]:
            if k in data and isinstance(data[k], str):
                data[k] = Path(data[k])
        return cls(**data)

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to a JSON file."""
        if path is None:
            path = self.project_root / "config.json"
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from a JSON file."""
        if path is None:
            path = Path(__file__).resolve().parent.parent.parent / "config.json"
        if not path.exists():
            return cls() # Return defaults if no config file found
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

# Singleton instance for global access
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

def set_config(new_config: Config) -> None:
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = new_config

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    config = get_config()
    config.seed = seed
    random.seed(seed)
    # Note: numpy seed handling is usually done where numpy is imported
    # to avoid circular imports here.

def get_seed() -> int:
    """Get the current random seed."""
    return get_config().seed

def get_data_path() -> Path:
    """Get the root data directory path."""
    return get_config().data_root

def get_threshold(key: str) -> float:
    """Get a specific analysis threshold by key."""
    config = get_config()
    mapping = {
        "fdr": config.fdr_threshold,
        "log2fc": config.log2fc_threshold,
        "cv_reduction": config.cv_reduction_target,
        "jaccard": config.jaccard_similarity_threshold,
        "missing_trait": config.missing_trait_threshold
    }
    if key not in mapping:
        raise ValueError(f"Unknown threshold key: {key}")
    return mapping[key]

def get_housekeeping_genes() -> List[str]:
    """Get the list of housekeeping genes."""
    return get_config().housekeeping_genes

def get_trait_synthesis_genes() -> List[str]:
    """Get the list of trait synthesis genes to exclude during LOSO."""
    return get_config().trait_synthesis_genes