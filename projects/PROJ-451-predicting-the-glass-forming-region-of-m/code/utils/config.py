import os
import logging
from pathlib import Path
from typing import Optional

# Configure logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the 'code' directory
# If running from 'code/', root is parent; if running from root, this logic adapts
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_env_path() -> Path:
    """Return the path to the .env file."""
    return _PROJECT_ROOT / ".env"

def load_env_vars() -> None:
    """
    Load environment variables from .env file if it exists.
    This is a simple manual loader to avoid adding 'python-dotenv' as a dependency
    unless strictly necessary, but robust enough for this task.
    """
    env_path = get_env_path()
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Environment variables may not be set.")
        return

    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value

# Load environment variables on module import
load_env_vars()

def get_materials_project_api_key() -> str:
    """
    Retrieve the Materials Project API key from the environment.
    Raises:
        ValueError: If the key is missing or empty.
    """
    key = os.getenv("MATERIALS_PROJECT_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "MATERIALS_PROJECT_API_KEY is not set in the environment or .env file. "
            "Please add it to code/.env.example (copy to .env) or set it directly."
        )
    return key

def get_materials_project_base_url() -> str:
    """
    Retrieve the Materials Project API base URL.
    Defaults to the standard v3 API URL if not set.
    """
    return os.getenv("MATERIALS_PROJECT_BASE_URL", "https://next-gen.materialsproject.org/api")

def get_zenodo_doi() -> str:
    """
    Retrieve the Zenodo DOI for the primary dataset.
    Raises:
        ValueError: If the DOI is missing or empty.
    """
    doi = os.getenv("ZENO_DO_ID", "").strip()
    if not doi:
        raise ValueError(
            "ZENO_DO_ID is not set in the environment or .env file. "
            "Please add it to code/.env.example (copy to .env) or set it directly."
        )
    return doi

def get_data_path() -> Path:
    """Return the path to the data directory."""
    return _PROJECT_ROOT / "data"

def get_raw_data_path() -> Path:
    """Return the path to the raw data directory."""
    return get_data_path() / "raw"

def get_processed_data_path() -> Path:
    """Return the path to the processed data directory."""
    return get_data_path() / "processed"

def get_results_path() -> Path:
    """Return the path to the results directory."""
    return get_data_path() / "results"

def get_custom_dataset_path() -> Path:
    """Return the path for custom datasets if needed."""
    return get_data_path() / "custom"

def ensure_data_directories() -> None:
    """Ensure all required data directories exist."""
    dirs = [
        get_data_path(),
        get_raw_data_path(),
        get_processed_data_path(),
        get_results_path(),
        get_custom_dataset_path(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directories exist at {_PROJECT_ROOT}/data")

def validate_environment() -> bool:
    """
    Validate that all critical environment variables are set and non-empty.
    Returns:
        True if validation passes.
    Raises:
        ValueError: If any critical variable is missing or empty.
    """
    try:
        get_materials_project_api_key()
        get_zenodo_doi()
        logger.info("Environment validation successful.")
        return True
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise

def init_environment() -> None:
    """
    Initialize the environment by ensuring directories exist and validating config.
    """
    ensure_data_directories()
    validate_environment()