"""
Configuration management for the project.
"""
import os
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables must be set manually.")

def get_materials_project_api_key() -> Optional[str]:
    """Retrieve Materials Project API key from environment."""
    return os.getenv('MATERIALS_PROJECT_API_KEY')

def get_materials_project_base_url() -> str:
    """Retrieve Materials Project API base URL."""
    return os.getenv('MATERIALS_PROJECT_BASE_URL', 'https://api.materialsproject.org')

def get_data_path() -> Path:
    """Get base data directory."""
    return Path(os.getenv('DATA_PATH', 'data'))

def get_raw_data_path() -> Path:
    """Get raw data directory."""
    return get_data_path() / 'raw'

def get_processed_data_path() -> Path:
    """Get processed data directory."""
    return get_data_path() / 'processed'

def get_results_path() -> Path:
    """Get results directory."""
    return get_data_path() / 'results'

def get_custom_dataset_path() -> Optional[Path]:
    """Get custom dataset path if defined."""
    path_str = os.getenv('CUSTOM_DATASET_PATH')
    return Path(path_str) if path_str else None

def ensure_data_directories() -> None:
    """Create data directories if they don't exist."""
    get_raw_data_path().mkdir(parents=True, exist_ok=True)
    get_processed_data_path().mkdir(parents=True, exist_ok=True)
    get_results_path().mkdir(parents=True, exist_ok=True)

def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    Returns True if valid, False otherwise.
    """
    api_key = get_materials_project_api_key()
    if not api_key:
        logger.warning("Materials Project API key is not set.")
        return False
    return True

def init_environment() -> None:
    """Initialize the environment (create dirs, validate)."""
    ensure_data_directories()
    if not validate_environment():
        logger.info("Environment validation failed. Continuing with limited functionality.")
