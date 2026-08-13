import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from . import logger

def load_environment():
    load_dotenv()

def initialize_config():
    load_environment()

def get_config_value(key: str, default: Any = None) -> Any:
    return os.getenv(key, default)

def get_int_config(key: str, default: int = 0) -> int:
    val = os.getenv(key)
    return int(val) if val else default

def get_float_config(key: str, default: float = 0.0) -> float:
    val = os.getenv(key)
    return float(val) if val else default

def get_bool_config(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes')

def get_api_key(service: str) -> Optional[str]:
    return os.getenv(f"{service.upper()}_API_KEY")

def get_data_source_url() -> str:
    return os.getenv("DATA_SOURCE_URL", "https://huggingface.co/datasets/materials-science/ceramic-reliability")

def get_memory_limit() -> int:
    return get_int_config("MEMORY_LIMIT_GB", 6)

def get_project_config() -> Dict[str, Any]:
    return {
        "memory_limit_gb": get_memory_limit(),
        "data_source": get_data_source_url()
    }
