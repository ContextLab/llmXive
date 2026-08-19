"""
Environment management.
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from dotenv import load_dotenv
from .logging_config import get_logger

logger = get_logger(__name__)

def load_dotenv_file():
    load_dotenv()

def validate_api_keys():
    pass

def get_env_var(name: str, default: str = "") -> str:
    return os.getenv(name, default)

def setup_environment():
    pass

def get_huggingface_token() -> Optional[str]:
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    return os.getenv("NCBI_API_KEY")

def get_random_seed() -> int:
    return int(os.getenv("RANDOM_SEED", "42"))

def get_max_workers() -> int:
    return int(os.getenv("MAX_WORKERS", "4"))

def get_timeout_seconds() -> int:
    return int(os.getenv("TIMEOUT_SECONDS", "300"))

def get_cache_dir() -> Path:
    return Path(os.getenv("CACHE_DIR", "cache"))
