"""
Utility functions for periodic table property retrieval.
"""
from pymatgen.core import Element
from typing import Optional

def get_atomic_radius(symbol: str) -> float:
    """Retrieve the atomic radius (pm) for a given element symbol.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'C').
        
    Returns:
        Atomic radius in picometers (pm). Returns float('nan') if unavailable.
    """
    try:
        el = Element(symbol)
        radius = el.atomic_radius
        return float(radius) if radius is not None else float('nan')
    except Exception:
        return float('nan')

def get_vec(symbol: str) -> float:
    """Retrieve the valence electron count (VEC) for a given element symbol.
    
    The VEC is determined by the number of valence electrons in the neutral atom.
    For transition metals, this is typically the sum of s and d electrons in the 
    outermost shells.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'C').
        
    Returns:
        Valence electron count. Returns float('nan') if unavailable.
    """
    try:
        el = Element(symbol)
        # Use the number of valence electrons from the electronic structure
        # pymatgen's Element class provides 'valence' which is the number of 
        # valence electrons based on the element's group
        if hasattr(el, 'valence') and el.valence is not None:
            return float(el.valence)
        
        # Fallback: use periodic table group number for main group elements
        # or calculate based on electron configuration for transition metals
        # pymatgen's Element class has 'group_number' which can be used
        group = el.group_number
        if group is not None:
            # For main group elements (groups 1, 2, 13-18)
            if group <= 2:
                return float(group)
            elif group <= 12:
                # Transition metals: group number - 10 for d-electrons + 2 for s-electrons
                # But this is a simplification; use the valence property if available
                return float(group - 10) if group > 10 else float(group)
            else:
                return float(group - 10)
        
        return float('nan')
    except Exception:
        return float('nan')

def get_electronegativity(symbol: str) -> float:
    """Retrieve the electronegativity (Pauling scale) for a given element symbol.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'C').
        
    Returns:
        Electronegativity on the Pauling scale. Returns float('nan') if unavailable.
    """
    try:
        el = Element(symbol)
        en = el.electronegativity
        return float(en) if en is not None else float('nan')
    except Exception:
        return float('nan')

def get_properties(symbol: str) -> dict:
    """Retrieve all periodic table properties for a given element.
    
    Args:
        symbol: Element symbol (e.g., 'Fe', 'C').
        
    Returns:
        Dictionary containing atomic_radius, vec, and electronegativity.
    """
    return {
        'atomic_radius': get_atomic_radius(symbol),
        'vec': get_vec(symbol),
        'electronegativity': get_electronegativity(symbol)
    }

def get_properties_batch(symbols: list) -> list:
    """Retrieve periodic table properties for a list of element symbols.
    
    Args:
        symbols: List of element symbols (e.g., ['Fe', 'C', 'Cr']).
        
    Returns:
        List of dictionaries, each containing atomic_radius, vec, and electronegativity.
    """
    return [get_properties(symbol) for symbol in symbols]