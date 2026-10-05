import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_path(relative_path: str) -> Path:
    """Get absolute path from project root."""
    return get_project_root() / relative_path

def get_hyperparameter(name: str, default: Any = None) -> Any:
    """Get hyperparameter from environment or return default."""
    return os.environ.get(name.upper(), default)

def set_deterministic_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def ensure_dirs_exist(*paths: Path) -> None:
    """Ensure all given directories exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
