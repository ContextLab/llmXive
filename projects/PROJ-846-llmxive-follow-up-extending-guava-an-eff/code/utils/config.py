"""
Configuration management for llmXive project.
Handles seeds, paths, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import random
import numpy as np
import torch

# Global configuration state
_config = {
    "seed": 42,
    "paths": {},
    "hyperparameters": {
        "latency_threshold_ms": 150,
        "training_epochs": 10,
        "learning_rate": 1e-4,
        "batch_size": 8,
        "perception_threshold": 0.5,
    }
}

def initialize_paths(project_root: Optional[Path] = None):
    """Initialize all standard project paths."""
    if project_root is None:
        # Default to parent of code/ directory
        project_root = Path(__file__).resolve().parents[2]
    
    # Define base directories
    base_dirs = {
        "project_root": project_root,
        "code": project_root / "code",
        "data": project_root / "data",
        "data_raw": project_root / "data" / "raw",
        "data_processed": project_root / "data" / "processed",
        "data_artifacts": project_root / "data" / "artifacts",
        "tests": project_root / "tests",
        "specs": project_root / "specs",
        "state": project_root / "state",
    }
    
    # Define specific file paths
    file_paths = {
        "requirements": base_dirs["code"] / "requirements.txt",
        "checksums": base_dirs["data_raw"] / "guava" / "checksums.json",
        "ground_truth_annotations": base_dirs["data_raw"] / "guava" / "ground_truth_annotations.json",
        "symbolic_dataset": base_dirs["data_processed"] / "symbolic_guava",
        "perception_log": base_dirs["data_artifacts"] / "perception_log.json",
        "training_metrics": base_dirs["data_artifacts"] / "training_metrics.json",
        "evaluation_outcomes_raw": base_dirs["data_artifacts"] / "evaluation_outcomes_raw.json",
        "categorized_outcomes": base_dirs["data_artifacts"] / "categorized_outcomes.json",
        "filtered_evaluation_outcomes": base_dirs["data_processed"] / "evaluation_outcomes.json",
        "latency_exclusion_verified": base_dirs["data_artifacts"] / "latency_exclusion_verified.json",
        "gpu_escape_log": base_dirs["data_artifacts"] / "gpu_escape_log.json",
        "evaluation_results": base_dirs["data_artifacts"] / "evaluation_results.json",
        "sc004_verification": base_dirs["data_artifacts"] / "sc004_verification.json",
    }
    
    _config["paths"].update(base_dirs)
    _config["paths"].update(file_paths)

def get_path(key: str) -> Path:
    """Get a specific path by key."""
    if key not in _config["paths"]:
        raise KeyError(f"Path key '{key}' not found in configuration.")
    return _config["paths"][key]

def set_hyperparameter(key: str, value: Any):
    """Set a hyperparameter value."""
    _config["hyperparameters"][key] = value

def get_hyperparameter(key: str, default: Any = None) -> Any:
    """Get a hyperparameter value."""
    return _config["hyperparameters"].get(key, default)

def set_global_seed(seed: int):
    """Set global random seeds for reproducibility."""
    _config["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories():
    """Ensure all required directories exist."""
    for path in _config["paths"].values():
        if isinstance(path, Path) and "directory" in str(path).lower() or path.suffix == "":
            # Heuristic: if it looks like a directory path or has no extension
            # Actually, let's be explicit: only create known directories
            pass
    
    # Explicit directory creation
    dirs_to_create = [
        _config["paths"]["data_raw"],
        _config["paths"]["data_processed"],
        _config["paths"]["data_artifacts"],
        _config["paths"]["state"],
        _config["paths"]["code"],
    ]
    
    for d in dirs_to_create:
        if d:
            d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "seed": _config["seed"],
        "hyperparameters": _config["hyperparameters"],
        "paths": {k: str(v) for k, v in _config["paths"].items()}
    }

# Initialize paths on module load
initialize_paths()
