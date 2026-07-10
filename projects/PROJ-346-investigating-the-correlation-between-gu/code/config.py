"""
Configuration management for dataset URLs and project paths.
Handles environment variable loading and validation for AGP, NHANES, and UK Biobank.
"""
import os
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

# Default fallback URLs if environment variables are not set
# These point to public repositories or documentation pages where data can be found
DEFAULT_URLS = {
    "AGP": "https://qiita.ucsd.edu/study/description/10313",
    "NHANES": "https://wwwn.cdc.gov/Nchs/Nhanes/ContinuousNhanes/Default.aspx?BeginYear=2011",
    "UK_BIOBANK": "https://biobank.ndph.ox.ac.uk/ukb/field.cgi?id=20002"
}

# Required environment variable names for dataset URLs
ENV_VAR_MAPPING = {
    "AGP": "DATASET_URL_AGP",
    "NHANES": "DATASET_URL_NHANES",
    "UK_BIOBANK": "DATASET_URL_UK_BIOBANK"
}

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assumes code/ is at project root or one level down
    current_file = Path(__file__).resolve()
    # Try to find 'code' directory in parent, or assume current dir is project root
    if current_file.parent.name == "code":
        return current_file.parent.parent
    return current_file.parent

def get_data_dir() -> Path:
    """Return the data directory path."""
    return get_project_root() / "data"

def ensure_data_dirs() -> None:
    """Create data subdirectories if they do not exist."""
    data_root = get_data_dir()
    dirs = ["raw", "processed", "qc"]
    for d in dirs:
        path = data_root / d
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {path}")

def load_dataset_urls(required_vars: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Load dataset URLs from environment variables.
    
    Args:
        required_vars: Optional list of specific dataset keys to require.
                       Defaults to all known datasets (AGP, NHANES, UK_BIOBANK).
    
    Returns:
        Dictionary mapping dataset keys to their URLs.
    
    Raises:
        ConfigError: If a required environment variable is missing or empty.
    """
    if required_vars is None:
        required_vars = list(ENV_VAR_MAPPING.keys())
    
    urls = {}
    missing_vars = []
    
    for dataset_key in required_vars:
        env_var_name = ENV_VAR_MAPPING.get(dataset_key)
        if not env_var_name:
            logger.warning(f"No environment variable mapping found for {dataset_key}")
            continue
        
        url = os.getenv(env_var_name)
        
        if url is None or url.strip() == "":
            # Check if it's strictly required based on context or if we have a default
            # For T003, we define the management, but allow defaults for runtime safety
            # However, the task asks to "Setup environment variable management",
            # so we prioritize the env var. If missing, we log a warning and use default.
            logger.warning(f"Environment variable {env_var_name} not set. Using default URL for {dataset_key}.")
            url = DEFAULT_URLS.get(dataset_key)
            if url is None:
                missing_vars.append(env_var_name)
                continue
        
        urls[dataset_key] = url
    
    if missing_vars:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    logger.info(f"Loaded dataset URLs for: {list(urls.keys())}")
    return urls

def get_config_path() -> Path:
    """Return the path to the config file if needed (e.g., .env file)."""
    return get_project_root() / ".env"

def load_dotenv_if_exists() -> None:
    """
    Attempt to load a .env file if it exists in the project root.
    Uses standard os.getenv logic, but explicitly checks for .env presence.
    Note: This implementation avoids adding 'python-dotenv' as a dependency
    if not strictly necessary, but for robustness in research pipelines,
    we assume the user might have set up a .env.
    """
    env_path = get_config_path()
    if env_path.exists():
        logger.info(f"Found .env file at {env_path}")
        # Simple parser for .env if python-dotenv is not installed
        # This ensures the task works without extra deps if possible
        try:
            from dotenv import load_dotenv as load_dotenv_ext
            load_dotenv_ext(dotenv_path=env_path)
        except ImportError:
            # Fallback: manual parsing
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
            logger.info("Loaded .env manually (python-dotenv not installed)")