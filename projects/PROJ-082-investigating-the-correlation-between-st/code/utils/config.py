import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

_PROJECT_ROOT: Optional[Path] = None

def get_project_root() -> Path:
    """Get the root directory of the project."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Assume project root is two levels up from code/utils/
        _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    return _PROJECT_ROOT

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return get_project_root() / "config.yaml"

def get_output_path(filename: str) -> Path:
    """Get the full path for an output file in data/."""
    return get_project_root() / "data" / filename

def get_figure_path(filename: str) -> Path:
    """Get the full path for a figure file in figures/."""
    return get_project_root() / "figures" / filename

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        key: val for key, val in os.environ.items()
        if key.startswith('PROJ_')
    }

def resolve_path(path_str: Union[str, Path]) -> Path:
    """Resolve a path relative to project root if relative, else absolute."""
    path = Path(path_str)
    if not path.is_absolute():
        return get_project_root() / path
    return path

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = resolve_path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
