import os
from pathlib import Path
from typing import Optional

# Project root relative to this file
_ROOT = Path(__file__).resolve().parent.parent

def get_materials_project_api_key() -> str:
    """Retrieve Materials Project API key from environment variable."""
    key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not key:
        raise RuntimeError(
            "MATERIALS_PROJECT_API_KEY environment variable not set. "
            "Please set it to your valid Materials Project API key."
        )
    return key

def get_data_path() -> Path:
    """Return the path to the data directory."""
    return _ROOT / "data"

def ensure_data_directories() -> None:
    """Create raw and processed data directories if they do not exist."""
    data_path = get_data_path()
    (data_path / "raw").mkdir(parents=True, exist_ok=True)
    (data_path / "processed").mkdir(parents=True, exist_ok=True)
    (data_path / "results").mkdir(parents=True, exist_ok=True)

def get_custom_dataset_path() -> Optional[Path]:
    """Return custom dataset path if set in environment, else None."""
    path_str = os.getenv("CUSTOM_DATASET_PATH")
    if path_str:
        return Path(path_str)
    return None

def init_environment() -> None:
    """Initialize project environment: ensure directories exist."""
    ensure_data_directories()
