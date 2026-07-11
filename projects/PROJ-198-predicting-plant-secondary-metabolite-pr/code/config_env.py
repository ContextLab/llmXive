"""
Environment variable management and validation.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class EnvConfig(BaseSettings):
    """Environment configuration loaded from .env or system environment."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Paths
    DATA_ROOT: Path = Field(default=Path("data"))
    LOGS_PATH: Path = Field(default=Path("logs"))
    FIGURES_PATH: Path = Field(default=Path("figures"))
    
    # API Keys
    NCBI_API_KEY: Optional[str] = Field(default=None)
    PMDB_API_KEY: Optional[str] = Field(default=None)
    
    # Flags
    CI_MODE: bool = Field(default=False)

def load_environment() -> EnvConfig:
    """Load environment configuration."""
    return EnvConfig()

def ensure_directories(cfg: Optional[EnvConfig] = None) -> None:
    """Create necessary directories if they don't exist."""
    if cfg is None:
        cfg = load_environment()
    
    dirs = [
        cfg.DATA_ROOT / "raw",
        cfg.DATA_ROOT / "processed",
        cfg.DATA_ROOT / "interim",
        cfg.LOGS_PATH,
        cfg.FIGURES_PATH,
        Path("model_cache")
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve an API key by service name.
    
    Args:
        service: 'ncbi', 'pmdb', etc.
    """
    cfg = load_environment()
    if service.lower() == "ncbi":
        return cfg.NCBI_API_KEY
    elif service.lower() == "pmdb":
        return cfg.PMDB_API_KEY
    return None

def get_data_path() -> Path:
    """Get the data root path."""
    return load_environment().DATA_ROOT

def get_logs_path() -> Path:
    """Get the logs path."""
    return load_environment().LOGS_PATH

def get_figures_path() -> Path:
    """Get the figures path."""
    return load_environment().FIGURES_PATH

def validate_required_env_vars(required: Set[str]) -> bool:
    """
    Check if all required environment variables are set.
    
    Args:
        required: Set of variable names to check.
        
    Returns:
        True if all present, False otherwise.
    """
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"Missing required environment variables: {missing}")
        return False
    return True

def create_env_file_template() -> str:
    """Generate a template .env file content."""
    return """
    # API Keys
    NCBI_API_KEY=your_ncbi_key_here
    PMDB_API_KEY=your_pmdb_key_here
    
    # Paths (relative to project root)
    DATA_ROOT=data
    LOGS_PATH=logs
    FIGURES_PATH=figures
    
    # Flags
    CI_MODE=false
    """

def get_env_config() -> EnvConfig:
    """Alias for load_environment."""
    return load_environment()
