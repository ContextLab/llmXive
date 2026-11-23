"""
Utils.py - Shared Utilities

This module provides:
1. Logging setup.
2. Directory creation.
3. Element property lookups.
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from mendeleev import element

# Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_dir(file_path: str):
    """Ensure the directory for a file path exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """Get all relevant properties for an element."""
    try:
        el = element(symbol)
        return {
            'atomic_radius': el.atomic_radius,
            'electronegativity': el.electronegativity,
            'melting_point': el.melting_point,
            'heat_fusion': el.heat_fusion,
            'atomic_weight': el.atomic_weight
        }
    except Exception as e:
        raise ValueError(f"Element {symbol} not found in mendeleev: {e}")

def get_element_property(symbol: str, property_name: str) -> Any:
    """Get a specific property for an element."""
    props = get_element_properties(symbol)
    if property_name not in props:
        raise KeyError(f"Property {property_name} not found for {symbol}")
    return props[property_name]

def normalize_element_symbol(symbol: str) -> str:
    """Normalize element symbol to standard format (e.g., 'cu' -> 'Cu')."""
    return symbol.capitalize()

def validate_composition(composition_str: str) -> bool:
    """Validate a composition string format."""
    import re
    pattern = r'^([A-Z][a-z]?\d*\.?\d*)+$'
    return bool(re.match(pattern, composition_str))
