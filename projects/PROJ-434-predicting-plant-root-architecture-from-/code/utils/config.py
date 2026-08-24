"""
Configuration management for the pipeline.
Task T009: Setup environment configuration management.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Holds configuration parameters loaded from environment or defaults."""
    def __init__(self, env_path: Optional[Path] = None):
        self.env_path = env_path
        self._load_env()

    def _load_env(self):
        if self.env_path and self.env_path.exists():
            load_dotenv(self.env_path)
            logger.info(f"Loaded environment from {self.env_path}")
        else:
            logger.warning(f"Environment file {self.env_path} not found, using system env vars")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)

def load_environment(env_path: Optional[Path] = None) -> Config:
    """Load environment configuration."""
    if env_path is None:
        env_path = Path.cwd() / ".env"
    return Config(env_path)

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get an environment variable."""
    return os.getenv(key, default)

def get_config(env_path: Optional[Path] = None) -> Config:
    """Get the global config instance."""
    return load_environment(env_path)

def validate_config(config: Config, required_keys: List[str]) -> bool:
    """Validate that required keys exist in the config."""
    missing = [k for k in required_keys if not config.get(k)]
    if missing:
        logger.error(f"Missing required config keys: {missing}")
        return False
    return True
