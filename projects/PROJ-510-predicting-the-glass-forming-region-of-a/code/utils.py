"""
Utility functions for the glass-forming alloy project.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from mendeleev import element

# Constants
RANDOM_STATE = 42

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_dir(file_path: str) -> None:
    """
    Ensure the directory for a file path exists.

    Args:
        file_path: Path to file.
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def get_element_properties(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get properties for an element.

    Args:
        symbol: Element symbol.

    Returns:
        Dictionary of properties or None if not found.
    """
    try:
        sym = normalize_element_symbol(symbol)
        if sym is None:
            return None

        elem = element(sym)
        if elem is None:
            return None

        return {
            'symbol': sym,
            'atomic_radius': elem.atomic_radius,
            'electronegativity': elem.electronegativity,
            'atomic_number': elem.atomic_number,
            'atomic_mass': elem.atomic_mass
        }
    except Exception:
        return None

def validate_composition(composition_str: str) -> bool:
    """
    Validate a composition string.

    Args:
        composition_str: Composition string.

    Returns:
        True if valid.
    """
    import re
    if not isinstance(composition_str, str):
        return False

    # Basic check for element symbols
    elements = re.findall(r'[A-Z][a-z]?', composition_str.replace('_', ''))
    if not elements:
        return False

    # Verify each element exists
    for elem in elements:
        if get_element_properties(elem) is None:
            return False

    return True

def normalize_element_symbol(symbol: str) -> Optional[str]:
    """
    Normalize an element symbol to proper case.

    Args:
        symbol: Element symbol.

    Returns:
        Normalized symbol or None if invalid.
    """
    if not symbol or not isinstance(symbol, str):
        return None

    symbol = symbol.strip()
    if len(symbol) == 1:
        return symbol.upper()
    elif len(symbol) == 2:
        return symbol[0].upper() + symbol[1].lower()
    else:
        # Try to find a match
        symbol = symbol.capitalize()
        try:
            elem = element(symbol)
            if elem:
                return elem.symbol
        except Exception:
            pass
        return None
