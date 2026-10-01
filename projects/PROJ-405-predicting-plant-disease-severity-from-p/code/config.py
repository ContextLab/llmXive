import os
from pathlib import Path
from typing import Any, Dict, Optional

# Base project root relative to this file's location (assuming code/ is at root or src/)
# We assume the script is run from the project root, so we use absolute paths relative to CWD
# or relative to a known base. To be safe, we resolve relative to the file's directory parent.
_BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration dictionary
CONFIG: Dict[str, Any] = {
    # Paths relative to project root
    "code": _BASE_DIR / "code",
    "data": _BASE_DIR / "data",
    "data_processed": _BASE_DIR / "data" / "processed",
    "data_raw": _BASE_DIR / "data" / "raw",
    "tests": _BASE_DIR / "tests",
    "artifacts": _BASE_DIR / "artifacts",
    "artifacts_models": _BASE_DIR / "artifacts" / "models",
    "artifacts_figures": _BASE_DIR / "artifacts" / "figures",
    "artifacts_logs": _BASE_DIR / "artifacts" / "logs",
    "state": _BASE_DIR / "state",
    "specs": _BASE_DIR / "specs",
    
    # Constants
    "SEED": 42,
    "RANDOM_SEED": 42,
    "WEATHER_WINDOW_DAYS": 7,
    "RAM_LIMIT_GB": 7,
    
    # API Keys (should be set via env, fallback to None)
    "OPEN_METEO_API_KEY": os.getenv("OPEN_METEO_API_KEY"),
    "NOAA_API_KEY": os.getenv("NOAA_API_KEY"),
}

def get_path(path_key: str) -> Path:
    """
    Retrieve a Path object for a given configuration key.
    
    Args:
        path_key: The key in CONFIG (e.g., 'data', 'artifacts_figures')
    
    Returns:
        Path object.
    
    Raises:
        KeyError: If the key is not found.
    """
    if path_key not in CONFIG:
        raise KeyError(f"Path key '{path_key}' not found in config.")
    
    val = CONFIG[path_key]
    if isinstance(val, Path):
        return val
    elif isinstance(val, str):
        return Path(val)
    else:
        raise ValueError(f"Value for '{path_key}' is not a valid path type.")

def ensure_dirs(path_keys: Optional[list] = None) -> None:
    """
    Ensure that directories for the given path keys exist.
    If path_keys is None, creates all directories defined in CONFIG.
    """
    keys_to_create = path_keys if path_keys else list(CONFIG.keys())
    for key in keys_to_create:
        if key.endswith("_key"): continue # Skip API keys
        try:
            p = get_path(key)
            p.mkdir(parents=True, exist_ok=True)
        except KeyError:
            pass # Skip if key doesn't exist

def get_env_or_fail(key: str, default: Optional[str] = None) -> str:
    """
    Get an environment variable. If not set and no default, raise error.
    """
    val = os.getenv(key, default)
    if val is None:
        raise ValueError(f"Environment variable '{key}' is required but not set.")
    return val
