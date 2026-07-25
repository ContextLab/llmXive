"""
Seed pinning utilities for deterministic reproducibility across all training variants.

This module provides functions to set and manage random seeds for Python, NumPy,
and PyTorch to ensure reproducible results across experiments.
"""

import os
import random
import hashlib
import numpy as np
import torch
from typing import Optional, Dict, Any, Union


def set_seed(seed: int, deterministic: bool = True) -> None:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.
    
    Args:
        seed: The random seed value to use.
        deterministic: If True, enable deterministic algorithms in PyTorch.
    """
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Set PyTorch random seeds
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    
    # Set environment variables for determinism
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    if deterministic:
        # Enable deterministic behavior in PyTorch
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        
        # Set environment variable for CuDNN
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        os.environ['CUDNN_DETERMINISTIC'] = '1'


def generate_seed_from_string(seed_string: str, offset: int = 0) -> int:
    """
    Generate a deterministic integer seed from a string input.
    
    Args:
        seed_string: The string to generate a seed from.
        offset: An optional offset to add to the generated seed.
        
    Returns:
        An integer seed value in the range [0, 2^31 - 1].
    """
    # Hash the string using SHA-256
    hash_object = hashlib.sha256(seed_string.encode('utf-8'))
    hash_bytes = hash_object.digest()
    
    # Convert first 4 bytes to an integer
    seed_value = int.from_bytes(hash_bytes[:4], byteorder='big')
    
    # Apply offset and ensure it's in valid range for 32-bit integers
    seed_value = (seed_value + offset) % (2**31 - 1)
    
    return seed_value


def get_seed_config(base_seed: int, variant_name: str, run_index: int = 0) -> Dict[str, Any]:
    """
    Generate a seed configuration dictionary for a specific variant and run.
    
    Args:
        base_seed: The base seed value for the experiment.
        variant_name: The name of the variant (e.g., 'opd', 'low_rank_rl').
        run_index: The index of the run within the variant (for multiple seeds).
        
    Returns:
        A dictionary containing the seed configuration.
    """
    # Generate a unique seed for this variant and run
    seed_string = f"{base_seed}_{variant_name}_{run_index}"
    variant_seed = generate_seed_from_string(seed_string)
    
    config = {
        'base_seed': base_seed,
        'variant_name': variant_name,
        'run_index': run_index,
        'variant_seed': variant_seed,
        'deterministic': True,
    }
    
    return config


def apply_seed_config(config: Dict[str, Any]) -> None:
    """
    Apply a seed configuration dictionary to set all random seeds.
    
    Args:
        config: A dictionary containing seed configuration (must have 'variant_seed').
    """
    if 'variant_seed' not in config:
        raise ValueError("Config must contain 'variant_seed' key")
    
    seed = config['variant_seed']
    deterministic = config.get('deterministic', True)
    
    set_seed(seed, deterministic)

def get_seed_environment() -> Optional[int]:
    """
    Check if a seed is provided via environment variable.
    
    Returns:
        The seed value if set, None otherwise.
    """
    seed_str = os.environ.get('LLMXIVE_SEED')
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            return None
    return None
