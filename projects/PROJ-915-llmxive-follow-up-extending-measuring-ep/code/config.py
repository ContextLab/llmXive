import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class SecretsManager:
    _instance = None
    _secrets: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_env_file(self, path: Path) -> None:
        if path.exists():
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        self._secrets[key.strip()] = value.strip()

    def get_secret(self, key: str) -> Optional[str]:
        return self._secrets.get(key)

def get_config() -> Dict[str, Any]:
    """Get configuration dictionary."""
    return {
        "MAX_RUNTIME_HOURS": 6,
        "data_dirs": {
            "raw": "data/raw",
            "processed": "data/processed",
            "interim": "data/interim",
            "results": "data/results"
        }
    }

def get_secrets() -> Dict[str, str]:
    """Get secrets."""
    return SecretsManager()._secrets

def validate_secrets(secrets: Dict[str, str]) -> bool:
    """Validate required secrets."""
    required = ["HF_TOKEN"]
    return all(key in secrets for key in required)

def get_hf_token() -> str:
    """Get Hugging Face token."""
    return SecretsManager().get_secret("HF_TOKEN")

def get_prolific_api_key() -> str:
    """Get Prolific API key."""
    return SecretsManager().get_secret("PROLIFIC_API_KEY")

def init_secrets() -> None:
    """Initialize secrets from .env file."""
    SecretsManager().load_env_file(Path(".env"))

def load_env_file(path: Path) -> None:
    """Load environment variables from file."""
    SecretsManager().load_env_file(path)

def get_secret(key: str) -> Optional[str]:
    """Get a specific secret."""
    return SecretsManager().get_secret(key)

def update_hash_state(state: Dict[str, Any], key: str, value: str) -> None:
    """Update state with hash."""
    state[key] = {
        "hash": hashlib.sha256(value.encode()).hexdigest(),
        "value": value
    }

def compute_sha256(data: str) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data.encode()).hexdigest()

class Config:
    def __init__(self):
        self.config = get_config()

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

def main():
    """Entry point for config script."""
    pass

if __name__ == "__main__":
    main()