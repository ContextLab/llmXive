"""
Configuration and Path Utilities.

Provides project root resolution, path helpers, and configuration loading.
Addresses API contract errors for get_data_path and get_results_path.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import random
import numpy as np

# Try to load from environment or default
PROJECT_ROOT = Path(os.getenv("LLMXIVE_PROJECT_ROOT", Path(__file__).parent.parent.parent))
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

def get_project_root() -> Path:
    """Return the project root path."""
    return PROJECT_ROOT

def get_data_path(relative_path: Optional[str] = None) -> Path:
    """
    Return the data directory path.
    
    Contract Fix: Must accept:
    1. No arguments (for T012b: get_data_path() / "raw")
    2. One argument (for T014c: get_data_path(project_root))
    
    If called with a Path object (project_root), it returns that Path / "data".
    If called with no args, it returns PROJECT_ROOT / "data".
    If called with a string, it returns PROJECT_ROOT / "data" / string.
    """
    base = PROJECT_ROOT / "data"
    
    if relative_path is None:
        # Case: get_data_path()
        return base
    
    # Check if it's a Path object (legacy call with project_root)
    if isinstance(relative_path, Path):
        # If a Path is passed, assume it's the project root and we should append "data"
        # This handles: get_data_path(project_root)
        return relative_path / "data"
    
    # Case: get_data_path("raw")
    return base / relative_path

def get_artifacts_path(relative_path: Optional[str] = None) -> Path:
    """Return the artifacts directory path."""
    base = PROJECT_ROOT / "artifacts"
    if relative_path is None:
        return base
    return base / relative_path

def get_results_path(relative_path: Optional[str] = None) -> Path:
    """
    Return the results directory path.
    
    Contract Fix: Must be importable and usable by stats.py.
    """
    base = PROJECT_ROOT / "data" / "results"
    if relative_path is None:
        return base
    return base / relative_path

def ensure_directories(*paths: Path) -> None:
    """Ensure the given paths exist, creating them if necessary."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml.
    Returns a dictionary with defaults if file is missing.
    """
    import yaml
    
    defaults = {
        "linearity_threshold": 0.7,
        "embedding_model": "all-MiniLM-L6-v2",
        "k_neighbors": 5,
        "similarity_threshold": 0.8,
        "random_seed": 42
    }
    
    if not CONFIG_PATH.exists():
        # Create a default config file if it doesn't exist
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(defaults, f)
        return defaults
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            # Merge with defaults
            return {**defaults, **(config or {})}
    except Exception as e:
        print(f"Warning: Could not load config file: {e}. Using defaults.")
        return defaults

# Ensure directories exist on import if needed (optional, can be lazy)
# ensure_directories(PROJECT_ROOT / "data" / "raw", PROJECT_ROOT / "data" / "processed", PROJECT_ROOT / "data" / "results")