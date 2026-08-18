import os
import sys
import random
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

# Project root detection
def get_project_root() -> Path:
    """Returns the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find a marker or root
    while current.parent != current:
        if (current / ".git").exists() or (current / "requirements.txt").exists():
            return current
        current = current.parent
    # Fallback: assume src/utils is 3 levels deep
    return Path(__file__).resolve().parent.parent.parent

def get_data_path(relative_path: Optional[str] = None) -> Path:
    """
    Returns the data directory.
    Compatible with:
      1. get_data_path() -> returns root data dir
      2. get_data_path(project_root) -> returns root data dir (ignores arg if Path)
      3. get_data_path("raw") -> returns data/raw
    """
    root = get_project_root()
    data_dir = root / "data"

    if relative_path is None:
        return data_dir

    if isinstance(relative_path, Path):
        # Called with a Path object (e.g. get_data_path(project_root))
        return data_dir

    return data_dir / relative_path

def get_artifacts_path() -> Path:
    """Returns the artifacts directory."""
    root = get_project_root()
    return root / "artifacts"

def get_results_path() -> Path:
    """Returns the results directory."""
    root = get_project_root()
    return root / "data" / "results"

def ensure_directories() -> None:
    """Ensures all required directories exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "artifacts",
        root / "reports" / "plots",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    """Sets random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads a YAML configuration file if provided."""
    if config_path is None:
        return {}
    import yaml
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}
