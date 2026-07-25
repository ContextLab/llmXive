"""
Utility functions for the molecular packing efficiency project.
Includes seed fixing, logging setup, and physical constants.
"""
import logging
import os
import random
import sys
from typing import Dict, Optional
import numpy as np

# Bondi van der Waals radii in Angstroms
BONDI_RADII = {
    'H': 1.20,
    'C': 1.70,
    'N': 1.55,
    'O': 1.52,
    'F': 1.47,
    'P': 1.80,
    'S': 1.80,
    'Cl': 1.75,
    'Br': 1.85,
    'I': 1.98,
    'He': 1.40,
    'Ne': 1.54,
    'Ar': 1.88,
    'Kr': 2.02,
    'Xe': 2.16,
    'Rn': 2.20
}

def fix_seed(seed: int = 42) -> None:
    """
    Fix random seeds for reproducibility across libraries.
    
    Args:
        seed (int): Random seed to use. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not installed, skip

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_file (str, optional): Path to log file. If None, logs to console only.
        level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("molecular_packing")
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger