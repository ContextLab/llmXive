"""
Configuration management for the project.

Handles loading of seeds, tolerances, paths, and other hyperparameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration values
DEFAULT_CONFIG = {
    "seed": 42,
    "tolerance": 1e-10,
    "matrix_size": 1000,
    "num_eigenvalues": 10,
    "perturbation_norm": 2.5,
    "sparsity_density": 0.1,
    "num_mc_iterations": 100,
    "project_root": None, # Will be resolved dynamically
}

def get_project_paths() -> Dict[str, Path]:
    """
    Resolve project directory paths relative to the execution context.
    Assumes the code is running from the project root or the code directory.
    """
    # Try to find the project root by looking for 'data' and 'state' directories
    # or by assuming the current working directory is the project root.
    cwd = Path.cwd()
    
    # Heuristic: if 'data' exists in cwd, assume cwd is root
    if (cwd / "data").exists():
        root = cwd
    else:
        # Fallback: assume we are in code/ directory
        root = cwd.parent if cwd.name == "code" else cwd

    return {
        "root": root,
        "code": root / "code",
        "data_raw": root / "data" / "raw",
        "data_processed": root / "data" / "processed",
        "state": root / "state",
        "figures": root / "data" / "figures",
        "logs": root / "data" / "logs",
    }

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file if it exists, otherwise return defaults.
    """
    paths = get_project_paths()
    if config_path is None:
        config_path = paths["root"] / "config.yaml"

    config = DEFAULT_CONFIG.copy()
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
        except ImportError:
            pass # yaml not installed, ignore config file
        except Exception as e:
            import logging
            logging.warning(f"Could not load config file {config_path}: {e}")
    
    return config

def ensure_directories(dirs: list) -> None:
    """Ensure a list of Path objects exist."""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    config = load_config()
    return int(config.get("seed", DEFAULT_CONFIG["seed"]))

def get_tolerance() -> float:
    config = load_config()
    return float(config.get("tolerance", DEFAULT_CONFIG["tolerance"]))

def get_matrix_size() -> int:
    config = load_config()
    return int(config.get("matrix_size", DEFAULT_CONFIG["matrix_size"]))

def get_num_eigenvalues() -> int:
    config = load_config()
    return int(config.get("num_eigenvalues", DEFAULT_CONFIG["num_eigenvalues"]))

def get_perturbation_norm() -> float:
    config = load_config()
    return float(config.get("perturbation_norm", DEFAULT_CONFIG["perturbation_norm"]))

def get_sparsity_density() -> float:
    config = load_config()
    return float(config.get("sparsity_density", DEFAULT_CONFIG["sparsity_density"]))

def get_num_mc_iterations() -> int:
    config = load_config()
    return int(config.get("num_mc_iterations", DEFAULT_CONFIG["num_mc_iterations"]))
