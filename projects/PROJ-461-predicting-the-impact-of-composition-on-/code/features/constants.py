"""
Base constants module for periodic table references.

This module provides access to elemental properties using the mendeleev library.
It exposes functions to retrieve atomic mass, atomic radius, and electronegativity
for chemical elements by symbol.
"""

from typing import Optional

try:
    from mendeleev import element
    from mendeleev.models import Element as MendeleevElement
except ImportError:
    raise ImportError(
        "The 'mendeleev' library is required to access periodic table data. "
        "Please install it via: pip install mendeleev"
    )

# Cache for element objects to avoid repeated lookups
_element_cache: dict[str, MendeleevElement] = {}

def _get_element(symbol: str) -> MendeleevElement:
    """
    Retrieve a Mendeleev Element object, using a cache for efficiency.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu').
        
    Returns:
        MendeleevElement object.
        
    Raises:
        ValueError: If the symbol is invalid or not found in the periodic table.
    """
    symbol = symbol.strip().capitalize()
    if symbol not in _element_cache:
        elem = element(symbol)
        if elem is None:
            raise ValueError(f"Invalid chemical symbol: {symbol}")
        _element_cache[symbol] = elem
    return _element_cache[symbol]

def get_atomic_mass(symbol: str) -> float:
    """
    Get the standard atomic mass of an element in atomic mass units (u).
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu').
        
    Returns:
        Atomic mass as a float.
        
    Raises:
        ValueError: If the symbol is invalid.
        AttributeError: If the atomic mass is not available for the element.
    """
    elem = _get_element(symbol)
    if elem.atomic_mass is None:
        raise AttributeError(f"Atomic mass not available for {symbol}")
    return float(elem.atomic_mass)

def get_atomic_radius(symbol: str, radius_type: str = "atomic") -> float:
    """
    Get the atomic radius of an element in picometers (pm).
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu').
        radius_type: Type of radius to retrieve. Options include:
            - 'atomic' (default): General atomic radius
            - 'covalent': Covalent radius
            - 'vdw': Van der Waals radius
            - 'ionic': Ionic radius (requires specific charge context, usually avoided here)
        
    Returns:
        Atomic radius as a float.
        
    Raises:
        ValueError: If the symbol is invalid or the specific radius is missing.
    """
    elem = _get_element(symbol)
    
    # Map common radius types to mendeleev attributes
    attr_map = {
        "atomic": "atomic_radius",
        "covalent": "covalent_radius",
        "vdw": "vdw_radius",
        "empirical": "empirical_radius",
        "calculated": "calculated_radius",
    }
    
    if radius_type not in attr_map:
        # Try to use the attribute name directly if not in map
        attr_name = radius_type
    else:
        attr_name = attr_map[radius_type]
    
    radius = getattr(elem, attr_name, None)
    
    if radius is None:
        # Fallback: try 'atomic_radius' if specific type missing
        radius = getattr(elem, "atomic_radius", None)
    
    if radius is None:
        raise AttributeError(f"Atomic radius not available for {symbol} (type: {radius_type})")
    
    return float(radius)

def get_electronegativity(symbol: str, scale: str = "pauling") -> float:
    """
    Get the electronegativity of an element.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu').
        scale: Electronegativity scale. Default is 'pauling'.
               Mendeleev primarily uses Pauling scale by default.
        
    Returns:
        Electronegativity value as a float.
        
    Raises:
        ValueError: If the symbol is invalid.
        AttributeError: If the electronegativity is not available.
    """
    elem = _get_element(symbol)
    
    if scale.lower() == "pauling":
        value = elem.electronegativity
    else:
        # Mendeleev mostly exposes Pauling, but we try generic access for others
        # if specific attributes exist in future versions
        value = getattr(elem, "electronegativity", None)
    
    if value is None:
        raise AttributeError(f"Electronegativity not available for {symbol} on {scale} scale")
    
    return float(value)

def get_all_properties(symbol: str) -> dict:
    """
    Retrieve a dictionary of common properties for an element.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu').
        
    Returns:
        Dictionary containing atomic_mass, atomic_radius, and electronegativity.
    """
    return {
        "atomic_mass": get_atomic_mass(symbol),
        "atomic_radius": get_atomic_radius(symbol),
        "electronegativity": get_electronegativity(symbol),
    }