import os
import sys
import random
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

PROJECT_ROOT: Optional[Path] = None

def get_project_root() -> Path:
    """Return the project root directory."""
    global PROJECT_ROOT
    if PROJECT_ROOT is None:
        # Attempt to find project root by looking for .git or specific files
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / ".git").exists() or (current / "pyproject.toml").exists():
                PROJECT_ROOT = current
                break
            current = current.parent
        if PROJECT_ROOT is None:
            # Fallback to assuming project root is 3 levels up from utils/config.py
            PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    return PROJECT_ROOT

def get_data_path(relative_path: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Resolve a path relative to the data directory.
    
    Handles two calling conventions:
    1. get_data_path() -> returns the data directory root
    2. get_data_path("raw") -> returns data/raw
    3. get_data_path(project_root=Path(...)) -> returns data dir for that root
    4. get_data_path("raw", project_root=Path(...)) -> returns data/raw for that root
    """
    root = project_root or get_project_root()
    data_dir = root / "data"
    
    if relative_path is None:
        return data_dir
    
    return data_dir / relative_path

def get_artifacts_path() -> Path:
    """Return the artifacts directory."""
    return get_project_root() / "artifacts"

def get_results_path() -> Path:
    """Return the results directory."""
    return get_project_root() / "data" / "results"

def ensure_directories(paths: list[Path]) -> None:
    """Ensure the given directories exist."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    import yaml
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    if not config_path.exists():
        return {}
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}
