"""
Core configuration management for the llmXive project.
Handles path resolution, environment variables, and global constants.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# --- Constants ---
PROJECT_ROOT_NAME = "PROJ-899-llmxive-follow-up-extending-evalverse-pi"
DEFAULT_SEED = 42
RANDOM_SEED = DEFAULT_SEED

# --- Path Resolvers ---
_project_root: Optional[Path] = None
_data_root: Optional[Path] = None
_state_root: Optional[Path] = None
_reports_root: Optional[Path] = None
_figures_root: Optional[Path] = None
_cache_dir: Optional[Path] = None

def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    global _project_root
    if _project_root is None:
        # Try to detect from environment or current working directory
        if "LLMXIVE_PROJECT_ROOT" in os.environ:
            _project_root = Path(os.environ["LLMXIVE_PROJECT_ROOT"])
        else:
            # Default: assume script is in code/scripts/, project root is parent of code/
            current = Path(__file__).resolve()
            _project_root = current.parent.parent

        if not _project_root.exists():
            raise FileNotFoundError(f"Project root not found at {_project_root}")
    return _project_root

def get_data_root() -> Path:
    """Return the absolute path to the data directory."""
    global _data_root
    if _data_root is None:
        _data_root = get_project_root() / "data"
    return _data_root

def get_state_root() -> Path:
    """Return the absolute path to the state directory."""
    global _state_root
    if _state_root is None:
        _state_root = get_project_root() / "state"
    return _state_root

def get_reports_root() -> Path:
    """Return the absolute path to the reports directory."""
    global _reports_root
    if _reports_root is None:
        _reports_root = get_project_root() / "reports"
    return _reports_root

def get_figures_root() -> Path:
    """Return the absolute path to the figures directory."""
    global _figures_root
    if _figures_root is None:
        _figures_root = get_project_root() / "figures"
    return _figures_root

def get_cache_dir() -> Path:
    """Return the absolute path to the cache directory."""
    global _cache_dir
    if _cache_dir is None:
        # Cache can be inside data or project root, typically data/cache or ~/.cache/llmxive
        # For this project, we use data/cache as per task T009 requirements
        _cache_dir = get_data_root() / "cache"
    return _cache_dir

def get_raw_data_dir() -> Path:
    """Return the path to the raw data subdirectory."""
    return get_data_root() / "raw"

def get_processed_data_dir() -> Path:
    """Return the path to the processed data subdirectory."""
    return get_data_root() / "processed"

# --- Environment Setup ---
def ensure_environment() -> bool:
    """
    Ensure all necessary directories and configuration files exist.
    Creates directories if missing.
    Returns True if successful.
    """
    # Ensure base directories
    dirs_to_create = [
        get_data_root(),
        get_state_root(),
        get_reports_root(),
        get_figures_root(),
        get_cache_dir(),
        get_raw_data_dir(),
        get_processed_data_dir(),
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    # Ensure .gitkeep files exist in empty directories to track them in git
    for d in dirs_to_create:
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    return True

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration state.
    """
    return {
        "project_root": str(get_project_root()),
        "data_root": str(get_data_root()),
        "state_root": str(get_state_root()),
        "reports_root": str(get_reports_root()),
        "figures_root": str(get_figures_root()),
        "cache_dir": str(get_cache_dir()),
        "random_seed": RANDOM_SEED,
        "raw_data_dir": str(get_raw_data_dir()),
        "processed_data_dir": str(get_processed_data_dir()),
    }
