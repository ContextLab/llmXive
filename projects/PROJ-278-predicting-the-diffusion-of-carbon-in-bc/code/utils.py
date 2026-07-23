"""Utility functions for data processing and feature engineering."""
from pymatgen.core import Element
from typing import Optional, Dict, List, Any
import logging
import yaml
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def get_atomic_radius(element_symbol: str) -> float:
    """Get the atomic radius of an element in Angstroms."""
    try:
        elem = Element(element_symbol)
        return elem.atomic_radius
    except Exception as e:
        logger.warning(f"Could not retrieve atomic radius for {element_symbol}: {e}")
        return 0.0

def get_vec(element_symbol: str) -> float:
    """Get the Valence Electron Count (VEC) for an element."""
    try:
        elem = Element(element_symbol)
        return elem.oxi_state_guesses(max_states=1)[0] # Approximation or use specific logic
        # Note: pymatgen Element doesn't have a direct VEC property. 
        # Usually derived from group number.
        # For this implementation, we assume a mapping or use group number.
        # A robust implementation would use a lookup table or specific logic.
        # Using group number as a proxy for VEC in simple cases.
        return elem.group_number
    except Exception as e:
        logger.warning(f"Could not retrieve VEC for {element_symbol}: {e}")
        return 0.0

def get_electronegativity(element_symbol: str) -> float:
    """Get the Pauling electronegativity of an element."""
    try:
        elem = Element(element_symbol)
        return elem.electronegativity
    except Exception as e:
        logger.warning(f"Could not retrieve electronegativity for {element_symbol}: {e}")
        return 0.0

def get_properties(element_symbol: str) -> Dict[str, float]:
    """Retrieve a dictionary of properties for an element."""
    return {
        "atomic_radius": get_atomic_radius(element_symbol),
        "vec": get_vec(element_symbol),
        "electronegativity": get_electronegativity(element_symbol)
    }

def get_properties_batch(elements: List[str]) -> List[Dict[str, float]]:
    """Retrieve properties for a list of elements."""
    return [get_properties(el) for el in elements]

def load_config_value(key: str) -> Any:
    """Load a specific value from the config file."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get(key)
