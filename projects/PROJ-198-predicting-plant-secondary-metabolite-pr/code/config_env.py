import logging
import os
from pathlib import Path
from typing import Optional, Set

from pydantic_settings import BaseSettings, SettingsConfigDict

class EnvConfig(BaseSettings):
    """Environment configuration loaded from .env or OS environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Example required variables
    NCBI_API_KEY: Optional[str] = None
    PMDB_API_TOKEN: Optional[str] = None
    CI_MODE: Optional[int] = 0

    class Config:
        env_prefix = ""

class EnvManager:
    """Singleton manager for environment variables."""

    _instance: Optional["EnvManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = EnvConfig()
        return cls._instance

    def get(self, key: str) -> Optional[str]:
        """Get an environment variable, returning None if not set."""
        return getattr(self._config, key, None)

def get_env_manager() -> EnvManager:
    """Return the singleton EnvManager instance."""
    return EnvManager()

def load_environment() -> EnvConfig:
    """Load environment configuration (ensures .env is read)."""
    return EnvConfig()

def ensure_directories(config: EnvConfig) -> None:
    """Create standard directories if they do not exist."""
    base = Path(config.model_config.get("data_root", "data"))
    for sub in ["raw", "processed", "interim", "figures", "logs"]:
        (base / sub).mkdir(parents=True, exist_ok=True)

def get_api_key(service: str, config: EnvConfig) -> Optional[str]:
    """Retrieve an API key for a given service."""
    key_name = f"{service.upper()}_API_KEY"
    return getattr(config, key_name, None)

def get_data_path(config: EnvConfig, sub_path: Optional[str] = None) -> Path:
    """Return a path inside the data directory."""
    base = Path(config.model_config.get("data_root", "data"))
    if sub_path:
        return base / sub_path
    return base

def get_logs_path(config: EnvConfig, filename: Optional[str] = None) -> Path:
    """Return a path for a log file (or the log directory)."""
    base = get_data_path(config, "logs")
    if filename:
        return base / filename
    return base

def get_figures_path(config: EnvConfig, filename: Optional[str] = None) -> Path:
    """Return a path for a figure file (or the figures directory)."""
    base = get_data_path(config, "figures")
    if filename:
        return base / filename
    return base

def validate_required_env_vars(config: EnvConfig, required_services: Set[str]) -> bool:
    """Ensure all required services have associated API keys."""
    missing = [svc for svc in required_services if not get_api_key(svc, config)]
    if missing:
        logging.warning(f"Missing API keys for services: {missing}")
        return False
    return True

def create_env_file_template() -> str:
    """Generate a minimal .env template."""
    return "NCBI_API_KEY=your_key_here\\nPMDB_API_TOKEN=your_token_here\\n"

def get_env_config() -> EnvConfig:
    """Backwards‑compatible accessor used by older code."""
    return load_environment()