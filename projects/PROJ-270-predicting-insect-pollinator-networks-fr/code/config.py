import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# Project root is assumed to be the parent of the 'code' directory
# or explicitly set via environment variable
_PROJECT_ROOT: Optional[Path] = None
_CONFIG_LOADED: bool = False

# Default directory structure relative to project root
DEFAULT_DIRS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "results": "results",
    "figures": "figures",
    "logs": "logs",
    "docs": "docs",
}


def _get_project_root() -> Path:
    """
    Determines the project root directory.
    1. Checks LLMXIVE_PROJECT_ROOT env var.
    2. Falls back to the parent of the 'code' directory.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    env_root = os.getenv("LLMXIVE_PROJECT_ROOT")
    if env_root:
        _PROJECT_ROOT = Path(env_root).resolve()
    else:
        # Assume this file is at code/config.py
        current_file = Path(__file__).resolve()
        _PROJECT_ROOT = current_file.parent.parent

    return _PROJECT_ROOT


def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    return _get_project_root()


def get_data_root() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"


def get_data_raw() -> Path:
    """Returns the path to the raw data directory."""
    return get_project_root() / "data" / "raw"


def get_data_processed() -> Path:
    """Returns the path to the processed data directory."""
    return get_project_root() / "data" / "processed"


def get_results_root() -> Path:
    """Returns the path to the results directory."""
    return get_project_root() / "results"


def get_figures_root() -> Path:
    """Returns the path to the figures directory."""
    return get_project_root() / "figures"


def get_logs_root() -> Path:
    """Returns the path to the logs directory."""
    return get_project_root() / "logs"


def ensure_directories_exist() -> None:
    """Creates all standard directories if they do not exist."""
    root = get_project_root()
    for dir_name in DEFAULT_DIRS.values():
        (root / dir_name).mkdir(parents=True, exist_ok=True)


def load_env_vars() -> Dict[str, str]:
    """
    Loads environment variables relevant to the project.
    Returns a dictionary of key-value pairs.
    """
    # In a real implementation, this might load from a .env file
    # using python-dotenv. For now, it returns system env vars.
    return dict(os.environ)


def set_global_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and python.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch.random.seed() would be added if PyTorch were a dependency

# Load configuration on import to ensure paths are ready
# We wrap in try/except to allow import in environments where
# the directory structure might not be fully set up yet (e.g., initial tests)
try:
    ensure_directories_exist()
    _CONFIG_LOADED = True
except Exception:
    # Fail gracefully if we can't create dirs immediately (e.g. permissions)
    pass

class Config:
    """
    A simple configuration class to hold project settings.
    """
    def __init__(self):
        self.project_root = get_project_root()
        self.data_raw = get_data_raw()
        self.data_processed = get_data_processed()
        self.results = get_results_root()
        self.figures = get_figures_root()
        self.logs = get_logs_root()
        self.seed = 42  # Default seed

    def __repr__(self) -> str:
        return f"Config(root={self.project_root})"

# Global config instance
config = Config()