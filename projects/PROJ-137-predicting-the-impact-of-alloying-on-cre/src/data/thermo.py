"""
Thermodynamic descriptor calculations for alloy analysis.

This module provides functions to calculate thermodynamic properties
such as mixing enthalpy and atomic radius mismatch based on alloy composition
and elemental properties.

These calculations are critical for the 'Thermodynamic GBR' model features.
"""

import numpy as np
from typing import Dict, List, Union

def calculate_radius_mismatch(
    composition: Dict[str, float],
    element_data: Dict[str, Dict[str, float]]
) -> float:
    """
    Calculate the atomic radius mismatch (delta) for an alloy.

    Formula:
    delta = sqrt( sum_i [ c_i * (1 - r_i / r_avg)^2 ] )
    where:
      c_i = atomic fraction of element i
      r_i = atomic radius of element i
      r_avg = sum_i (c_i * r_i) = average atomic radius

    Args:
        composition: Dictionary mapping element symbol to atomic fraction.
        element_data: Dictionary mapping element symbol to a dict containing 'atomic_radius'.

    Returns:
        float: The radius mismatch parameter (delta).

    Raises:
        KeyError: If an element in composition is not found in element_data.
    """
    # Calculate average atomic radius
    r_avg = 0.0
    for elem, frac in composition.items():
        if elem not in element_data:
            raise KeyError(f"Element {elem} not found in element_data")
        r_avg += frac * element_data[elem]["atomic_radius"]

    if r_avg == 0:
        return 0.0

    # Calculate delta
    delta_sq_sum = 0.0
    for elem, frac in composition.items():
        r_i = element_data[elem]["atomic_radius"]
        term = frac * (1.0 - (r_i / r_avg)) ** 2
        delta_sq_sum += term

    return np.sqrt(delta_sq_sum)


def calculate_mixing_enthalpy(
    composition: Dict[str, float],
    element_data: Dict[str, Dict[str, float]]
) -> float:
    """
    Calculate the mixing enthalpy (Delta_H_mix) for an alloy.

    This implementation uses a simplified model based on electronegativity differences
    as a proxy for interaction energy, as full Miedema calculations require extensive
    database lookups not always available in a lightweight pipeline.
    
    Simplified Model:
    Delta_H_mix = sum_{i < j} ( Omega_ij * c_i * c_j )
    where Omega_ij = (chi_i - chi_j)^2 * K
    (K is a scaling constant, set to 100 for this implementation to match typical units)

    Note: In a production environment with full thermodynamic databases (e.g., Calphad),
    this would be replaced by actual enthalpy of mixing values from the database.
    For this research pipeline, we use this proxy to generate consistent features
    for the model training (T023) and to satisfy the "thermodynamic descriptor" requirement.

    Args:
        composition: Dictionary mapping element symbol to atomic fraction.
        element_data: Dictionary mapping element symbol to a dict containing 'electronegativity'.

    Returns:
        float: The mixing enthalpy (in arbitrary units consistent with the proxy model).

    Raises:
        KeyError: If an element in composition is not found in element_data.
    """
    elements = list(composition.keys())
    n = len(elements)
    delta_h = 0.0
    K = 100.0  # Scaling constant for the simplified model

    for i in range(n):
        elem_i = elements[i]
        if elem_i not in element_data:
            raise KeyError(f"Element {elem_i} not found in element_data")
        chi_i = element_data[elem_i]["electronegativity"]
        c_i = composition[elem_i]

        for j in range(i + 1, n):
            elem_j = elements[j]
            if elem_j not in element_data:
                raise KeyError(f"Element {elem_j} not found in element_data")
            chi_j = element_data[elem_j]["electronegativity"]
            c_j = composition[elem_j]

            # Interaction parameter proxy
            omega_ij = (chi_i - chi_j) ** 2 * K
            delta_h += omega_ij * c_i * c_j

    return delta_h


def calculate_thermodynamic_descriptors(
    composition: Dict[str, float],
    element_data: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    Calculate all thermodynamic descriptors for a given alloy composition.

    This function aggregates the individual calculations into a single result dictionary.

    Args:
        composition: Dictionary mapping element symbol to atomic fraction.
        element_data: Dictionary mapping element symbol to elemental properties.

    Returns:
        Dict[str, float]: A dictionary containing:
            - 'mixing_enthalpy': Calculated mixing enthalpy.
            - 'radius_mismatch': Calculated radius mismatch.
    """
    return {
        "mixing_enthalpy": calculate_mixing_enthalpy(composition, element_data),
        "radius_mismatch": calculate_radius_mismatch(composition, element_data)
    }