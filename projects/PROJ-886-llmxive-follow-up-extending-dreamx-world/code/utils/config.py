import os
import random
import logging
from typing import Optional, Dict, Any
import torch
import numpy as np

logger = logging.getLogger(__name__)

# Global seed state
_GLOBAL_SEED = None

def set_global_seed(seed: int) -> None:
    """
    Set global random seed for reproducibility across all libraries.
    
    Args:
        seed: Integer seed value (0-2^32-1)
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    
    # Set seeds for Python random
    random.seed(seed)
    
    # Set seeds for NumPy
    np.random.seed(seed)
    
    # Set seeds for PyTorch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    # Set deterministic behavior for PyTorch
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    logger.info(f"Global seed set to: {seed}")

def get_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary of configuration values
    """
    return {
        "seed": int(os.getenv("DEEPMX_SEED", "42")),
        "device": os.getenv("DEEPMX_DEVICE", "cpu"),
        "log_level": os.getenv("DEEPMX_LOG_LEVEL", "INFO"),
        "data_root": os.getenv("DEEPMX_DATA_ROOT", "./data"),
        "project_root": os.getenv("DEEPMX_PROJECT_ROOT", "."),
    }

def ensure_directories(paths: list) -> None:
    """
    Ensure that a list of directory paths exist.
    
    Args:
        paths: List of directory paths to create
    """
    from pathlib import Path
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {path}")

def init_environment(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Initialize the environment with default settings.
    
    Args:
        seed: Optional seed value (defaults to environment or 42)
        
    Returns:
        Configuration dictionary
    """
    config = get_env_config()
    
    if seed is not None:
        config["seed"] = seed
    
    set_global_seed(config["seed"])
    ensure_directories([config["data_root"], "code", "tests"])
    
    logging.basicConfig(
        level=getattr(logging, config["log_level"]),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Environment initialized")
    return config
