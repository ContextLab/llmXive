"""
Configuration module for llmXive project.
Provides paths, seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root is assumed to be the parent of the code/ directory
PROJECT_ROOT = Path(__file__).parent.parent

# Default hyperparameters
DEFAULT_HYPERPARAMETERS = {
    "k": 100,  # Number of singular vectors
    "n_bootstrap": 1000,  # Bootstrap iterations
    "confidence_level": 0.95,  # Standard confidence level
    "null_threshold": 0.0,  # Expected similarity under null hypothesis
    "noise_scale": 0.01,  # Noise scale for null distribution
    "seed": 42,  # Default random seed
}

# Path mappings
PATH_DEFINITIONS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "figures": "figures",
    "similarity_matrix_json": "data/processed/similarity_matrix.json",
    "anisotropy_deviation_json": "data/processed/anisotropy_deviation.json",
    "token_attribution_json": "data/processed/token_attribution_report.json",
    "permutation_result_json": "data/processed/permutation_result.json",
    "wals_validation_json": "data/processed/wals_validation.json",
    "checksums_json": "data/checksums.json",
}

def load_config() -> Dict[str, Any]:
    """Load configuration from environment or defaults."""
    config = {
        "project_root": PROJECT_ROOT,
        "hyperparameters": DEFAULT_HYPERPARAMETERS.copy(),
        "paths": {},
    }
    
    # Resolve paths
    for key, rel_path in PATH_DEFINITIONS.items():
        config["paths"][key] = PROJECT_ROOT / rel_path
    
    return config

def get_path(config: Dict[str, Any], key: str) -> Path:
    """Get a path from the configuration."""
    if key in config["paths"]:
        return config["paths"][key]
    raise KeyError(f"Path key not found: {key}")

def get_hyperparameter(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a hyperparameter from the configuration."""
    if key in config["hyperparameters"]:
        return config["hyperparameters"][key]
    if default is not None:
        return default
    raise KeyError(f"Hyperparameter not found: {key}")

def get_seed(config: Dict[str, Any]) -> Optional[int]:
    """Get the random seed from configuration."""
    return get_hyperparameter(config, "seed", None)

def ensure_dirs(path: Path) -> None:
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def get_path_str(path: Path) -> str:
    """Convert a Path to a string representation."""
    return str(path)

def update_hyperparameters(config: Dict[str, Any], updates: Dict[str, Any]) -> None:
    """Update hyperparameters in the configuration."""
    config["hyperparameters"].update(updates)

def update_paths(config: Dict[str, Any], updates: Dict[str, str]) -> None:
    """Update path definitions in the configuration."""
    for key, rel_path in updates.items():
        config["paths"][key] = PROJECT_ROOT / rel_path

def main():
    """Print current configuration (for debugging)."""
    config = load_config()
    print("Project Root:", config["project_root"])
    print("Hyperparameters:", config["hyperparameters"])
    print("Paths:")
    for key, path in config["paths"].items():
        print(f"  {key}: {path}")

if __name__ == "__main__":
    main()