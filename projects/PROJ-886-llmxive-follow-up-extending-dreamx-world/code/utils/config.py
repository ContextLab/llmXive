import os
import random
import logging
from typing import Optional, Dict, Any
import torch
import numpy as np
from pathlib import Path

# Global seed configuration
_GLOBAL_SEED = 42

def set_global_seed(seed: int = 42):
    """Set global random seeds for reproducibility.
    
    Args:
        seed: Random seed value (default: 42)
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    logging.info(f"Global seed set to {seed}")

def get_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Dictionary containing configuration values
    """
    return {
        'seed': int(os.getenv('RANDOM_SEED', _GLOBAL_SEED)),
        'device': os.getenv('DEVICE', 'cpu'),
        'data_path': os.getenv('DATA_PATH', 'data'),
        'output_path': os.getenv('OUTPUT_PATH', 'data/derived'),
        'log_path': os.getenv('LOG_PATH', 'logs'),
    }

def ensure_directories(paths: list):
    """Ensure all specified directories exist.
    
    Args:
        paths: List of directory paths to create
    """
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
        logging.debug(f"Ensured directory: {path}")

def init_environment(seed: int = 42):
    """Initialize the environment with default settings.
    
    This function:
    1. Sets the global random seed
    2. Loads environment configuration
    3. Creates required directory structure
    
    Args:
        seed: Random seed for reproducibility (default: 42)
        
    Returns:
        Configuration dictionary from environment variables
    """
    set_global_seed(seed)
    config = get_env_config()
    
    # Ensure all required project directories exist
    ensure_directories([
        'data/raw',
        'data/derived',
        'data/derived/videos',
        'logs',
        'figures',
        'code',
        'code/models',
        'code/pipeline',
        'code/analysis',
        'code/utils',
        'tests/unit',
        'tests/integration',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/raw',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/videos',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/models',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/pipeline',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/analysis',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/utils',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/unit',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/integration',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/logs',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/docs',
        'projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/config',
    ])
    
    logging.info("Environment initialized successfully")
    return config

def get_seed() -> int:
    """Get the current global seed value.
    
    Returns:
        Current seed value
    """
    return _GLOBAL_SEED