"""
Environment configuration management for llmXive project.

Loads GitHub tokens, paths, and other settings from .env file.
Validates required environment variables and provides typed access.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    from dotenv import load_dotenv, find_dotenv
except ImportError:
    raise ImportError(
        "python-dotenv is required. Install it via: pip install python-dotenv"
    )

# Configure logging
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default paths relative to project root
DEFAULT_DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_SPECS_DIR = PROJECT_ROOT / "specs"
DEFAULT_CODE_DIR = PROJECT_ROOT / "code"

# Required environment variables
REQUIRED_ENV_VARS = [
    "GITHUB_TOKEN",
]

# Optional environment variables with defaults
OPTIONAL_ENV_VARS: Dict[str, Any] = {
    "GITHUB_API_BASE_URL": "https://api.github.com",
    "DATA_RAW_DIR": str(DEFAULT_DATA_RAW_DIR),
    "DATA_PROCESSED_DIR": str(DEFAULT_DATA_PROCESSED_DIR),
    "RESULTS_DIR": str(DEFAULT_RESULTS_DIR),
    "SPECS_DIR": str(DEFAULT_SPECS_DIR),
    "CODE_DIR": str(DEFAULT_CODE_DIR),
    "MAX_REPOS": "40",
    "RETRY_COUNT": "2",
    "LOG_LEVEL": "INFO",
}

# Global config dictionary (populated after load)
_config: Dict[str, Any] = {}
_loaded: bool = False


def load_env(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Path to .env file. If None, searches from current directory up.
    
    Returns:
        True if .env file was found and loaded, False otherwise.
    
    Raises:
        ValueError: If required environment variables are missing after loading.
    """
    global _loaded, _config
    
    if _loaded:
        logger.debug("Environment already loaded")
        return True
    
    # Find .env file
    if env_path is None:
        env_file = find_dotenv(usecwd=True)
    else:
        env_file = str(env_path)
    
    if env_file:
        loaded = load_dotenv(env_file)
        if loaded:
            logger.info(f"Loaded environment from {env_file}")
        else:
            logger.warning(f"No .env file found at {env_file}")
    else:
        logger.warning("No .env file found in project directory tree")
    
    # Load required variables
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if value is None or value.strip() == "":
            missing_vars.append(var)
        else:
            _config[var] = value
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please create a .env file in {PROJECT_ROOT} with the following: "
            f"{', '.join(missing_vars)}=<your_value>"
        )
    
    # Load optional variables with defaults
    for var, default in OPTIONAL_ENV_VARS.items():
        value = os.getenv(var, default)
        _config[var] = value
    
    _loaded = True
    logger.info("Environment configuration loaded successfully")
    return True


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: Configuration key name.
        default: Default value if key not found.
    
    Returns:
        Configuration value or default.
    """
    if not _loaded:
        load_env()
    return _config.get(key, default)


def get_github_token() -> str:
    """Get GitHub token from environment."""
    if not _loaded:
        load_env()
    token = _config.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment")
    return token


def get_data_raw_dir() -> Path:
    """Get data/raw directory path."""
    if not _loaded:
        load_env()
    return Path(_config["DATA_RAW_DIR"])


def get_data_processed_dir() -> Path:
    """Get data/processed directory path."""
    if not _loaded:
        load_env()
    return Path(_config["DATA_PROCESSED_DIR"])


def get_results_dir() -> Path:
    """Get results directory path."""
    if not _loaded:
        load_env()
    return Path(_config["RESULTS_DIR"])


def get_specs_dir() -> Path:
    """Get specs directory path."""
    if not _loaded:
        load_env()
    return Path(_config["SPECS_DIR"])


def get_code_dir() -> Path:
    """Get code directory path."""
    if not _loaded:
        load_env()
    return Path(_config["CODE_DIR"])


def get_max_repos() -> int:
    """Get maximum number of repositories to process."""
    if not _loaded:
        load_env()
    return int(_config["MAX_REPOS"])


def get_retry_count() -> int:
    """Get retry count for failed operations."""
    if not _loaded:
        load_env()
    return int(_config["RETRY_COUNT"])


def get_log_level() -> str:
    """Get logging level."""
    if not _loaded:
        load_env()
    return _config["LOG_LEVEL"]


def get_github_api_base_url() -> str:
    """Get GitHub API base URL."""
    if not _loaded:
        load_env()
    return _config["GITHUB_API_BASE_URL"]


def validate_paths() -> bool:
    """
    Validate that all required directories exist.
    
    Returns:
        True if all directories exist or can be created.
    
    Raises:
        ValueError: If a directory cannot be created.
    """
    if not _loaded:
        load_env()
    
    dirs = [
        get_data_raw_dir(),
        get_data_processed_dir(),
        get_results_dir(),
        get_specs_dir(),
        get_code_dir(),
    ]
    
    for dir_path in dirs:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            except OSError as e:
                raise ValueError(f"Cannot create directory {dir_path}: {e}")
    
    return True


def main():
    """Main entry point for testing configuration loading."""
    print("Testing environment configuration loading...")
    
    try:
        load_env()
        print("✓ Environment loaded successfully")
        
        # Test getters
        print(f"  GitHub Token: {'*' * 8} (present)")
        print(f"  Data Raw Dir: {get_data_raw_dir()}")
        print(f"  Data Processed Dir: {get_data_processed_dir()}")
        print(f"  Results Dir: {get_results_dir()}")
        print(f"  Specs Dir: {get_specs_dir()}")
        print(f"  Code Dir: {get_code_dir()}")
        print(f"  Max Repos: {get_max_repos()}")
        print(f"  Retry Count: {get_retry_count()}")
        print(f"  Log Level: {get_log_level()}")
        print(f"  GitHub API Base URL: {get_github_api_base_url()}")
        
        # Validate paths
        validate_paths()
        print("✓ All paths validated")
        
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
