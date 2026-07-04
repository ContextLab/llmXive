"""
Periodic property helpers for chalcogenide glass composition analysis.

This module provides functions to retrieve element properties using the
mendeleev library and compute compositional descriptors such as mean
coordination number, electronegativity variance, and atomic radius variance.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import re

try:
    from mendeleev import element
except ImportError:
    element = None
    logging.warning("mendeleev library not installed. Periodic property helpers will not work.")

# Standard coordination numbers for common elements in chalcogenide glasses
# Based on 8-N rule and common oxidation states
DEFAULT_COORDINATION_NUMBERS: Dict[str, int] = {
    # Chalcogens (Group 16)
    'O': 2, 'S': 2, 'Se': 2, 'Te': 2,
    # Group 15 (Pnictogens)
    'N': 3, 'P': 3, 'As': 3, 'Sb': 3, 'Bi': 3,
    # Group 14 (Tetrels)
    'C': 4, 'Si': 4, 'Ge': 4, 'Sn': 4, 'Pb': 4,
    # Group 13 (Triels)
    'B': 3, 'Al': 3, 'Ga': 3, 'In': 3, 'Tl': 3,
    # Group 17 (Halogens)
    'F': 1, 'Cl': 1, 'Br': 1, 'I': 1,
    # Common modifiers
    'Li': 1, 'Na': 1, 'K': 1, 'Rb': 1, 'Cs': 1,
    'Mg': 2, 'Ca': 2, 'Sr': 2, 'Ba': 2,
    'Zn': 2, 'Cd': 2, 'Hg': 2,
}


def get_element(symbol: str):
    """
    Retrieve an Element object from mendeleev.

    Args:
        symbol: Chemical symbol (e.g., 'Ge', 'Se')

    Returns:
        mendeleev.element.Element object or None if not found
    """
    if element is None:
        logging.error("mendeleev library is not installed.")
        return None

    try:
        return element(symbol)
    except Exception as e:
        logging.warning(f"Could not find element '{symbol}': {e}")
        return None


def get_coordination_number(symbol: str, default: Optional[int] = None) -> int:
    """
    Get the coordination number for an element.

    Uses the 8-N rule for main group elements if available, otherwise
    falls back to a predefined dictionary or a default value.

    Args:
        symbol: Chemical symbol
        default: Default coordination number if not found (default: 2)

    Returns:
        Coordination number as integer
    """
    # Check predefined dictionary first
    if symbol in DEFAULT_COORDINATION_NUMBERS:
        return DEFAULT_COORDINATION_NUMBERS[symbol]

    # Try to get from mendeleev group/period logic (8-N rule approximation)
    elem = get_element(symbol)
    if elem and hasattr(elem, 'group') and hasattr(elem, 'period'):
        group = elem.group
        # Main group elements (groups 1, 2, 13-18)
        if group in [1, 2] or (13 <= group <= 18):
            if group >= 14:
                # For groups 14-18, use 8-N rule (N = group - 10 for 13-18)
                n_valence = group - 10
                return 8 - n_valence
            elif group == 13:
                return 3
            elif group == 2:
                return 2
            elif group == 1:
                return 1

    # Fallback
    return default if default is not None else 2


def get_electronegativity(symbol: str) -> Optional[float]:
    """
    Get the Pauling electronegativity for an element.

    Args:
        symbol: Chemical symbol

    Returns:
        Electronegativity value or None if not available
    """
    elem = get_element(symbol)
    if elem and hasattr(elem, 'electronegativity'):
        val = elem.electronegativity
        return float(val) if val is not None else None
    return None


def get_atomic_radius(symbol: str) -> Optional[float]:
    """
    Get the covalent radius for an element in Angstroms.

    Args:
        symbol: Chemical symbol

    Returns:
        Atomic radius in Angstroms or None if not available
    """
    elem = get_element(symbol)
    if elem and hasattr(elem, 'covalent_radius'):
        val = elem.covalent_radius
        # Return in Angstroms (mendeleev returns in pm usually, but covalent_radius is often in pm)
        # Check if the value is in pm (> 50) and convert
        if val is not None and val > 50:
            return val / 100.0  # Convert pm to Angstroms
        return float(val) if val is not None else None
    return None


def get_element_property(symbol: str, property_name: str) -> Optional[Union[int, float]]:
    """
    Generic getter for element properties.

    Args:
        symbol: Chemical symbol
        property_name: Name of the property (e.g., 'electronegativity', 'atomic_radius', 'coordination_number')

    Returns:
        Property value or None
    """
    property_name = property_name.lower()

    if property_name == 'coordination_number':
        return get_coordination_number(symbol)
    elif property_name == 'electronegativity':
        return get_electronegativity(symbol)
    elif property_name == 'atomic_radius':
        return get_atomic_radius(symbol)
    else:
        elem = get_element(symbol)
        if elem and hasattr(elem, property_name):
            val = getattr(elem, property_name)
            return float(val) if val is not None else None
        return None


def parse_composition(composition_str: str) -> List[Tuple[str, float]]:
    """
    Parse a composition string into a list of (element, fraction) tuples.

    Supports formats like:
    - "Ge20Se80"
    - "As30Se70"
    - "Ge0.2Se0.8"
    - "As 30 Se 70" (with spaces)

    Args:
        composition_str: Composition string

    Returns:
        List of (symbol, fraction) tuples
    """
    if not composition_str or not isinstance(composition_str, str):
        return []

    # Normalize: remove spaces, handle common separators
    s = composition_str.replace(" ", "").replace(",", "")

    # Pattern to match element symbol followed by optional number
    # Element symbols are 1-2 letters, first uppercase, second lowercase
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'

    matches = re.findall(pattern, s)

    result = []
    for symbol, num_str in matches:
        try:
            if num_str:
                fraction = float(num_str)
            else:
                fraction = 1.0
            result.append((symbol, fraction))
        except ValueError:
            continue

    # Normalize fractions to sum to 1 if they are integers (e.g., Ge20Se80 -> 0.2, 0.8)
    total = sum(f for _, f in result)
    if total > 1.0:
        result = [(sym, f / total) for sym, f in result]

    return result


def compute_mean_coordination_number(composition_str: str) -> Optional[float]:
    """
    Compute the mean coordination number for a given composition.

    <r> = sum(x_i * r_i) where x_i is the atomic fraction and r_i is the coordination number.

    Args:
        composition_str: Composition string (e.g., "Ge20Se80")

    Returns:
        Mean coordination number or None if calculation fails
    """
    parsed = parse_composition(composition_str)
    if not parsed:
        return None

    total_cn = 0.0
    total_frac = 0.0

    for symbol, fraction in parsed:
        cn = get_coordination_number(symbol)
        if cn is not None:
            total_cn += fraction * cn
            total_frac += fraction

    if total_frac == 0:
        return None

    return total_cn / total_frac


def compute_electronegativity_variance(composition_str: str) -> Optional[float]:
    """
    Compute the variance of electronegativity for a given composition.

    Var(EN) = sum(x_i * (EN_i - <EN>)^2)

    Args:
        composition_str: Composition string

    Returns:
        Electronegativity variance or None if calculation fails
    """
    parsed = parse_composition(composition_str)
    if not parsed:
        return None

    # Calculate mean electronegativity
    en_values = []
    fractions = []
    for symbol, fraction in parsed:
        en = get_electronegativity(symbol)
        if en is not None:
            en_values.append(en)
            fractions.append(fraction)

    if not en_values:
        return None

    # Normalize fractions
    total_frac = sum(fractions)
    fractions = [f / total_frac for f in fractions]

    mean_en = sum(e * f for e, f in zip(en_values, fractions))

    # Calculate variance
    variance = sum(f * (e - mean_en) ** 2 for e, f in zip(en_values, fractions))

    return variance


def compute_atomic_radius_variance(composition_str: str) -> Optional[float]:
    """
    Compute the variance of atomic radius for a given composition.

    Var(R) = sum(x_i * (R_i - <R>)^2)

    Args:
        composition_str: Composition string

    Returns:
        Atomic radius variance or None if calculation fails
    """
    parsed = parse_composition(composition_str)
    if not parsed:
        return None

    # Calculate mean atomic radius
    radius_values = []
    fractions = []
    for symbol, fraction in parsed:
        r = get_atomic_radius(symbol)
        if r is not None:
            radius_values.append(r)
            fractions.append(fraction)

    if not radius_values:
        return None

    # Normalize fractions
    total_frac = sum(fractions)
    fractions = [f / total_frac for f in fractions]

    mean_radius = sum(r * f for r, f in zip(radius_values, fractions))

    # Calculate variance
    variance = sum(f * (r - mean_radius) ** 2 for r, f in zip(radius_values, fractions))

    return variance