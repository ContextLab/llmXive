import os
from pathlib import Path
from typing import Optional

# Project root is assumed to be the directory containing this file's parent
# or we can explicitly look for a marker file. Assuming standard layout:
# project_root/
#   code/
#     config.py
#   data/
#   .env
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

# Default paths relative to project root
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"
_DEFAULT_RAW_DIR = _DEFAULT_DATA_DIR / "raw"
_DEFAULT_PROCESSED_DIR = _DEFAULT_DATA_DIR / "processed"
_DEFAULT_RESULTS_DIR = _DEFAULT_DATA_DIR / "results"

# Materials Project API configuration
_MP_API_KEY_ENV_VAR = "MATERIALS_PROJECT_API_KEY"
_MP_API_BASE_URL = "https://next-gen.materialsproject.org/api/v3"

def _load_env_file(env_path: Path) -> None:
    """Load variables from a .env file into os.environ if it exists."""
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

def init_environment() -> None:
    """
    Initialize the environment by loading the .env file if present.
    This should be called early in the application lifecycle.
    """
    _load_env_file(_ENV_PATH)

def get_materials_project_api_key() -> str:
    """
    Retrieve the Materials Project API key.
    Raises KeyError if the key is not found in environment variables.
    """
    key = os.getenv(_MP_API_KEY_ENV_VAR)
    if not key:
        raise KeyError(
            f"Missing required environment variable '{_MP_API_KEY_ENV_VAR}'. "
            f"Please set it in your environment or add it to the '{_ENV_PATH}' file."
        )
    return key

def get_data_path() -> Path:
    """Get the base data directory path."""
    return _DEFAULT_DATA_DIR

def get_raw_data_path() -> Path:
    """Get the raw data directory path."""
    return _DEFAULT_RAW_DIR

def get_processed_data_path() -> Path:
    """Get the processed data directory path."""
    return _DEFAULT_PROCESSED_DIR

def get_results_path() -> Path:
    """Get the results directory path."""
    return _DEFAULT_RESULTS_DIR

def get_custom_dataset_path() -> Optional[Path]:
    """
    Get a custom dataset path if specified via environment variable.
    Returns None if not set.
    """
    custom_path = os.getenv("CUSTOM_DATASET_PATH")
    if custom_path:
        return Path(custom_path)
    return None

def ensure_data_directories() -> None:
    """
    Ensure that all required data directories exist.
    Creates them if they are missing.
    """
    _DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _DEFAULT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    _DEFAULT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    _DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def get_materials_project_base_url() -> str:
    """Get the base URL for the Materials Project API."""
    return _MP_API_BASE_URL

def validate_environment() -> bool:
    """
    Validate that the environment is correctly configured.
    Returns True if valid, raises an error otherwise.
    """
    try:
        get_materials_project_api_key()
    except KeyError:
        return False
    ensure_data_directories()
    return True
