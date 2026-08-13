"""
Environment configuration management for the llmXive project.

This module handles loading environment variables from a .env file using python-dotenv,
providing typed access to API keys, file paths, and simulation parameters.

It enforces the project's path conventions and ensures required configuration
is present before execution.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load .env file from the project root if it exists
# The .env file should be in the root directory relative to where the script is run
# or explicitly specified. We look for it in the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    # If .env doesn't exist, we proceed but warn if critical vars are missing later
    pass

# Constants for directory paths relative to project root
# These are derived from the project structure defined in tasks.md
# T001a: src/, tests/
# T001b: data/ (raw, processed, derived)
# T001c: config/

PROJECT_ROOT: Path = _PROJECT_ROOT
SRC_DIR: Path = PROJECT_ROOT / "src"
TESTS_DIR: Path = PROJECT_ROOT / "tests"
DATA_DIR: Path = PROJECT_ROOT / "data"
CONFIG_DIR: Path = PROJECT_ROOT / "config"

# Data subdirectories (T005)
DATA_RAW_DIR: Path = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Path = DATA_DIR / "processed"
DATA_DERIVED_DIR: Path = DATA_DIR / "derived"

# Output directories for figures and reports
FIGURES_DIR: Path = PROJECT_ROOT / "figures"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

# Ensure directories exist (optional, can be done in setup script too)
# We do a lazy check here to avoid side effects during import unless explicitly requested
# But for configuration, we often want to ensure paths are valid.
# For now, we just define the paths. The runner will ensure they exist.

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Retrieve an environment variable.
    
    Args:
        key: The name of the environment variable.
        default: Default value if the variable is not set.
        required: If True, raise an error if the variable is missing.
    
    Returns:
        The value of the environment variable or the default.
    
    Raises:
        ValueError: If required is True and the variable is not set.
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set.")
    return value if value else default

def get_path_env_var(key: str, default: Optional[Path] = None, required: bool = False) -> Path:
    """
    Retrieve an environment variable as a Path object.
    
    Args:
        key: The name of the environment variable.
        default: Default Path value if the variable is not set.
        required: If True, raise an error if the variable is missing.
    
    Returns:
        The value of the environment variable as a Path.
    
    Raises:
        ValueError: If required is True and the variable is not set.
    """
    value_str = get_env_var(key, default=str(default) if default else None, required=required)
    if value_str is None:
        if required:
            raise ValueError(f"Required environment variable '{key}' is not set.")
        return default
    return Path(value_str)

# Configuration Accessors
# API Keys (if needed in the future)
# Example: VADER might need an API key if using a hosted service, but local VADER doesn't.
# Pushshift API key (if used for real data fetch in US2)
PUSHSHIFT_API_KEY: Optional[str] = get_env_var("PUSHSHIFT_API_KEY", required=False)

# Paths (can be overridden via env)
# Default to the constants defined above if not overridden
CUSTOM_DATA_DIR: Path = get_path_env_var("CUSTOM_DATA_DIR", default=DATA_DIR)
CUSTOM_CONFIG_DIR: Path = get_path_env_var("CUSTOM_CONFIG_DIR", default=CONFIG_DIR)

# Simulation / Runtime Config (from T006)
# These are typically in config/simulation_config.yaml, but can be overridden by env
MAX_RUNTIME_SECONDS: int = int(get_env_var("MAX_RUNTIME_SECONDS", default="3600"))
SAMPLE_SIZE_FALLBACK: int = int(get_env_var("SAMPLE_SIZE_FALLBACK", default="1000"))
USE_REAL_DATA_ONLY: bool = get_env_var("USE_REAL_DATA_ONLY", default="True").lower() in ("true", "1", "yes")

# Logging Level
LOG_LEVEL: str = get_env_var("LOG_LEVEL", default="INFO")

class Config:
    """
    Centralized configuration class for easy access to all settings.
    """
    # Paths
    project_root: Path = PROJECT_ROOT
    src_dir: Path = SRC_DIR
    tests_dir: Path = TESTS_DIR
    data_dir: Path = CUSTOM_DATA_DIR
    config_dir: Path = CUSTOM_CONFIG_DIR
    data_raw_dir: Path = data_dir / "raw"
    data_processed_dir: Path = data_dir / "processed"
    data_derived_dir: Path = data_dir / "derived"
    figures_dir: Path = FIGURES_DIR
    reports_dir: Path = REPORTS_DIR
    
    # API Keys
    pushshift_api_key: Optional[str] = PUSHSHIFT_API_KEY
    
    # Runtime
    max_runtime_seconds: int = MAX_RUNTIME_SECONDS
    sample_size_fallback: int = SAMPLE_SIZE_FALLBACK
    use_real_data_only: bool = USE_REAL_DATA_ONLY
    log_level: str = LOG_LEVEL

# Instantiate a global config object
config = Config()
