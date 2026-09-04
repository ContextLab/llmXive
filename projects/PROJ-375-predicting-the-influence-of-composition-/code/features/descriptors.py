import re
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
import math
import logging
from mendeleev import element

logger = logging.getLogger(__name__)

def parse_formula(formula: str) -> Dict[str, float]:
    """
    Parses a chemical formula string into a dictionary of element: fraction.
    Example: "Zr50Cu40Al10" -> {'Zr': 0.5, 'Cu': 0.4, 'Al': 0.1}
    """
    if not formula:
        raise ValueError("Formula cannot be empty")

    # Regex to match element symbol and optional number
    pattern = r"([A-Z][a-z]?)(\d*\.?\d*)"
    matches = re.findall(pattern, formula)

    if not matches:
        raise ValueError(f"Invalid formula format: {formula}")

    composition = {}
    total_weight = 0.0

    for elem, count_str in matches:
        count = float(count_str) if count_str else 1.0
        composition[elem] = count
        total_weight += count

    # Normalize to fractions
    if total_weight == 0:
        raise ValueError("Total weight in formula is zero")

    return {elem: count / total_weight for elem, count in composition.items()}

def calculate_weighted_mean_radius(composition: Dict[str, float], radii: Dict[str, float]) -> float:
    """
    Calculates the weighted mean atomic radius.
    Formula: Σ (atomic_fraction_i * atomic_radius_i)
    """
    weighted_sum = 0.0
    for elem, frac in composition.items():
        if elem not in radii:
            logger.warning(f"Atomic radius not found for {elem}. Skipping.")
            continue
        weighted_sum += frac * radii[elem]
    return weighted_sum

def calculate_weighted_mean_electronegativity(composition: Dict[str, float], electronegativities: Dict[str, float]) -> float:
    """
    Calculates the weighted mean electronegativity.
    """
    weighted_sum = 0.0
    for elem, frac in composition.items():
        if elem not in electronegativities:
            logger.warning(f"Electronegativity not found for {elem}. Skipping.")
            continue
        weighted_sum += frac * electronegativities[elem]
    return weighted_sum

def calculate_variance_electronegativity(composition: Dict[str, float], electronegativities: Dict[str, float]) -> float:
    """
    Calculates the variance of electronegativity.
    Formula: Σ (atomic_fraction_i * (electronegativity_i - mean_electronegativity)^2)
    """
    mean_en = calculate_weighted_mean_electronegativity(composition, electronegativities)
    variance = 0.0
    for elem, frac in composition.items():
        if elem not in electronegativities:
            continue
        diff = electronegativities[elem] - mean_en
        variance += frac * (diff ** 2)
    return variance

def calculate_weighted_mean_VEC(composition: Dict[str, float], vecs: Dict[str, float]) -> float:
    """
    Calculates the weighted mean Valence Electron Concentration (VEC).
    """
    weighted_sum = 0.0
    for elem, frac in composition.items():
        if elem not in vecs:
            logger.warning(f"VEC not found for {elem}. Skipping.")
            continue
        weighted_sum += frac * vecs[elem]
    return weighted_sum

def calculate_atomic_size_mismatch(composition: Dict[str, float], radii: Dict[str, float]) -> float:
    """
    Calculates the atomic size mismatch parameter.
    Formula: 1 - Σ (atomic_fraction_i * (1 - |atomic_radius_i - mean_radius| / mean_radius))
    """
    mean_radius = calculate_weighted_mean_radius(composition, radii)
    if mean_radius == 0:
        return 0.0

    mismatch_sum = 0.0
    for elem, frac in composition.items():
        if elem not in radii:
            continue
        diff = abs(radii[elem] - mean_radius)
        term = 1 - (diff / mean_radius)
        mismatch_sum += frac * term

    return 1 - mismatch_sum

def extract_descriptors(composition_str: str) -> Dict[str, float]:
    """
    Extracts all required descriptors from a composition string.
    """
    composition = parse_formula(composition_str)

    # Fetch properties from mendeleev
    radii = {}
    electronegativities = {}
    vecs = {}

    for elem in composition.keys():
        try:
            el = element(elem)
            radii[elem] = el.atomic_radius
            electronegativities[elem] = el.electronegativity
            vecs[elem] = el.valence_electrons
        except Exception as e:
            logger.warning(f"Could not fetch properties for {elem}: {e}")

    return {
        "mean_atomic_radius": calculate_weighted_mean_radius(composition, radii),
        "electronegativity_var": calculate_variance_electronegativity(composition, electronegativities),
        "vec": calculate_weighted_mean_VEC(composition, vecs),
        "size_mismatch": calculate_atomic_size_mismatch(composition, radii)
    }

def check_vif_conflict(vif_value: float, threshold: float = 5.0) -> bool:
    """
    Checks if VIF exceeds the threshold and logs a warning.
    Returns True if high VIF is detected.
    """
    if vif_value > threshold:
        logger.warning(f"High VIF detected for size_mismatch (VIF={vif_value}). "
                       "Retaining feature per FR-002 and Constitution Principle VI.")
        return True
    return False