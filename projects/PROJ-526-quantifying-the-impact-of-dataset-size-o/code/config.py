"""
Environment configuration management for API keys and paths.

This module handles the loading and validation of environment variables
required for the project, including API keys (e.g., HuggingFace) and
directory paths. It provides a centralized configuration object.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project root is assumed to be the parent of the 'code' directory
# Adjust if the project structure differs in the actual execution environment
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default paths relative to project root
DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"
DEFAULT_STATE_DIR = _PROJECT_ROOT / "state"
DEFAULT_DOCS_DIR = _PROJECT_ROOT / "docs"
DEFAULT_CODE_DIR = _PROJECT_ROOT / "code"

# Environment variable names
ENV_HF_TOKEN = "HF_TOKEN"
ENV_DATA_DIR = "DATA_DIR"
ENV_STATE_DIR = "STATE_DIR"
ENV_LOG_LEVEL = "LOG_LEVEL"

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Centralized configuration class.
    
    Loads settings from environment variables with sensible defaults.
    Validates critical requirements upon instantiation.
    """
    
    def __init__(self):
        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        # API Keys
        self.hf_token: Optional[str] = os.getenv(ENV_HF_TOKEN)
        
        # Paths
        # If not set in env, use defaults relative to project root
        self.data_dir = Path(os.getenv(ENV_DATA_DIR, str(DEFAULT_DATA_DIR)))
        self.state_dir = Path(os.getenv(ENV_STATE_DIR, str(DEFAULT_STATE_DIR)))
        self.docs_dir = Path(os.getenv("DOCS_DIR", str(DEFAULT_DOCS_DIR)))
        self.code_dir = Path(os.getenv("CODE_DIR", str(DEFAULT_CODE_DIR)))
        
        # Logging
        log_level = os.getenv(ENV_LOG_LEVEL, "INFO")
        self.log_level = log_level.upper()

    def _validate_config(self) -> None:
        """Validate that critical configuration is present."""
        # Check if HF token is required but missing
        # We don't strictly require it for local testing, but warn if missing
        # if the code attempts to use it.
        if not self.hf_token:
            # We will not raise an error here to allow local development without token
            # but we log a warning or set a flag.
            pass 
        
        # Ensure directories exist, create if missing
        for dir_path in [self.data_dir, self.state_dir, self.docs_dir]:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def hf_token(self) -> Optional[str]:
        return self._hf_token

    @hf_token.setter
    def hf_token(self, value: Optional[str]) -> None:
        self._hf_token = value

    def get_path(self, key: str) -> Path:
        """
        Get a path from the configuration.
        
        Args:
            key: The key name (e.g., 'data_dir', 'state_dir')
        
        Returns:
            The Path object.
        
        Raises:
            ConfigError: If the key is not found.
        """
        attr = getattr(self, key, None)
        if attr is None:
            raise ConfigError(f"Configuration key '{key}' not found.")
        return attr

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to a dictionary (excluding sensitive data)."""
        return {
            "data_dir": str(self.data_dir),
            "state_dir": str(self.state_dir),
            "docs_dir": str(self.docs_dir),
            "log_level": self.log_level,
            # Do not expose the token in the dict
            "hf_token_set": self.hf_token is not None
        }

# Global configuration instance
config = Config()

def get_config() -> Config:
    """
    Retrieve the global configuration instance.
    
    Returns:
        The global Config object.
    """
    return config

def require_hf_token() -> str:
    """
    Ensure HuggingFace token is available.
    
    Returns:
        The token string.
        
    Raises:
        ConfigError: If the token is missing.
    """
    cfg = get_config()
    if not cfg.hf_token:
        raise ConfigError(
            f"HuggingFace token not found. Please set the {ENV_HF_TOKEN} "
            "environment variable."
        )
    return cfg.hf_token

def require_data_dir() -> Path:
    """
    Ensure data directory exists and is accessible.
    
    Returns:
        The data directory path.
    """
    cfg = get_config()
    if not cfg.data_dir.exists():
        raise ConfigError(f"Data directory does not exist: {cfg.data_dir}")
    return cfg.data_dir

def require_state_dir() -> Path:
    """
    Ensure state directory exists and is accessible.
    
    Returns:
        The state directory path.
    """
    cfg = get_config()
    if not cfg.state_dir.exists():
        raise ConfigError(f"State directory does not exist: {cfg.state_dir}")
    return cfg.state_dir

if __name__ == "__main__":
    # Simple test to verify config loading
    print("Loading configuration...")
    cfg = get_config()
    print(f"Data Directory: {cfg.data_dir}")
    print(f"State Directory: {cfg.state_dir}")
    print(f"Log Level: {cfg.log_level}")
    print(f"HF Token Present: {cfg.hf_token is not None}")
    print("Configuration loaded successfully.")
