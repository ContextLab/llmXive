import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(os, 'setenv'):
        os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_path() -> Path:
    """Return the path to the config directory."""
    return get_project_root() / "data" / "config"

def get_output_path() -> Path:
    """Return the path to the output directory."""
    return get_project_root() / "data" / "derived"

def get_figure_path() -> Path:
    """Return the path to the figures directory."""
    return get_project_root() / "figures"

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        "seed": int(os.getenv("RANDOM_SEED", 42)),
        "data_path": os.getenv("DATA_PATH", str(get_project_root() / "data" / "raw")),
        "output_path": os.getenv("OUTPUT_PATH", str(get_output_path())),
    }

def resolve_path(path: Union[str, Path]) -> Path:
    """Resolve a path relative to project root if relative."""
    path = Path(path)
    if not path.is_absolute():
        return get_project_root() / path
    return path

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists."""
    path = resolve_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path