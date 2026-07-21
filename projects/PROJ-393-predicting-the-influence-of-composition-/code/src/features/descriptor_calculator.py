"""
Descriptor Calculator for Heusler Alloy Features.

Computes compositional descriptors:
- Average Electronegativity
- Valence Electron Concentration (VEC)
- Atomic Radii Variance
- Average d-electrons
- Atomic Size Mismatch
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from src.utils.periodic_table_loader import load_elemental_properties, get_element_property

# Configure logger
logger = logging.getLogger(__name__)


def parse_composition_string(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Co2MnGa' or 'Co2MnGa0.9' into atomic fractions.

    Supports:
    - Formula format: Element followed by optional integer/float count.
    - Assumes the sum of counts equals the total atoms (normalized to fractions).

    Args:
        composition_str: String representation of composition.

    Returns:
        Dictionary mapping element symbol to atomic fraction.
    """
    import re

    # Regex to match Element (2 chars or 1 char) followed by optional number
    # Elements: Capital letter followed by optional lowercase letter
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)

    elements_counts = {}
    total_count = 0.0

    for elem, count_str in matches:
        count = float(count_str) if count_str else 1.0
        elements_counts[elem] = count
        total_count += count

    if total_count == 0:
        raise ValueError(f"Total count is zero for composition: {composition_str}")

    # Normalize to fractions
    fractions = {elem: count / total_count for elem, count in elements_counts.items()}
    return fractions


def calculate_average_electronegativity(composition: Dict[str, float]) -> float:
    """Calculate weighted average electronegativity."""
    total_en = 0.0
    for elem, frac in composition.items():
        en = get_element_property(elem, "electronegativity")
        if en is None:
            logger.warning(f"Electronegativity not found for {elem}, skipping.")
            continue
        total_en += frac * en
    return total_en


def calculate_valence_electron_concentration(composition: Dict[str, float]) -> float:
    """Calculate weighted average valence electrons (VEC)."""
    total_vec = 0.0
    for elem, frac in composition.items():
        vec = get_element_property(elem, "valence_electrons")
        if vec is None:
            logger.warning(f"Valence electrons not found for {elem}, skipping.")
            continue
        total_vec += frac * vec
    return total_vec


def calculate_atomic_radii_variance(composition: Dict[str, float]) -> float:
    """Calculate variance of atomic radii weighted by composition."""
    radii = []
    weights = []
    for elem, frac in composition.items():
        r = get_element_property(elem, "atomic_radii")
        if r is None:
            logger.warning(f"Atomic radii not found for {elem}, skipping.")
            continue
        radii.append(r)
        weights.append(frac)

    if not radii:
        return 0.0

    # Weighted variance
    weights_arr = np.array(weights)
    radii_arr = np.array(radii)
    mean_r = np.average(radii_arr, weights=weights_arr)
    variance = np.average((radii_arr - mean_r) ** 2, weights=weights_arr)
    return variance


def calculate_average_d_electrons(composition: Dict[str, float]) -> float:
    """
    Calculate average d-electrons.
    Note: This is an approximation based on valence electrons for transition metals.
    For simplicity, we use valence electrons as a proxy if specific d-electron data is not available.
    A more precise implementation would require a specific d-electron table.
    Here, we assume valence_electrons approximates d+ s electrons for transition metals.
    """
    # For this implementation, we use valence electrons as a proxy for d-electrons
    # if specific d-electron counts are not in the periodic table data.
    # If the data source had a 'd_electrons' column, we would use that.
    # Since T006 provides 'valence_electrons', we use that.
    return calculate_valence_electron_concentration(composition)


def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic size mismatch (delta).
    delta = sqrt(sum(c_i * (1 - r_i / r_bar)^2))
    where r_bar is the average atomic radius.
    """
    radii = []
    weights = []
    for elem, frac in composition.items():
        r = get_element_property(elem, "atomic_radii")
        if r is None:
            logger.warning(f"Atomic radii not found for {elem}, skipping.")
            continue
        radii.append(r)
        weights.append(frac)

    if not radii:
        return 0.0

    weights_arr = np.array(weights)
    radii_arr = np.array(radii)
    r_bar = np.average(radii_arr, weights=weights_arr)

    if r_bar == 0:
        return 0.0

    mismatch = np.sqrt(np.average(((1 - radii_arr / r_bar) ** 2), weights=weights_arr))
    return mismatch


def compute_descriptors_row(row: pd.Series) -> Dict[str, float]:
    """
    Compute all descriptors for a single row of a DataFrame.

    Args:
        row: A pandas Series containing at least a 'composition' field.

    Returns:
        Dictionary of computed descriptors.
    """
    comp_str = row.get("composition")
    if not comp_str or not isinstance(comp_str, str):
        raise ValueError(f"Invalid or missing composition in row: {row}")

    composition = parse_composition_string(comp_str)

    return {
        "avg_electronegativity": calculate_average_electronegativity(composition),
        "valence_electron_concentration": calculate_valence_electron_concentration(composition),
        "atomic_radii_variance": calculate_atomic_radii_variance(composition),
        "avg_d_electrons": calculate_average_d_electrons(composition),
        "atomic_size_mismatch": calculate_atomic_size_mismatch(composition)
    }


def calculate_all_descriptors(row: pd.Series) -> Dict[str, float]:
    """
    Wrapper to compute descriptors for a row.

    Args:
        row: A pandas Series containing composition data.

    Returns:
        Dictionary of descriptors.
    """
    return compute_descriptors_row(row)


def main():
    """Test function for descriptor calculation."""
    # Example usage
    test_row = pd.Series({"composition": "Co2MnGa"})
    try:
        result = calculate_all_descriptors(test_row)
        print(f"Descriptors for Co2MnGa: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
