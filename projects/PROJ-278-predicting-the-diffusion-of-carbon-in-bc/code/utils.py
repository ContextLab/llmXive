"""Utility functions for periodic table properties and configuration."""
from pymatgen.core import Element
from typing import Optional, Dict, List, Any
import logging
import yaml
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def get_atomic_radius(symbol: str) -> float:
    """Get atomic radius for an element symbol."""
    try:
        elem = Element(symbol)
        return elem.atomic_radius
    except Exception as e:
        logger.warning(f"Could not get atomic radius for {symbol}: {e}")
        return 0.0

def get_vec(symbol: str) -> float:
    """Get valence electron count for an element symbol."""
    try:
        elem = Element(symbol)
        return elem.valence
    except Exception as e:
        logger.warning(f"Could not get VEC for {symbol}: {e}")
        return 0.0

def get_electronegativity(symbol: str) -> float:
    """Get electronegativity for an element symbol."""
    try:
        elem = Element(symbol)
        return elem.electronegativity
    except Exception as e:
        logger.warning(f"Could not get electronegativity for {symbol}: {e}")
        return 0.0

def get_properties_batch(elements: List[str]) -> Dict[str, List[float]]:
    """Get properties for a batch of elements."""
    return {
        'radius': [get_atomic_radius(e) for e in elements],
        'vec': [get_vec(e) for e in elements],
        'electronegativity': [get_electronegativity(e) for e in elements]
    }

def load_config_value(config_path: str, key: str) -> Any:
    """Load a value from the config YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get(key)
