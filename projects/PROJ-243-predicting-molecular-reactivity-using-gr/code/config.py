import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

_CONFIG: Optional[Dict[str, Any]] = None

def get_default_config() -> Dict[str, Any]:
    """Returns the default configuration dictionary."""
    return {
        'project_root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data_root': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'),
        'code_root': os.path.dirname(os.path.abspath(__file__)),
        'artifacts_root': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'artifacts'),
        'tests_root': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests'),
        'seed': 42,
        'log_level': logging.INFO,
        'directories': [
            'data/raw',
            'data/processed',
            'data/assets',
            'artifacts',
            'artifacts/logs',
            'artifacts/weights',
            'tests/unit',
            'tests/integration',
            'tests/contract',
            'code/utils',
            'code/models',
        ]
    }

def get_config() -> Dict[str, Any]:
    """Returns the global configuration, initializing if necessary."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = get_default_config()
    return _CONFIG

def set_config(new_config: Dict[str, Any]) -> None:
    """Updates the global configuration."""
    global _CONFIG
    _CONFIG = {**get_default_config(), **new_config}

def set_seed(seed: Optional[int] = None) -> None:
    """Sets the random seed for reproducibility."""
    if seed is None:
        seed = get_config().get('seed', 42)
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch seed setting is done in training scripts as needed

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Creates all necessary directories defined in the configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    """
    if config is None:
        config = get_config()
    
    dirs_to_create = config.get('directories', [])
    
    for dir_path in dirs_to_create:
        full_path = os.path.join(config.get('project_root', '.'), dir_path)
        os.makedirs(full_path, exist_ok=True)

def init_config_logging() -> None:
    """Initializes logging based on the current configuration."""
    config = get_config()
    log_level = config.get('log_level', logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
