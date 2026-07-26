"""
Utility functions for data handling, logging, and periodic table lookups.

This module provides core infrastructure for the glass-forming region prediction pipeline,
including elemental property retrieval via mendeleev, composition validation, and directory management.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from mendeleev import element
from mendeleev.exceptions import ElementNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global random state for reproducibility across the project
RANDOM_STATE = 42

# Cache for elemental properties to avoid repeated database lookups
_element_cache: Dict[str, Dict[str, Any]] = {}

def get_element_properties(symbol: str) -> Dict[str, Any]:
    """
    Retrieve elemental properties from mendeleev with caching.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu')
        
    Returns:
        Dictionary containing atomic_radius, electronegativity, etc.
        
    Raises:
        ValueError: If element symbol is invalid or property is missing
    """
    symbol = symbol.strip().capitalize()
    
    # Check cache first
    if symbol in _element_cache:
        return _element_cache[symbol]
    
    try:
        el = element(symbol)
        
        # Retrieve properties, handling cases where mendeleev returns None
        atomic_radius = el.atomic_radius
        electronegativity = el.electronegativity
        melting_point = el.melting_point
        
        # Validate critical properties needed for thermodynamic calculations
        if atomic_radius is None:
            raise ValueError(f"Atomic radius not found for element '{symbol}'")
        if electronegativity is None:
            raise ValueError(f"Electronegativity not found for element '{symbol}'")
        
        props = {
            'symbol': el.symbol,
            'atomic_number': el.atomic_number,
            'atomic_radius': float(atomic_radius),  # pm
            'electronegativity': float(electronegativity),  # Pauling scale
            'melting_point': float(melting_point) if melting_point is not None else None,  # K
            'atomic_weight': float(el.atomic_weight),
        }
        
        # Cache the result
        _element_cache[symbol] = props
        return props
        
    except ElementNotFoundError:
        raise ValueError(f"Invalid element symbol '{symbol}': not found in mendeleev database")
    except Exception as e:
        raise ValueError(f"Error retrieving properties for element '{symbol}': {e}")

def validate_composition(composition: Dict[str, float], tolerance: float = 1e-6) -> Tuple[bool, str]:
    """
    Validate that a composition dictionary sums to 1.0 within tolerance.
    
    Args:
        composition: Dict mapping element symbols to atomic fractions
        tolerance: Acceptable deviation from 1.0
        
    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    if not composition:
        return False, "Composition dictionary is empty"
    
    # Check for valid element symbols and numeric values
    for symbol, fraction in composition.items():
        if not isinstance(fraction, (int, float)):
            return False, f"Fraction for '{symbol}' is not numeric: {fraction}"
        if fraction < 0:
            return False, f"Fraction for '{symbol}' is negative: {fraction}"
        
        # Optional: Validate element exists (expensive, so skip in tight loops if needed)
        # try:
        #     element(symbol.strip().capitalize())
        # except:
        #     return False, f"Invalid element symbol: {symbol}"
    
    total = sum(composition.values())
    if abs(total - 1.0) > tolerance:
        return False, f"Composition sum is {total:.6f}, expected 1.0 (tolerance: {tolerance})"
        
    return True, ""

def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Created directory: {path}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__ of the caller)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def normalize_element_symbol(symbol: str) -> str:
    """
    Normalize an element symbol to standard format (e.g., 'fe' -> 'Fe').
    
    Args:
        symbol: Raw element symbol string
        
    Returns:
        Standardized element symbol
        
    Raises:
        ValueError: If symbol cannot be normalized
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError(f"Invalid symbol input: {symbol}")
    
    symbol = symbol.strip()
    if len(symbol) == 1:
        return symbol.capitalize()
    elif len(symbol) == 2:
        return symbol[0].upper() + symbol[1].lower()
    else:
        # Try to find a matching element
        symbol_lower = symbol.lower()
        for el in [element(s) for s in ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
                                         'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
                                         'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
                                         'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
                                         'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd',
                                         'In', 'Sn', 'Sb', 'Te', 'I', 'Xe',
                                         'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',
                                         'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
                                         'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn',
                                         'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr']]:
            if el.symbol.lower() == symbol_lower:
                return el.symbol
        raise ValueError(f"Cannot normalize symbol: {symbol}")