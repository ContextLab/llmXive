"""
Configuration and path management for the research pipeline.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Project root is assumed to be the directory containing 'code/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Random seed for reproducibility
DEFAULT_SEED = 42

def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across libraries.
    
    Args:
        seed: The random seed to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If using PyTorch or TensorFlow, set their seeds here too
    # torch.manual_seed(seed)
    # tf.random.set_seed(seed)

def get_paths() -> Dict[str, Path]:
    """
    Get all relevant directory paths for the project.
    
    Returns:
        Dict: Mapping of directory names to Path objects.
    """
    return {
        "root": PROJECT_ROOT,
        "code": PROJECT_ROOT / "code",
        "data": PROJECT_ROOT / "data",
        "data_raw": PROJECT_ROOT / "data" / "raw",
        "data_processed": PROJECT_ROOT / "data" / "processed",
        "data_artifacts": PROJECT_ROOT / "data" / "artifacts",
        "tests": PROJECT_ROOT / "tests",
        "docs": PROJECT_ROOT / "docs",
        "state": PROJECT_ROOT / "state",
        "state_projects": PROJECT_ROOT / "state" / "projects",
        "figures": PROJECT_ROOT / "figures",
        "contracts": PROJECT_ROOT / "contracts",
        "specs": PROJECT_ROOT / "specs"
    }

def ensure_directories(path_list: list[Path]) -> None:
    """
    Ensure that the given list of directories exist.
    
    Args:
        path_list: List of Path objects to create.
    """
    for p in path_list:
        p.mkdir(parents=True, exist_ok=True)

def main():
    """CLI entry point for config inspection."""
    paths = get_paths()
    print("Project Paths:")
    for name, path in paths.items():
        print(f"  {name}: {path}")

if __name__ == "__main__":
    main()
