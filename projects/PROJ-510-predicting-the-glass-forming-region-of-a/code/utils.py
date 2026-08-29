"""
Utility functions for the Glass Forming Region Prediction project.
Includes periodic table lookups and logging infrastructure.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from mendeleev import element

def get_logger(name: str = __name__) -> logging.Logger:
    """Create and configure a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_dir(directory: str) -> str:
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Retrieve properties for a chemical element using mendeleev.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu')
        
    Returns:
        Dictionary of element properties
        
    Raises:
        ValueError: If element symbol is invalid
    """
    symbol = normalize_element_symbol(symbol)
    try:
        el = element(symbol)
        return {
            'symbol': el.symbol,
            'atomic_mass': el.atomic_weight,
            'atomic_radius': el.atomic_radius,
            'electronegativity': el.electronegativity,
            'group': el.group_id,
            'period': el.period
        }
    except Exception as e:
        raise ValueError(f"Invalid element symbol: {symbol}. Error: {str(e)}")

def get_element_property(symbol: str, property_name: str) -> Any:
    """
    Retrieve a specific property for an element.
    
    Args:
        symbol: Chemical symbol
        property_name: Name of the property (e.g., 'atomic_mass')
        
    Returns:
        Property value
    """
    props = get_element_properties(symbol)
    if property_name not in props:
        raise KeyError(f"Property {property_name} not found for element {symbol}")
    return props[property_name]

def normalize_element_symbol(symbol: str) -> str:
    """Normalize element symbol to proper case (e.g., 'fe' -> 'Fe')."""
    if not symbol:
        raise ValueError("Element symbol cannot be empty")
    return symbol[0].upper() + symbol[1:].lower()

def validate_composition(composition: str) -> bool:
    """
    Validate a composition string format.
    Expected format: 'Elem1_Elem2_Elem3' or 'Elem1 Elem2 Elem3'
    """
    if not composition:
        return False
    
    # Simple check: split by common separators and verify all parts are valid symbols
    parts = composition.replace('_', ' ').split()
    for part in parts:
        try:
            normalize_element_symbol(part)
        except ValueError:
            return False
    return True
