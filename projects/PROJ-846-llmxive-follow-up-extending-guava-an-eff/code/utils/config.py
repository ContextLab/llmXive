"""
Configuration management for the project.
Handles paths, seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import random
import numpy as np
import torch

# Global configuration dictionary
_CONFIG: Dict[str, Any] = {
    "seed": 42,
    "paths": {},
    "hyperparameters": {
        "io_safety_factor": 2.0,
        "max_latency_ms": 150.0,
        "max_dataset_hours": 4.0,
        "estimated_frame_count": 100000,
    }
}

def initialize_paths(project_root: Optional[Path] = None):
    """Initialize standard directory paths."""
    if project_root is None:
        # Default to current directory if not specified
        project_root = Path.cwd()
    
    # Define standard paths relative to project root
    # Adjust based on actual project structure
    _CONFIG["paths"] = {
        "root": project_root,
        "code": project_root / "code",
        "data": project_root / "data",
        "data_raw": project_root / "data" / "raw",
        "data_processed": project_root / "data" / "processed",
        "data_artifacts": project_root / "data" / "artifacts",
        "models": project_root / "code" / "models",
        "tests": project_root / "tests",
        "state": project_root / "state",
    }
    
    # Ensure directories exist
    ensure_directories()

def get_path(key: str) -> Path:
    """Get a configured path."""
    if key not in _CONFIG["paths"]:
        raise ValueError(f"Path key '{key}' not found in configuration.")
    return _CONFIG["paths"][key]

def set_hyperparameter(key: str, value: Any):
    """Set a hyperparameter value."""
    _CONFIG["hyperparameters"][key] = value

def get_hyperparameter(key: str, default: Any = None) -> Any:
    """Get a hyperparameter value."""
    if key in _CONFIG["hyperparameters"]:
        return _CONFIG["hyperparameters"][key]
    return default

def set_global_seed(seed: Optional[int] = None):
    """Set the random seed for reproducibility."""
    if seed is None:
        seed = _CONFIG.get("seed", 42)
    
    _CONFIG["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories():
    """Create all required directories if they don't exist."""
    for key, path in _CONFIG["paths"].items():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "seed": _CONFIG["seed"],
        "paths": {k: str(v) for k, v in _CONFIG["paths"].items()},
        "hyperparameters": _CONFIG["hyperparameters"].copy()
    }

# Initialize paths on module load if __main__ or if explicitly called
# For library usage, users should call initialize_paths() explicitly
# initialize_paths()