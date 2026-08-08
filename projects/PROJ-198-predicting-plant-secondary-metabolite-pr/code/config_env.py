"""
Environment configuration management for the llmXive project.
Handles API keys, local paths, and directory validation.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class EnvConfig(BaseSettings):
    """
    Pydantic model for environment variables.
    Loads from .env file if present, otherwise from system environment.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys
    NCBI_API_KEY: Optional[str] = Field(default=None, description="NCBI API Key for rate limit increases")
    METABOLIGHTS_API_KEY: Optional[str] = Field(default=None, description="MetaboLights API Key")
    PMDB_ACCESS_TOKEN: Optional[str] = Field(default=None, description="PMDB Access Token")

    # Data Paths
    DATA_ROOT_DIR: str = Field(default="data", description="Root directory for all data")
    DATA_RAW_DIR: str = Field(default="data/raw", description="Directory for raw downloaded data")
    DATA_PROCESSED_DIR: str = Field(default="data/processed", description="Directory for processed data")
    DATA_INTERIM_DIR: str = Field(default="data/interim", description="Directory for intermediate data")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE_PATH: str = Field(default="logs/project.log", description="Path to log file")

    # Figures
    FIGURES_DIR: str = Field(default="figures", description="Directory for output figures")

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got: {v}")
        return v.upper()

def load_environment() -> EnvConfig:
    """
    Load environment configuration from .env or system environment.
    Returns a validated EnvConfig object.
    """
    try:
        config = EnvConfig()
        logger.debug("Environment configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        raise

def ensure_directories(config: Optional[EnvConfig] = None) -> None:
    """
    Ensure all required directories exist based on configuration.
    Creates directories if they don't exist.
    """
    if config is None:
        config = load_environment()

    dirs_to_create = [
        config.DATA_ROOT_DIR,
        config.DATA_RAW_DIR,
        config.DATA_PROCESSED_DIR,
        config.DATA_INTERIM_DIR,
        Path(config.LOG_FILE_PATH).parent,
        config.FIGURES_DIR
    ]

    for dir_path in dirs_to_create:
        path_obj = Path(dir_path)
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path_obj}")
        else:
            logger.debug(f"Directory already exists: {path_obj}")

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve an API key for a specific service.

    Args:
        service: Service name ('ncbi', 'metabolights', 'pmdb')

    Returns:
        The API key string or None if not configured
    """
    config = load_environment()
    service_map = {
        'ncbi': config.NCBI_API_KEY,
        'metabolights': config.METABOLIGHTS_API_KEY,
        'pmdb': config.PMDB_ACCESS_TOKEN
    }

    key = service_map.get(service.lower())
    if key is None:
        logger.warning(f"No API key configured for {service}")
    return key

def get_data_path(subdir: Optional[str] = None) -> Path:
    """
    Get a path within the data directory structure.

    Args:
        subdir: Optional subdirectory relative to DATA_ROOT_DIR

    Returns:
        Path object to the requested location
    """
    config = load_environment()
    base = Path(config.DATA_ROOT_DIR)
    if subdir:
        return base / subdir
    return base

def get_logs_path() -> Path:
    """
    Get the path to the log file.

    Returns:
        Path object to the log file
    """
    config = load_environment()
    return Path(config.LOG_FILE_PATH)

def get_figures_path() -> Path:
    """
    Get the path to the figures directory.

    Returns:
        Path object to the figures directory
    """
    config = load_environment()
    return Path(config.FIGURES_DIR)

def validate_required_env_vars(required_keys: Set[str]) -> None:
    """
    Validate that all required environment variables are set.

    Args:
        required_keys: Set of environment variable names that must be present

    Raises:
        ValueError: If any required variable is missing or empty
    """
    config = load_environment()
    missing = []

    # Map common names to config attributes
    key_map = {
        'NCBI_API_KEY': 'NCBI_API_KEY',
        'METABOLIGHTS_API_KEY': 'METABOLIGHTS_API_KEY',
        'PMDB_ACCESS_TOKEN': 'PMDB_ACCESS_TOKEN'
    }

    for key in required_keys:
        attr_name = key_map.get(key.upper(), key.upper())
        value = getattr(config, attr_name, None)
        if not value:
            missing.append(key)

    if missing:
        raise ValueError(f"Missing required environment variables: {missing}. "
                       f"Please set them in your .env file or system environment.")

def create_env_file_template() -> str:
    """
    Generate a template for the .env file.

    Returns:
        String content for a .env file template
    """
    return """
# Environment Configuration for llmXive Project
# Copy this file to .env and fill in your values
# DO NOT commit .env to version control

# API Keys (if external services are used)
# NCBI API Key (optional, increases rate limits)
NCBI_API_KEY=

# MetaboLights API Key (if required by specific endpoints)
METABOLIGHTS_API_KEY=

# PMDB Access Token (if required)
PMDB_ACCESS_TOKEN=

# Local Path Configuration
# Root directory for all project data
DATA_ROOT_DIR=data

# Subdirectories (usually derived from DATA_ROOT_DIR, but can be overridden)
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed
DATA_INTERIM_DIR=data/interim

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/project.log

# Figures output directory
FIGURES_DIR=figures
""".strip()

def get_env_config() -> Dict[str, Any]:
    """
    Get a dictionary representation of the current environment configuration.

    Returns:
        Dictionary with configuration values (API keys masked)
    """
    config = load_environment()
    config_dict = config.model_dump()

    # Mask sensitive values
    sensitive_keys = {'NCBI_API_KEY', 'METABOLIGHTS_API_KEY', 'PMDB_ACCESS_TOKEN'}
    for key in sensitive_keys:
        if key in config_dict and config_dict[key]:
            config_dict[key] = "***"

    return config_dict
