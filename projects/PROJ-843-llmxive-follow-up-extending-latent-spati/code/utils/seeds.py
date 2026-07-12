"""
Seed pinning utilities for reproducible experiments.

This module ensures deterministic behavior across all relevant libraries
used in the llmXive pipeline by setting random seeds for Python, NumPy,
OpenCV, and PyTorch (CPU/CUDA).
"""
import os
import random
import hashlib
from typing import Optional, Union

import numpy as np
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def set_global_seed(seed: int = 42) -> None:
    """
    Set random seeds for all major libraries to ensure reproducibility.
    
    Args:
        seed: The integer seed value to use. Defaults to 42.
    """
    # Python built-in random
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # OpenCV (if available)
    if CV2_AVAILABLE:
        cv2.setNumThreads(0)  # Ensure deterministic behavior in some ops
        # OpenCV doesn't have a global seed setter like numpy, 
        # but we ensure thread safety for reproducibility where applicable
    
    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        
        # Ensure deterministic algorithms for CPU
        if torch.backends.mkl.is_available():
            torch.set_num_threads(1)  # Force single thread for determinism
    
    # Environment variable for additional determinism
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Log the seed for traceability
    print(f"[SEED] Global random seed set to: {seed}")


def generate_seed_from_hash(input_string: str) -> int:
    """
    Generate a deterministic integer seed from a string input.
    
    Useful for deriving reproducible seeds for specific tasks or datasets
    while maintaining a base seed.
    
    Args:
        input_string: The string to hash.
        
    Returns:
        An integer seed derived from the hash.
    """
    hash_object = hashlib.sha256(input_string.encode())
    hash_hex = hash_object.hexdigest()
    # Convert first 8 hex chars to an integer
    return int(hash_hex[:8], 16)


def set_seed_for_task(task_name: str, base_seed: int = 42) -> int:
    """
    Set a unique but reproducible seed for a specific task name.
    
    Args:
        task_name: The name of the task (e.g., 'stratify', 'extract_features').
        base_seed: The base seed to use as the source of entropy.
        
    Returns:
        The generated seed for this task.
    """
    combined = f"{base_seed}_{task_name}"
    task_seed = generate_seed_from_hash(combined)
    set_global_seed(task_seed)
    return task_seed
