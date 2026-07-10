"""
Environment variable management for API keys and local paths.

This module provides utilities to load, validate, and access environment variables
required for the llmXive plant metabolite prediction pipeline.

It integrates with the existing ConfigSettings model to ensure all required
environment variables are present before pipeline execution.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.logging import get_logger

logger = get_logger(__name__)


class EnvConfig(BaseSettings):
    """
    Configuration model for environment variables.
    
    Uses pydantic-settings to automatically load from environment variables.
    All fields are optional here, but validation happens in load_environment().
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # API Keys (optional, only required if using specific external services)
    NCBI_API_KEY: Optional[str] = Field(
        default=None,
        description="NCBI E-utilities API key for higher rate limits"
    )
    PMDB_API_KEY: Optional[str] = Field(
        default=None,
        description="PMDB (Plant Metabolic Data Resource) API key"
    )
    METABOLIGHTS_TOKEN: Optional[str] = Field(
        default=None,
        description="MetaboLights API token"
    )

    # Local Paths
    DATA_ROOT: Path = Field(
        default=Path("data"),
        description="Root directory for all data files"
    )
    DATA_RAW: Path = Field(
        default=Path("data/raw"),
        description="Directory for raw downloaded data"
    )
    DATA_PROCESSED: Path = Field(
        default=Path("data/processed"),
        description="Directory for processed analysis results"
    )
    DATA_INTERIM: Path = Field(
        default=Path("data/interim"),
        description="Directory for intermediate processing results"
    )
    LOGS_DIR: Path = Field(
        default=Path("logs"),
        description="Directory for log files"
    )
    FIGURES_DIR: Path = Field(
        default=Path("figures"),
        description="Directory for output figures and plots"
    )

    # AntiSMASH Configuration
    ANTIMASH_PATH: Optional[str] = Field(
        default=None,
        description="Path to antiSMASH executable (if not in PATH)"
    )
    ANTIMASH_DB_PATH: Optional[str] = Field(
        default=None,
        description="Path to antiSMASH database directory"
    )

    @field_validator('DATA_ROOT', 'DATA_RAW', 'DATA_PROCESSED', 'DATA_INTERIM', 'LOGS_DIR', 'FIGURES_DIR')
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        """Ensure paths are valid Path objects."""
        if not isinstance(v, Path):
            v = Path(v)
        return v


def load_environment() -> EnvConfig:
    """
    Load environment variables and return validated configuration.
    
    Returns:
        EnvConfig: Validated environment configuration object
        
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        config = EnvConfig()
        logger.info("Environment configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        raise


def ensure_directories(config: Optional[EnvConfig] = None) -> None:
    """
    Create all required directories if they don't exist.
    
    Args:
        config: EnvConfig object. If None, loads from environment.
    """
    if config is None:
        config = load_environment()
    
    directories = [
        config.DATA_ROOT,
        config.DATA_RAW,
        config.DATA_PROCESSED,
        config.DATA_INTERIM,
        config.LOGS_DIR,
        config.FIGURES_DIR
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")


def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve an API key for a specific service.
    
    Args:
        service: Service name ('ncbi', 'pmdb', 'metabolights')
        
    Returns:
        API key string or None if not configured
        
    Raises:
        ValueError: If service name is not recognized
    """
    service = service.lower()
    key_map = {
        'ncbi': 'NCBI_API_KEY',
        'pmdb': 'PMDB_API_KEY',
        'metabolights': 'METABOLIGHTS_TOKEN'
    }
    
    if service not in key_map:
        raise ValueError(f"Unknown service: {service}. Valid services: {list(key_map.keys())}")
    
    env_var = key_map[service]
    return os.getenv(env_var)


def get_data_path(subpath: Optional[str] = None) -> Path:
    """
    Get the root data path or a subpath within it.
    
    Args:
        subpath: Optional subpath relative to DATA_ROOT
        
    Returns:
        Path object for the requested location
    """
    config = load_environment()
    if subpath:
        return config.DATA_ROOT / subpath
    return config.DATA_ROOT


def get_logs_path() -> Path:
    """Get the logs directory path."""
    config = load_environment()
    return config.LOGS_DIR


def get_figures_path() -> Path:
    """Get the figures directory path."""
    config = load_environment()
    return config.FIGURES_DIR


def validate_required_env_vars(required: Set[str]) -> None:
    """
    Check that all required environment variables are set.
    
    Args:
        required: Set of required environment variable names
        
    Raises:
        ValueError: If any required variable is missing
    """
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please set them in your .env file or export them in your shell."
        )


def create_env_file_template(output_path: Optional[str] = None) -> Path:
    """
    Create a template .env file with all available configuration options.
    
    Args:
        output_path: Optional path for the output file. Defaults to .env in project root.
        
    Returns:
        Path to the created template file
    """
    if output_path is None:
        output_path = ".env"
    
    template_content = """# llmXive Plant Metabolite Prediction Pipeline - Environment Configuration
# Copy this file to .env and fill in your values
# Do not commit .env to version control

# API Keys (optional - only set if using these services)
# NCBI_API_KEY=your_ncbi_api_key_here
# PMDB_API_KEY=your_pmdb_api_key_here
# METABOLIGHTS_TOKEN=your_metabolights_token_here

# Data Paths (defaults to project-relative paths)
# DATA_ROOT=data
# DATA_RAW=data/raw
# DATA_PROCESSED=data/processed
# DATA_INTERIM=data/interim

# Logging
# LOGS_DIR=logs

# Figures
# FIGURES_DIR=figures

# AntiSMASH (optional - only if not in PATH)
# ANTIMASH_PATH=/path/to/antismash
# ANTIMASH_DB_PATH=/path/to/antismash/database
"""
    
    path = Path(output_path)
    if not path.exists():
        path.write_text(template_content)
        logger.info(f"Created .env template at {path}")
    else:
        logger.warning(f".env file already exists at {path}, not overwriting")
    
    return path


# Convenience function for use in config.py
def get_env_config() -> EnvConfig:
    """
    Get the environment configuration, ensuring directories exist.
    
    Returns:
        EnvConfig: Validated environment configuration
    """
    config = load_environment()
    ensure_directories(config)
    return config