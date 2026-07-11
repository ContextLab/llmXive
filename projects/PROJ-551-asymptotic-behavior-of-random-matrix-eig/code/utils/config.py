"""
Configuration management.
Loads settings from YAML/JSON or uses defaults.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Default configuration values
DEFAULTS = {
    "random_seed": 42,
    "tolerance": 1e-10,
    "max_iterations": 1000,
    "matrix_size": 1000,
    "num_eigenvalues": 10,
    "perturbation_norm": 2.5,
    "sparsity_density": 0.1,
    "num_mc_iterations": 100,
}

def get_project_paths() -> Dict[str, Any]:
    """
    Returns a dictionary of paths for the project.
    """
    root = Path(__file__).parent.parent.parent
    return {
        "root": root,
        "code": root / "code",
        "data": {
            "raw": root / "data" / "raw",
            "processed": root / "data" / "processed",
            "logs": root / "data" / "logs",
            "figures": root / "data" / "figures",
        },
        "figures": root / "figures",
        "specs": root / "specs",
        "state": root / "state",
    }

def load_config(config_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    Defaults to 'config.yaml' in the project root if not specified.
    
    Returns a merged dictionary of default values and file values.
    """
    paths = get_project_paths()
    if config_path is None:
        config_path = paths["root"] / "config.yaml"
    else:
        config_path = Path(config_path)
    
    config = DEFAULTS.copy()
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    # Ensure paths are resolved relative to root
    if "output_dir" in config:
        config["output_dir"] = paths["root"] / config["output_dir"]
    
    return config

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Create all necessary directories for the project based on configuration.
    """
    if config is None:
        config = load_config()
    
    paths = get_project_paths()
    
    # Create data subdirectories
    for subdir in ["raw", "processed", "logs", "figures"]:
        dir_path = paths["data"][subdir]
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create figures and state directories
    paths["figures"].mkdir(parents=True, exist_ok=True)
    paths["state"].mkdir(parents=True, exist_ok=True)

def get_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the random seed from configuration.
    """
    if config is None:
        config = load_config()
    return config.get("random_seed", DEFAULTS["random_seed"])

def get_tolerance(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the numerical tolerance from configuration.
    """
    if config is None:
        config = load_config()
    return float(config.get("tolerance", DEFAULTS["tolerance"]))

def get_matrix_size(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the default matrix size from configuration.
    """
    if config is None:
        config = load_config()
    return int(config.get("matrix_size", DEFAULTS["matrix_size"]))

def get_num_eigenvalues(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the number of eigenvalues to compute from configuration.
    """
    if config is None:
        config = load_config()
    return int(config.get("num_eigenvalues", DEFAULTS["num_eigenvalues"]))

def get_perturbation_norm(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the perturbation norm from configuration.
    """
    if config is None:
        config = load_config()
    return float(config.get("perturbation_norm", DEFAULTS["perturbation_norm"]))

def get_sparsity_density(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the sparsity density from configuration.
    """
    if config is None:
        config = load_config()
    return float(config.get("sparsity_density", DEFAULTS["sparsity_density"]))

def get_num_mc_iterations(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the number of Monte Carlo iterations from configuration.
    """
    if config is None:
        config = load_config()
    return int(config.get("num_mc_iterations", DEFAULTS["num_mc_iterations"]))
