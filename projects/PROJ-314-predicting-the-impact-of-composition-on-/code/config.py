import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from . import logger

_config: Dict[str, Any] = {}
_initialized = False

def initialize_config():
    global _config, _initialized
    if _initialized:
        return
    
    # Load from environment or defaults
    _config = {
        'project_root': Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent)),
        'data_source_url': os.getenv('DATA_SOURCE_URL', ''),
        'random_seed': int(os.getenv('RANDOM_SEED', '42')),
        'max_runtime_hours': int(os.getenv('MAX_RUNTIME_HOURS', '6')),
        'n_permutations': int(os.getenv('N_PERMUTATIONS', '1000')),
    }
    _initialized = True
    logger.info("Configuration initialized.")

def load_environment():
    """Load .env file if it exists."""
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    initialize_config()

def get_config_value(key: str) -> Any:
    if not _initialized:
        initialize_config()
    return _config.get(key)

def get_int_config(key: str, default: int = 0) -> int:
    val = get_config_value(key)
    if val is None:
        return default
    return int(val)

def get_float_config(key: str, default: float = 0.0) -> float:
    val = get_config_value(key)
    if val is None:
        return default
    return float(val)

def get_bool_config(key: str, default: bool = False) -> bool:
    val = get_config_value(key)
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).lower() in ('true', '1', 'yes')

def get_api_key(service: str) -> Optional[str]:
    return os.getenv(f"{service.upper()}_API_KEY")

def get_data_source_url() -> str:
    return get_config_value('data_source_url')

def get_project_config() -> Dict[str, Any]:
    return _config.copy()
