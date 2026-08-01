import logging
import os
import random
import sys
from typing import Dict, Optional
import numpy as np

# Bondi radii for van der Waals calculations (in Angstroms)
BONDI_RADII = {
    'H': 1.20, 'He': 1.40,
    'Li': 1.82, 'Be': 1.53, 'B': 1.92, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'F': 1.47, 'Ne': 1.54,
    'Na': 2.27, 'Mg': 1.73, 'Al': 1.84, 'Si': 2.10, 'P': 1.80, 'S': 1.80, 'Cl': 1.75, 'Ar': 1.88,
    'K': 2.75, 'Ca': 2.31, 'Sc': 2.23, 'Ti': 2.14, 'V': 2.05, 'Cr': 2.05, 'Mn': 2.05, 'Fe': 2.04,
    'Co': 2.00, 'Ni': 1.99, 'Cu': 1.90, 'Zn': 1.90, 'Ga': 1.87, 'Ge': 1.87, 'As': 1.85, 'Se': 1.90,
    'Br': 1.85, 'Kr': 2.02, 'Rb': 3.03, 'Sr': 2.49, 'Y': 2.27, 'Zr': 2.06, 'Nb': 2.08, 'Mo': 2.05,
    'Tc': 2.05, 'Ru': 2.04, 'Rh': 2.00, 'Pd': 1.94, 'Ag': 1.88, 'Cd': 1.92, 'In': 1.93, 'Sn': 2.01,
    'Sb': 2.06, 'Te': 2.06, 'I': 1.98, 'Xe': 2.16, 'Cs': 3.43, 'Ba': 2.68, 'La': 2.38, 'Ce': 2.36,
    'Pr': 2.35, 'Nd': 2.34, 'Pm': 2.33, 'Sm': 2.32, 'Eu': 2.31, 'Gd': 2.30, 'Tb': 2.29, 'Dy': 2.28,
    'Ho': 2.27, 'Er': 2.26, 'Tm': 2.25, 'Yb': 2.24, 'Lu': 2.23, 'Hf': 2.11, 'Ta': 2.09, 'W': 2.06,
    'Re': 2.05, 'Os': 2.04, 'Ir': 2.02, 'Pt': 2.01, 'Au': 1.98, 'Hg': 1.90, 'Tl': 1.96, 'Pb': 2.02,
    'Bi': 2.07, 'Po': 2.10, 'At': 2.10, 'Rn': 2.10, 'Fr': 3.48, 'Ra': 2.83, 'Ac': 2.47, 'Th': 2.41,
    'Pa': 2.36, 'U': 2.35, 'Np': 2.33, 'Pu': 2.32, 'Am': 2.31, 'Cm': 2.30, 'Bk': 2.29, 'Cf': 2.28,
    'Es': 2.27, 'Fm': 2.26, 'Md': 2.25, 'No': 2.24, 'Lr': 2.23
}

def fix_seed(seed: int = 42) -> None:
    """
    Fix random seeds for reproducibility.
    
    Args:
        seed: Random seed value
    """
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger('molecular_packing')
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger