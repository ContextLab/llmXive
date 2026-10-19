"""
Feature‑extraction utilities for metallic‑glass compositions.

The public API of this module matches the original contract but adds
two new helpers required by task T002:

* ``calculate_atomic_size_coefficient_of_variation`` – the σ/μ descriptor
  defined in the specification.
* ``extract_descriptors`` – now returns field names that exactly match the
  dataset schema (``weighted_mean_atomic_radius``, ``electronegativity_variance``,
  ``vec``, ``atomic_size_coefficient_of_variation``).
"""

import logging
import math
from collections import Counter
from typing import Dict, List, Tuple, Any, Optional

from mendeleev import element

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Formula parsing
# -------------------------------------------------------------------------

def parse_formula(formula: str) -> Dict[str, float]:
    """
    Parses a chemical formula string into a dictionary of element → fraction.
    Example: "Zr50Cu40Al10" -> {'Zr': 0.5, 'Cu': 0.4, 'Al': 0.1}
    """
    if not formula:
        raise ValueError("Formula cannot be empty")

    import re

    pattern = r"([A-Z][a-z]?)(\d*\.?\d*)"
    matches = re.findall(pattern, formula)

    if not matches:
        raise ValueError(f"Invalid formula format: {formula}")

    composition: Dict[str, float] = {}
    total = 0.0
    for elem, count_str in matches:
        count = float(count_str) if count_str else 1.0
        composition[elem] = count
        total += count

    if total == 0:
        raise ValueError("Total weight in formula is zero")

    return {elem: cnt / total for elem, cnt in composition.items()}

# -------------------------------------------------------------------------
# Atomic property look‑ups
# -------------------------------------------------------------------------

def _load_element_properties(symbols: List[str]) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """
    Retrieve atomic radius (pm), Pauling electronegativity and valence‑electron count
    for each element symbol in *symbols* using the ``mendeleev`` package.
    Missing properties are logged and omitted from the returned dicts.
    """
    radii: Dict[str, float] = {}
    electronegativities: Dict[str, float] = {}
    vecs: Dict[str, float] = {}

    for sym in symbols:
        try:
            el = element(sym)
            # ``atomic_radius`` may be ``None`` for some entries – guard against it.
            if el.atomic_radius is not None:
                radii[sym] = float(el.atomic_radius)
            else:
                logger.warning(f"Atomic radius missing for element {sym}")

            if el.electronegativity is not None:
                electronegativities[sym] = float(el.electronegativity)
            else:
                logger.warning(f"Electronegativity missing for element {sym}")

            if el.valence_electrons is not None:
                vecs[sym] = float(el.valence_electrons)
            else:
                logger.warning(f"Valence electron count missing for element {sym}")

        except Exception as exc:
            logger.warning(f"Failed to retrieve data for element {sym}: {exc}")

    return radii, electronegativities, vecs

# -------------------------------------------------------------------------
# Descriptor calculations
# -------------------------------------------------------------------------

def calculate_weighted_mean_radius(composition: Dict[str, float], radii: Dict[str, float]) -> float:
    """Weighted mean atomic radius (pm)."""
    return sum(frac * radii[elem] for elem, frac in composition.items() if elem in radii)

def calculate_weighted_mean_electronegativity(composition: Dict[str, float], electronegativities: Dict[str, float]) -> float:
    """Weighted mean electronegativity."""
    return sum(frac * electronegativities[elem] for elem, frac in composition.items() if elem in electronegativities)

def calculate_variance_electronegativity(composition: Dict[str, float], electronegativities: Dict[str, float]) -> float:
    """Weighted variance of electronegativity."""
    mean_en = calculate_weighted_mean_electronegativity(composition, electronegativities)
    return sum(
        frac * ((electronegativities[elem] - mean_en) ** 2)
        for elem, frac in composition.items()
        if elem in electronegativities
    )

def calculate_weighted_mean_VEC(composition: Dict[str, float], vecs: Dict[str, float]) -> float:
    """Weighted mean valence electron concentration (VEC)."""
    return sum(frac * vecs[elem] for elem, frac in composition.items() if elem in vecs)

def calculate_atomic_size_coefficient_of_variation(composition: Dict[str, float], radii: Dict[str, float]) -> float:
    """
    Atomic size coefficient of variation (σ/μ).
    μ = weighted mean radius, σ = weighted standard deviation.
    """
    mean_radius = calculate_weighted_mean_radius(composition, radii)
    if mean_radius == 0:
        return 0.0
    # Weighted variance of radii
    variance = sum(
        frac * ((radii[elem] - mean_radius) ** 2)
        for elem, frac in composition.items()
        if elem in radii
    )
    std_dev = math.sqrt(variance)
    return std_dev / mean_radius

# -------------------------------------------------------------------------
# Public descriptor extractor (matches schema field names)
# -------------------------------------------------------------------------

def extract_descriptors(composition_str: str) -> Dict[str, float]:
    """
    Extract the four required descriptors from *composition_str* and return a
    dictionary whose keys exactly match the dataset schema:

    * ``weighted_mean_atomic_radius``
    * ``electronegativity_variance``
    * ``vec``
    * ``atomic_size_coefficient_of_variation``
    """
    composition = parse_formula(composition_str)
    symbols = list(composition.keys())
    radii, electronegativities, vecs = _load_element_properties(symbols)

    # Guard against missing property dictionaries – they will result in NaNs.
    mean_radius = calculate_weighted_mean_radius(composition, radii)
    en_variance = calculate_variance_electronegativity(composition, electronegativities)
    vec = calculate_weighted_mean_VEC(composition, vecs)
    size_cov = calculate_atomic_size_coefficient_of_variation(composition, radii)

    return {
        "weighted_mean_atomic_radius": mean_radius,
        "electronegativity_variance": en_variance,
        "vec": vec,
        "atomic_size_coefficient_of_variation": size_cov,
    }

# -------------------------------------------------------------------------
# VIF helper (unchanged contract)
# -------------------------------------------------------------------------

def check_vif_conflict(vif_value: float, threshold: float = 5.0) -> bool:
    """
    Checks if VIF exceeds the threshold and logs a warning.
    Returns True if high VIF is detected.
    """
    if vif_value > threshold:
        logger.warning(
            f"High VIF detected for size_mismatch (VIF={vif_value}). "
            "Retaining feature per FR-002 and Constitution Principle VI."
        )
        return True
    return False
