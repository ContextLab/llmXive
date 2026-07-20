"""
Utility functions for llmXive project.
Provides logging setup, deterministic seeding, and hashing utilities.
"""
import hashlib
import logging
import os
import random
from typing import Optional, Union
import numpy as np
import torch

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional file path to write logs to
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("llmxive")
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def set_deterministic_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across numpy, torch, and python random.
    
    Args:
        seed: Integer seed value
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    # Ensure deterministic behavior in torch
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def compute_sha256(data: Union[str, bytes]) -> str:
    """
    Compute SHA-256 hash of input data.
    
    Args:
        data: String or bytes to hash
        
    Returns:
        Hexadecimal string of SHA-256 hash
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()
