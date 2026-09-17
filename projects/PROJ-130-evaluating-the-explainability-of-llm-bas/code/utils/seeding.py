"""
Environment configuration management and random seed pinning utility.
"""
import os
import random
import numpy as np
import torch
from typing import Any, Dict, Optional


_GLOBAL_SEED: Optional[int] = None
_CONFIG: Dict[str, Any] = {
    "seed": None,
    "deterministic": False,
    "cudnn_benchmark": False,
    "cudnn_deterministic": False,
}


def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility across libraries.
    
    This function sets the seed for:
    - Python's built-in random module
    - NumPy
    - PyTorch (CPU and CUDA if available)
    
    Args:
        seed (int): The random seed to use.
    """
    global _GLOBAL_SEED, _CONFIG
    
    _GLOBAL_SEED = seed
    _CONFIG["seed"] = seed
    
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy seed
    np.random.seed(seed)
    
    # Set PyTorch seeds
    torch.manual_seed(seed)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    # Configure deterministic behavior
    _CONFIG["deterministic"] = True
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    _CONFIG["cudnn_benchmark"] = False
    _CONFIG["cudnn_deterministic"] = True


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration state.
    
    Returns:
        Dict[str, Any]: A dictionary containing the current seed and 
                        deterministic configuration settings.
    """
    return _CONFIG.copy()


def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.
    
    Returns:
        Optional[int]: The global seed if set, None otherwise.
    """
    return _GLOBAL_SEED
