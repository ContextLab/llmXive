import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class EnvConfig(BaseSettings):
    """
    Configuration for environment variables.
    Loads from .env file, environment variables, and defaults.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys (Optional - only required if specific integrations are used)
    NCBI_API_KEY: Optional[str] = Field(None, description="NCBI E-utilities API key")
    PHYTOZOME_API_KEY: Optional[str] = Field(None, description="Phytozome API key")
    METABOLIGHTS_API_KEY: Optional[str] = Field(None, description="MetaboLights API key")
    PMDB_API_KEY: Optional[str] = Field(None, description="PMDB API key")

    # Local Paths
    DATA_ROOT: Path = Field(Path("data"), description="Root directory for data")
    CODE_ROOT: Path = Field(Path("code"), description="Root directory for code")
    LOGS_DIR: Path = Field(Path("logs"), description="Directory for log files")
    FIGURES_DIR: Path = Field(Path("figures"), description="Directory for output figures")
    STATE_DIR: Path = Field(Path("state"), description="Directory for project state")

    # Optional: Custom paths for external tools
    ANTIMASH_PATH: Optional[str] = Field(None, description="Path to antiSMASH executable")
    HMMER_PATH: Optional[str] = Field(None, description="Path to HMMER tools")

    @field_validator('DATA_ROOT', 'CODE_ROOT', 'LOGS_DIR', 'FIGURES_DIR', 'STATE_DIR')
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        if isinstance(v, str):
            return Path(v)
        return v

def load_environment() -> EnvConfig:
    """
    Load environment configuration from .env file and system variables.
    Returns:
        EnvConfig: Validated configuration object
    """
    logger.info("Loading environment configuration...")
    try:
        config = EnvConfig()
        logger.info("Environment configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        raise

def ensure_directories(config: EnvConfig) -> None:
    """
    Ensure all required directories exist.
    Creates directories if they don't exist.
    """
    directories = [
        config.DATA_ROOT,
        config.DATA_ROOT / "raw",
        config.DATA_ROOT / "processed",
        config.DATA_ROOT / "interim",
        config.CODE_ROOT,
        config.LOGS_DIR,
        config.FIGURES_DIR,
        config.STATE_DIR,
        config.STATE_DIR / "projects"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

def get_api_key(service: str, config: EnvConfig) -> Optional[str]:
    """
    Get API key for a specific service.
    Args:
        service: Service name (e.g., 'NCBI', 'PHYTOZOME')
        config: Environment configuration
    Returns:
        API key string or None if not set
    """
    key_map = {
        'NCBI': config.NCBI_API_KEY,
        'PHYTOZOME': config.PHYTOZOME_API_KEY,
        'METABOLIGHTS': config.METABOLIGHTS_API_KEY,
        'PMDB': config.PMDB_API_KEY
    }
    key = key_map.get(service.upper())
    if key:
        logger.debug(f"API key found for {service}")
    else:
        logger.warning(f"No API key found for {service}. Some features may be limited.")
    return key

def get_data_path(config: EnvConfig, sub_path: Optional[str] = None) -> Path:
    """
    Get full path for data files.
    Args:
        config: Environment configuration
        sub_path: Optional sub-path within data directory
    Returns:
        Full Path object
    """
    base = config.DATA_ROOT
    if sub_path:
        return base / sub_path
    return base

def get_logs_path(config: EnvConfig, filename: Optional[str] = None) -> Path:
    """
    Get full path for log files.
    Args:
        config: Environment configuration
        filename: Optional filename for the log file
    Returns:
        Full Path object
    """
    base = config.LOGS_DIR
    if filename:
        return base / filename
    return base

def get_figures_path(config: EnvConfig, filename: Optional[str] = None) -> Path:
    """
    Get full path for figure files.
    Args:
        config: Environment configuration
        filename: Optional filename for the figure file
    Returns:
        Full Path object
    """
    base = config.FIGURES_DIR
    if filename:
        return base / filename
    return base

def validate_required_env_vars(config: EnvConfig, required_services: Set[str]) -> bool:
    """
    Validate that API keys are present for required services.
    Args:
        config: Environment configuration
        required_services: Set of service names that require API keys
    Returns:
        True if all required keys are present, False otherwise
    """
    missing = []
    for service in required_services:
        if not get_api_key(service, config):
            missing.append(service)

    if missing:
        logger.error(f"Missing API keys for required services: {missing}")
        return False

    logger.info("All required API keys are present.")
    return True

def create_env_file_template() -> str:
    """
    Create a template .env file content.
    Returns:
        String content for .env file
    """
    return """# Environment Configuration for Plant Secondary Metabolite Prediction Project
# Copy this file to .env and fill in your values

# API Keys (Optional - only required if using specific services)
NCBI_API_KEY=your_ncbi_api_key_here
PHYTOZOME_API_KEY=your_phytozome_api_key_here
METABOLIGHTS_API_KEY=your_metabolights_api_key_here
PMDB_API_KEY=your_pmdb_api_key_here

# Local Paths (Optional - defaults to project root subdirectories)
# DATA_ROOT=data
# CODE_ROOT=code
# LOGS_DIR=logs
# FIGURES_DIR=figures
# STATE_DIR=state

# Optional: Custom paths for external tools
# ANTIMASH_PATH=/path/to/antismash
# HMMER_PATH=/path/to/hmmer
"""

def get_env_config() -> EnvConfig:
    """
    Get the global environment configuration.
    Returns:
        EnvConfig: Validated configuration object
    """
    return load_environment()