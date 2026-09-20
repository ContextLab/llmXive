"""
Configuration management utilities.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigError(Exception):
    pass

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    # Simple implementation without python-dotenv dependency if not available
    # Or assume dotenv is installed as per requirements
    try:
        from dotenv import load_dotenv
        if env_path:
            return load_dotenv(env_path)
        return load_dotenv()
    except ImportError:
        # Fallback: read .env manually
        if not env_path:
            env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"')
            return True
        return False

def get_api_key(key_name: str) -> str:
    value = os.getenv(key_name)
    if not value:
        raise ConfigError(f"Required API key '{key_name}' is missing. Please ensure it is set in the .env file or environment variables.")
    return value

def validate_environment(required_keys: List[str]) -> bool:
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise ConfigError(f"Missing API keys: {missing}")
    return True
