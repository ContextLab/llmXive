import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from mendeleev import element

# Global random state seed for reproducibility
RANDOM_STATE = 42

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_dir(file_path: str):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """Get properties for an element symbol."""
    el = element(symbol)
    return {
        'atomic_radius': el.atomic_radius,
        'electronegativity': el.electronegativity,
        'melting_point': el.melting_point,
        'atomic_mass': el.atomic_mass
    }

def validate_composition(composition: str) -> bool:
    """Basic validation of composition string."""
    if not composition or not isinstance(composition, str):
        return False
    return True

def normalize_element_symbol(symbol: str) -> str:
    """Normalize element symbol to standard format."""
    return symbol.strip().capitalize()
