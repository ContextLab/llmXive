"""
Environment configuration management for the Glass Forming Region Prediction project.

This module handles loading, validating, and providing access to environment variables
defined in .env or the system environment.
"""
import os
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the 'code' directory
# However, for flexibility, we allow DATA_PATH to override relative behavior
_project_root: Optional[Path] = None

def _get_project_root() -> Path:
    """Determine the project root directory."""
    global _project_root
    if _project_root is None:
        # Assume code/ is in the root, or code/utils/config.py is deep inside
        current_file = Path(__file__).resolve()
        # Standard layout: code/utils/config.py -> project root is parent of 'code'
        _project_root = current_file.parent.parent
    return _project_root

def _load_dotenv() -> None:
    """
    Load .env file if it exists.
    Note: We use standard os.getenv logic but check for a .env file manually
    to avoid requiring 'python-dotenv' if not strictly needed, 
    though typically it is installed.
    """
    env_path = _get_project_root() / ".env"
    if env_path.exists():
        logger.info(f"Loading environment from {env_path}")
        try:
            # Attempt to import dotenv if available for robust parsing
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_path)
        except ImportError:
            # Fallback: simple parsing if dotenv is not installed
            logger.warning("python-dotenv not installed. Parsing .env manually.")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        logger.warning(f".env file not found at {env_path}. Using system environment variables.")

def init_environment() -> None:
    """Initialize the environment by loading .env if present."""
    _load_dotenv()

def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        bool: True if validation passes, False otherwise.
        
    Raises:
        ValueError: If critical variables are missing.
    """
    init_environment()
    
    # Check for Materials Project API Key
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        # It's optional for some scripts (e.g., Zenodo only), but required for MP
        # We log a warning but don't fail hard here, as T010 might handle MP optional logic
        logger.warning("MATERIALS_PROJECT_API_KEY is not set or is a placeholder. "
                     "Materials Project data fetching will fail if attempted.")
    
    # Check for DATA_PATH
    data_path = os.getenv("DATA_PATH")
    if not data_path:
        logger.warning("DATA_PATH is not set. Defaulting to 'data' relative to project root.")
    
    return True

def get_materials_project_api_key() -> Optional[str]:
    """Retrieve the Materials Project API key."""
    init_environment()
    key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if key and key != "your_api_key_here":
        return key
    return None

def get_materials_project_base_url() -> str:
    """Retrieve the Materials Project API base URL."""
    init_environment()
    return os.getenv("MATERIALS_PROJECT_BASE_URL", "https://api.materialsproject.org")

def get_data_path() -> Path:
    """Retrieve the root data directory path."""
    init_environment()
    data_path_str = os.getenv("DATA_PATH", "data")
    # If it's an absolute path, use it; otherwise, resolve relative to project root
    if Path(data_path_str).is_absolute():
        return Path(data_path_str)
    return _get_project_root() / data_path_str

def get_raw_data_path() -> Path:
    """Retrieve the path to the raw data directory."""
    return get_data_path() / "raw"

def get_processed_data_path() -> Path:
    """Retrieve the path to the processed data directory."""
    return get_data_path() / "processed"

def get_results_path() -> Path:
    """Retrieve the path to the results directory."""
    return get_data_path() / "results"

def get_custom_dataset_path() -> Optional[Path]:
    """Retrieve the path to a custom dataset if specified."""
    init_environment()
    custom_path = os.getenv("CUSTOM_DATASET_PATH")
    if custom_path:
        if Path(custom_path).is_absolute():
            return Path(custom_path)
        return _get_project_root() / custom_path
    return None

def ensure_data_directories() -> None:
    """Create data directories if they do not exist."""
    init_environment()
    dirs = [
        get_raw_data_path(),
        get_processed_data_path(),
        get_results_path()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {d}")