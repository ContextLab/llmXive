"""
Feature engineering module for Metallic Glass composition descriptors.

Calculates:
- Weighted mean atomic radius
- Electronegativity variance
- Valence Electron Concentration (VEC)
- Atomic size mismatch (delta)
"""
import re
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
import math
import logging
from mendeleev import element

logger = logging.getLogger(__name__)

# Constants for property retrieval
PROPERTIES = {
    'radius': 'atomic_radius',
    'electronegativity': 'electronegativity',
    'valence': 'valence_electrons'
}

def parse_formula(formula: str) -> Dict[str, float]:
    """
    Parse a chemical formula string (e.g., 'Zr50Cu40Al10') into a dictionary
    of element symbols and their atomic fractions.

    Args:
        formula: String in format ElementNumber... (e.g., Zr50Cu40Al10)

    Returns:
        Dict mapping element symbol to atomic fraction (normalized to 1.0).
    """
    if not formula:
        raise ValueError("Formula string cannot be empty")

    # Regex to match element symbol followed by optional number
    # Element symbols: Capital letter followed by optional lowercase
    pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
    matches = pattern.findall(formula)

    if not matches:
        raise ValueError(f"Could not parse formula: {formula}")

    composition = {}
    total_atoms = 0.0

    for symbol, count_str in matches:
        count = int(count_str) if count_str else 1.0
        composition[symbol] = float(count)
        total_atoms += count

    if total_atoms == 0:
        raise ValueError(f"Total atom count is zero for formula: {formula}")

    # Normalize to fractions
    return {k: v / total_atoms for k, v in composition.items()}


def _get_property_from_mendeleev(symbol: str, prop_key: str) -> float:
    """
    Safely retrieve a property from mendeleev element database.

    Args:
        symbol: Element symbol (e.g., 'Zr')
        prop_key: Key in PROPERTIES mapping to mendeleev attribute

    Returns:
        Property value as float.

    Raises:
        ValueError: If element not found or property missing.
    """
    try:
        elem = element(symbol)
    except Exception as e:
        raise ValueError(f"Element {symbol} not found in mendeleev database: {e}")

    attr_name = PROPERTIES.get(prop_key)
    if not attr_name:
        raise ValueError(f"Unknown property key: {prop_key}")

    value = getattr(elem, attr_name, None)
    if value is None:
        raise ValueError(f"Property '{attr_name}' is missing for element {symbol}")

    # Handle potential non-numeric or missing values in mendeleev
    if isinstance(value, (int, float)):
        return float(value)
    
    # Some properties might be lists or other types in newer mendeleev versions
    # We take the first value or average if it's a list of covalent radii etc.
    if isinstance(value, list):
        if len(value) > 0:
            return float(value[0])
        raise ValueError(f"Property '{attr_name}' is an empty list for {symbol}")
    
    raise ValueError(f"Unexpected type for property '{attr_name}' of {symbol}: {type(value)}")


def calculate_weighted_mean_radius(composition: Dict[str, float]) -> float:
    """
    Calculate the weighted mean atomic radius (R_bar).

    R_bar = sum(c_i * R_i)

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Weighted mean atomic radius in pm (or consistent units).
    """
    if not composition:
        raise ValueError("Composition dictionary cannot be empty")

    total = 0.0
    for symbol, fraction in composition.items():
        radius = _get_property_from_mendeleev(symbol, 'radius')
        total += fraction * radius

    return total


def calculate_weighted_mean_electronegativity(composition: Dict[str, float]) -> float:
    """
    Calculate the weighted mean electronegativity (chi_bar).

    chi_bar = sum(c_i * chi_i)

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Weighted mean electronegativity (Pauling scale).
    """
    if not composition:
        raise ValueError("Composition dictionary cannot be empty")

    total = 0.0
    for symbol, fraction in composition.items():
        chi = _get_property_from_mendeleev(symbol, 'electronegativity')
        total += fraction * chi

    return total


def calculate_variance_electronegativity(composition: Dict[str, float]) -> float:
    """
    Calculate the variance of electronegativity (Delta chi).

    Delta chi = sum(c_i * (chi_i - chi_bar)^2)

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Variance of electronegativity.
    """
    if not composition:
        raise ValueError("Composition dictionary cannot be empty")

    chi_bar = calculate_weighted_mean_electronegativity(composition)
    variance = 0.0

    for symbol, fraction in composition.items():
        chi = _get_property_from_mendeleev(symbol, 'electronegativity')
        variance += fraction * ((chi - chi_bar) ** 2)

    return variance


def calculate_weighted_mean_VEC(composition: Dict[str, float]) -> float:
    """
    Calculate the weighted mean Valence Electron Concentration (VEC).

    VEC_bar = sum(c_i * VEC_i)

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Weighted mean VEC.
    """
    if not composition:
        raise ValueError("Composition dictionary cannot be empty")

    total = 0.0
    for symbol, fraction in composition.items():
        vec = _get_property_from_mendeleev(symbol, 'valence')
        total += fraction * vec

    return total


def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate the atomic size mismatch parameter (delta).

    delta = sqrt( sum(c_i * (1 - R_i / R_bar)^2) )

    where R_bar is the weighted mean atomic radius.

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Atomic size mismatch parameter (dimensionless).
    """
    if not composition:
        raise ValueError("Composition dictionary cannot be empty")

    r_bar = calculate_weighted_mean_radius(composition)
    if r_bar == 0:
        raise ValueError("Calculated mean radius is zero, cannot compute mismatch.")

    sum_val = 0.0
    for symbol, fraction in composition.items():
        r_i = _get_property_from_mendeleev(symbol, 'radius')
        sum_val += fraction * ((1.0 - (r_i / r_bar)) ** 2)

    return math.sqrt(sum_val)


def extract_descriptors(formula: str) -> Dict[str, float]:
    """
    Main entry point to extract all required descriptors from a formula string.

    Args:
        formula: Chemical formula string (e.g., 'Zr50Cu40Al10')

    Returns:
        Dictionary containing:
            - 'mean_atomic_radius': float
            - 'mean_electronegativity': float
            - 'electronegativity_variance': float
            - 'vec': float
            - 'size_mismatch': float
    """
    try:
        composition = parse_formula(formula)
    except ValueError as e:
        logger.error(f"Failed to parse formula '{formula}': {e}")
        raise

    try:
        return {
            'mean_atomic_radius': calculate_weighted_mean_radius(composition),
            'mean_electronegativity': calculate_weighted_mean_electronegativity(composition),
            'electronegativity_variance': calculate_variance_electronegativity(composition),
            'vec': calculate_weighted_mean_VEC(composition),
            'size_mismatch': calculate_atomic_size_mismatch(composition)
        }
    except ValueError as e:
        logger.error(f"Failed to calculate descriptors for '{formula}': {e}")
        raise


def check_vif_conflict(descriptors: List[Dict[str, float]], threshold: float = 5.0) -> bool:
    """
    Check for multicollinearity (VIF) between mean_atomic_radius and size_mismatch.
    
    Note: This is a simplified check. A full VIF calculation requires a regression model.
    Here we check the correlation magnitude as a proxy for VIF > threshold.
    If high correlation is detected, we log a warning but DO NOT exclude the feature
    per Constitution Principle VI.

    Args:
        descriptors: List of descriptor dictionaries.
        threshold: VIF threshold (default 5.0).

    Returns:
        True if high multicollinearity is detected (VIF > threshold), False otherwise.
    """
    if len(descriptors) < 2:
        return False

    radii = [d.get('mean_atomic_radius') for d in descriptors if d.get('mean_atomic_radius') is not None]
    mismatches = [d.get('size_mismatch') for d in descriptors if d.get('size_mismatch') is not None]

    if len(radii) != len(mismatches) or len(radii) < 2:
        return False

    # Calculate Pearson correlation coefficient
    n = len(radii)
    mean_r = sum(radii) / n
    mean_m = sum(mismatches) / n

    numerator = sum((radii[i] - mean_r) * (mismatches[i] - mean_m) for i in range(n))
    denom_r = math.sqrt(sum((x - mean_r) ** 2 for x in radii))
    denom_m = math.sqrt(sum((x - mean_m) ** 2 for x in mismatches))

    if denom_r == 0 or denom_m == 0:
        return False

    r_val = numerator / (denom_r * denom_m)

    # VIF approx 1 / (1 - R^2). If R^2 is high, VIF is high.
    # If r_val^2 > 0.8, VIF > 5.0 (approx)
    r_squared = r_val ** 2
    vif_approx = 1.0 / (1.0 - r_squared) if (1.0 - r_squared) > 1e-9 else float('inf')

    if vif_approx > threshold:
        logger.warning(f"High VIF detected for size_mismatch (approx VIF: {vif_approx:.2f}). "
                     "Retaining feature per Constitution Principle VI.")
        return True

    return False
