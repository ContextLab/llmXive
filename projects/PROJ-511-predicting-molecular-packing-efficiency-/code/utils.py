"""
Utility functions for the molecular packing efficiency project.
"""
import logging
import os
import random
import sys
from typing import Dict, Optional
import numpy as np

# Bondi van der Waals radii (in Angstroms)
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
    'Si': 2.10,
    'B': 1.73,
    'Be': 1.60,
    'Li': 1.82,
    'Na': 2.27,
    'K': 2.75,
    'Ca': 2.31,
    'Mg': 1.73,
    'Al': 1.84,
    'Fe': 2.04,
    'Cu': 1.80,
    'Zn': 1.98,
    'Ag': 2.00,
    'Au': 2.00,
    'Pt': 2.00,
    'Pd': 2.00,
    'Ni': 1.80,
    'Co': 1.80,
    'Mn': 1.80,
    'Cr': 1.80,
    'V': 1.80,
    'Ti': 1.80,
    'Sc': 1.80,
    'Y': 2.00,
    'La': 2.00,
    'Ce': 2.00,
    'Pr': 2.00,
    'Nd': 2.00,
    'Sm': 2.00,
    'Eu': 2.00,
    'Gd': 2.00,
    'Tb': 2.00,
    'Dy': 2.00,
    'Ho': 2.00,
    'Er': 2.00,
    'Tm': 2.00,
    'Yb': 2.00,
    'Lu': 2.00,
    'Hf': 2.00,
    'Ta': 2.00,
    'W': 2.00,
    'Re': 2.00,
    'Os': 2.00,
    'Ir': 2.00,
    'Ru': 2.00,
    'Rh': 2.00,
    'Mo': 2.00,
    'Nb': 2.00,
    'Zr': 2.00,
    'Ge': 2.00,
    'As': 2.00,
    'Se': 2.00,
    'Te': 2.00,
    'Bi': 2.00,
    'Pb': 2.00,
    'Sn': 2.00,
    'Ga': 2.00,
    'In': 2.00,
    'Tl': 2.00,
    'Hg': 2.00,
    'Cd': 2.00,
    'Ru': 2.00
}

def fix_seed(seed: int = 42):
    """
    Fix random seed for reproducibility.
    
    Args:
        seed: Random seed to use
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger
