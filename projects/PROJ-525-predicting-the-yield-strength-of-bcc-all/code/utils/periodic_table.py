"""
Static NIST elemental property lookup for BCC alloy analysis.
Provides atomic radius, valence electron count, and electronegativity
without external API calls.
"""
from typing import Dict, Optional, Tuple
import math

# NIST-based static lookup tables (approximate values for common BCC alloying elements)
# Units: radius (pm), valence (electrons), electronegativity (Pauling)
_ELEMENT_DATA: Dict[str, Tuple[float, int, float]] = {
    # Transition Metals (Common BCC formers)
    "V": (134, 5, 1.63),   # Vanadium
    "Cr": (128, 6, 1.66),  # Chromium
    "Mo": (139, 6, 2.16),  # Molybdenum
    "Nb": (146, 5, 1.60),  # Niobium
    "Ta": (146, 5, 1.50),  # Tantalum
    "W": (139, 6, 2.36),   # Tungsten
    "Fe": (126, 8, 1.83),  # Iron (BCC alpha phase)
    "Zr": (160, 4, 1.33),  # Zirconium (BCC beta phase)
    "Ti": (147, 4, 1.54),  # Titanium (BCC beta phase)
    
    # Common Alloying Elements
    "Al": (143, 3, 1.61),  # Aluminum
    "Si": (118, 4, 1.90),  # Silicon
    "Co": (125, 9, 1.88),  # Cobalt
    "Ni": (124, 10, 1.91), # Nickel
    "Cu": (128, 11, 1.90), # Copper
    "Mn": (127, 7, 1.55),  # Manganese
    
    # Light Elements
    "Mg": (160, 2, 1.31),  # Magnesium
    "Ca": (197, 2, 1.00),  # Calcium
    
    # Others
    "C": (77, 4, 2.55),    # Carbon
    "N": (75, 5, 3.04),    # Nitrogen
    "O": (73, 6, 3.44),    # Oxygen
    "H": (53, 1, 2.20),    # Hydrogen
    
    # Rare Earths (Common in HEAs)
    "Y": (180, 3, 1.22),   # Yttrium
    "La": (187, 3, 1.10),  # Lanthanum
    "Ce": (182, 4, 1.12),  # Cerium
}

def get_element_properties(symbol: str) -> Optional[Tuple[float, int, float]]:
    """
    Retrieve atomic radius (pm), valence electrons, and electronegativity for an element.
    
    Args:
        symbol: Chemical symbol (e.g., "Fe", "Cr"). Case-insensitive.
        
    Returns:
        Tuple of (radius_pm, valence, electronegativity) if found, else None.
    """
    symbol = symbol.strip().upper()
    if symbol in _ELEMENT_DATA:
        return _ELEMENT_DATA[symbol]
    return None

def get_atomic_radius(symbol: str) -> Optional[float]:
    """Get atomic radius in picometers."""
    props = get_element_properties(symbol)
    return props[0] if props else None

def get_valence(symbol: str) -> Optional[int]:
    """Get valence electron count."""
    props = get_element_properties(symbol)
    return props[1] if props else None

def get_electronegativity(symbol: str) -> Optional[float]:
    """Get Pauling electronegativity."""
    props = get_element_properties(symbol)
    return props[2] if props else None

def calculate_weighted_average(
    elements: list[str],
    fractions: list[float],
    getter_func
) -> Optional[float]:
    """
    Calculate a weighted average property for an alloy composition.
    
    Args:
        elements: List of element symbols.
        fractions: List of atomic fractions (must sum to ~1.0).
        getter_func: Function to retrieve the property for a single element.
        
    Returns:
        Weighted average property value, or None if any element is missing.
    """
    if len(elements) != len(fractions):
        raise ValueError("Elements and fractions lists must be the same length.")
    
    total = 0.0
    for sym, frac in zip(elements, fractions):
        val = getter_func(sym)
        if val is None:
            return None
        total += val * frac
    
    return total

def calculate_atomic_radius_mismatch(
    elements: list[str],
    fractions: list[float]
) -> Optional[float]:
    """
    Calculate the atomic radius mismatch parameter (δ) for an alloy.
    δ = sqrt( Σ ci * (1 - ri/r_avg)^2 ) * 100
    
    Args:
        elements: List of element symbols.
        fractions: List of atomic fractions.
        
    Returns:
        Mismatch percentage, or None if data is missing.
    """
    radii = []
    for sym in elements:
        r = get_atomic_radius(sym)
        if r is None:
            return None
        radii.append(r)
    
    # Calculate average radius
    r_avg = sum(f * r for f, r in zip(fractions, radii))
    if r_avg == 0:
        return 0.0
    
    # Calculate mismatch
    sum_sq = sum(f * (1 - r / r_avg) ** 2 for f, r in zip(fractions, radii))
    return math.sqrt(sum_sq) * 100

def calculate_valence_electron_concentration(
    elements: list[str],
    fractions: list[float]
) -> Optional[float]:
    """
    Calculate the average Valence Electron Concentration (VEC).
    VEC = Σ ci * VECi
    
    Args:
        elements: List of element symbols.
        fractions: List of atomic fractions.
        
    Returns:
        Average VEC, or None if data is missing.
    """
    return calculate_weighted_average(elements, fractions, get_valence)

def calculate_electronegativity_average(
    elements: list[str],
    fractions: list[float]
) -> Optional[float]:
    """
    Calculate the average electronegativity.
    χ_avg = Σ ci * χi
    
    Args:
        elements: List of element symbols.
        fractions: List of atomic fractions.
        
    Returns:
        Average electronegativity, or None if data is missing.
    """
    return calculate_weighted_average(elements, fractions, get_electronegativity)