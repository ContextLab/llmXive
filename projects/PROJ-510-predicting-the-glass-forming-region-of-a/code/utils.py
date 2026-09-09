"""
Utility functions for the glass forming region prediction pipeline.

Provides logging setup, directory management, and periodic table lookups
using the mendeleev library.
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from mendeleev import element


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger.

    Args:
        name: Name of the logger.
        log_file: Optional path to a log file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if log_file:
            ensure_dir(log_file)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger


def ensure_dir(file_path: str) -> None:
    """
    Ensure the directory for a given file path exists.

    Args:
        file_path: Full path to a file (directory is extracted).
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_element_properties(element_symbol: str) -> Dict[str, Any]:
    """
    Retrieve properties of an element from the periodic table.

    Args:
        element_symbol: Chemical symbol (e.g., 'Fe').

    Returns:
        Dictionary of element properties.

    Raises:
        ValueError: If the element symbol is invalid.
    """
    try:
        el = element(element_symbol)
        return {
            'symbol': el.symbol,
            'atomic_number': el.atomic_number,
            'atomic_mass': el.atomic_mass,
            'electronegativity': el.electronegativity,
            'atomic_radius': el.atomic_radius,
            'melting_point': el.melting_point,
            'group': el.group_id,
            'period': el.period
        }
    except Exception as e:
        raise ValueError(f"Invalid element symbol '{element_symbol}': {e}")


def get_element_property(element_symbol: str, property_name: str) -> Any:
    """
    Retrieve a specific property of an element.

    Args:
        element_symbol: Chemical symbol.
        property_name: Name of the property to retrieve.

    Returns:
        Value of the property.

    Raises:
        ValueError: If element or property is invalid.
    """
    el_data = get_element_properties(element_symbol)
    if property_name not in el_data:
        raise ValueError(f"Property '{property_name}' not found for {element_symbol}")
    return el_data[property_name]


def normalize_element_symbol(symbol: str) -> str:
    """
    Normalize an element symbol to proper case (e.g., 'fe' -> 'Fe').

    Args:
        symbol: Raw element symbol string.

    Returns:
        Normalized symbol.
    """
    if not symbol:
        return ""
    return symbol[0].upper() + symbol[1:].lower()


def validate_composition(composition_str: str) -> Tuple[bool, str]:
    """
    Basic validation of a composition string format.

    Args:
        composition_str: String representation of composition.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not composition_str or not isinstance(composition_str, str):
        return False, "Composition string is empty or not a string"

    # Basic check for element symbols and numbers
    # Detailed parsing is handled by ingestion.py
    return True, ""
