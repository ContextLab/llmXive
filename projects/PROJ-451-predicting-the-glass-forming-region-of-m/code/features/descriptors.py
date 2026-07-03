"""
Atomic Descriptors for Metallic Glass Prediction.

This module computes 10 atomic-scale descriptors used to predict the
glass-forming region of metallic alloys. The descriptors are based on
elemental properties (atomic radius, electronegativity, valence electrons)
and mixture rules.

Formulas are derived from established literature on metallic glass formation
(e.g., Inoue's criteria, Miedema's model, and statistical analyses of
amorphous vs crystalline phases).

Dependencies:
    - pandas: for DataFrame handling
    - numpy: for numerical operations
    - periodictable: for elemental properties (must be installed)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional
import re

try:
    import periodictable as pt
except ImportError:
    raise ImportError(
        "The 'periodictable' package is required to compute atomic descriptors. "
        "Install it via: pip install periodictable"
    )

# Constants
R_H = 13.6  # Rydberg constant in eV (used in Miedema calculations)
K_MIEDema = 10.0  # Empirical constant for Miedema's heat of formation (approx)


def get_element_properties(symbol: str) -> Dict[str, float]:
    """
    Retrieve atomic properties for a given element symbol.

    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Zr').

    Returns:
        Dictionary with keys: 'radius', 'electronegativity', 'valence', 'mass'.
    """
    symbol = symbol.strip().capitalize()
    try:
        el = pt.elements[symbol]
    except (KeyError, IndexError):
        raise ValueError(f"Invalid element symbol: {symbol}")

    return {
        'radius': el.radius,  # Covalent radius in Angstroms (or atomic if covalent missing)
        'electronegativity': el.chem.electronegativity if hasattr(el, 'chem') else 0.0,
        'valence': el.chem.valence if hasattr(el, 'chem') else 0.0,
        'mass': el.mass
    }


def parse_composition(formula: str) -> Dict[str, float]:
    """
    Parse a chemical formula string into a dictionary of element counts.
    Handles standard notation (e.g., 'Zr50Cu40Al10', 'Fe2O3').

    Args:
        formula: Chemical formula string.

    Returns:
        Dictionary mapping element symbols to their atomic counts.
    """
    # Regex to match element symbols and optional counts
    pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
    matches = pattern.findall(formula.replace(' ', ''))
    composition = {}
    for element, count in matches:
        count = int(count) if count else 1
        composition[element] = count
    return composition


def compute_atomic_radius(composition: Dict[str, float]) -> float:
    """
    Compute the average atomic radius (weighted by atomic fraction).

    Formula: R_avg = sum(x_i * R_i)

    Args:
        composition: Dict of element -> count.

    Returns:
        Average atomic radius in Angstroms.
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    weighted_sum = 0.0
    for el, count in composition.items():
        props = get_element_properties(el)
        weighted_sum += (count / total_atoms) * props['radius']

    return weighted_sum


def compute_electronegativity(composition: Dict[str, float]) -> float:
    """
    Compute the average electronegativity (weighted by atomic fraction).

    Formula: Chi_avg = sum(x_i * Chi_i)

    Args:
        composition: Dict of element -> count.

    Returns:
        Average electronegativity (Pauling scale).
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    weighted_sum = 0.0
    for el, count in composition.items():
        props = get_element_properties(el)
        weighted_sum += (count / total_atoms) * props['electronegativity']

    return weighted_sum


def compute_valence_electron_concentration(composition: Dict[str, float]) -> float:
    """
    Compute the Valence Electron Concentration (VEC).

    Formula: VEC = sum(x_i * V_i)

    Args:
        composition: Dict of element -> count.

    Returns:
        Average valence electron count.
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    weighted_sum = 0.0
    for el, count in composition.items():
        props = get_element_properties(el)
        weighted_sum += (count / total_atoms) * props['valence']

    return weighted_sum


def compute_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Compute Atomic Size Mismatch (delta, δ).

    Formula: δ = 100 * sqrt( sum(x_i * (1 - R_i/R_avg)^2) )

    This quantifies the deviation of atomic sizes from the mean.

    Args:
        composition: Dict of element -> count.

    Returns:
        Atomic size mismatch in percent (%).
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    # Calculate R_avg first
    r_avg = compute_atomic_radius(composition)
    if r_avg == 0:
        return 0.0

    variance_sum = 0.0
    for el, count in composition.items():
        props = get_element_properties(el)
        r_i = props['radius']
        x_i = count / total_atoms
        variance_sum += x_i * ((1 - (r_i / r_avg)) ** 2)

    return 100.0 * np.sqrt(variance_sum)


def compute_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Compute the Mixing Enthalpy (Delta H_mix) using the Miedema model approximation.

    Formula: Delta H_mix = sum_{i != j} (x_i * x_j * Omega_ij)
    Where Omega_ij is the interaction enthalpy between elements i and j.
    For simplicity, we use a simplified Miedema-like estimation based on
    electronegativity difference and atomic volume if detailed Miedema parameters
    are not available in the lightweight periodictable library.

    Approximation: Omega_ij approx -2 * (Chi_i - Chi_j)^2 (Empirical fit for metallic glasses)
    Note: A full Miedema implementation requires tabulated Phi and n_ws values.
    We use a heuristic based on electronegativity difference which correlates
    well with mixing enthalpy in many metallic systems.

    Args:
        composition: Dict of element -> count.

    Returns:
        Mixing enthalpy in arbitrary units (correlated with kJ/mol).
    """
    elements = list(composition.keys())
    counts = [composition[el] for el in elements]
    total_atoms = sum(counts)
    if total_atoms == 0:
        return 0.0

    mole_fracs = [c / total_atoms for c in counts]
    electronegativities = [get_element_properties(el)['electronegativity'] for el in elements]

    delta_h = 0.0
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            x_i, x_j = mole_fracs[i], mole_fracs[j]
            chi_i, chi_j = electronegativities[i], electronegativities[j]
            # Heuristic interaction term
            omega_ij = -4.0 * (chi_i - chi_j) ** 2
            delta_h += 2.0 * x_i * x_j * omega_ij

    return delta_h


def compute_atomic_size_difference(composition: Dict[str, float]) -> float:
    """
    Compute Atomic Size Difference (often related to mismatch but focusing on max-min).

    Formula: SD = (R_max - R_min) / R_avg

    Args:
        composition: Dict of element -> count.

    Returns:
        Atomic size difference ratio.
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    radii = []
    for el in composition:
        radii.append(get_element_properties(el)['radius'])

    if not radii:
        return 0.0

    r_max = max(radii)
    r_min = min(radii)
    r_avg = compute_atomic_radius(composition)

    if r_avg == 0:
        return 0.0

    return (r_max - r_min) / r_avg


def compute_valence_electron_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Compute Valence Electron Size Mismatch.

    This is a composite descriptor combining valence electron concentration
    variance and atomic size variance.

    Formula: VESM = sqrt( Var(VEC) * Var(R) )
    Where Var(VEC) = sum(x_i * (V_i - V_avg)^2)
    And Var(R) = sum(x_i * (R_i - R_avg)^2)

    Args:
        composition: Dict of element -> count.

    Returns:
        Valence electron size mismatch value.
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    # Calculate averages
    v_avg = compute_valence_electron_concentration(composition)
    r_avg = compute_atomic_radius(composition)

    var_pec = 0.0
    var_r = 0.0

    for el, count in composition.items():
        x_i = count / total_atoms
        props = get_element_properties(el)
        v_i = props['valence']
        r_i = props['radius']

        var_pec += x_i * (v_i - v_avg) ** 2
        var_r += x_i * (r_i - r_avg) ** 2

    return np.sqrt(var_pec * var_r)


def compute_electron_atom_ratio(composition: Dict[str, float]) -> float:
    """
    Compute Electron-Atom Ratio (e/a).

    Formula: e/a = (sum(x_i * V_i)) / (sum(x_i))
    Since sum(x_i) = 1 in atomic fractions, this is equivalent to VEC.
    However, sometimes defined as total valence electrons per total atoms
    without normalization if counts are raw. Here we return the normalized VEC.

    Args:
        composition: Dict of element -> count.

    Returns:
        Electron-atom ratio.
    """
    return compute_valence_electron_concentration(composition)


def compute_miedema_heat_of_formation(composition: Dict[str, float]) -> float:
    """
    Compute Miedema's Heat of Formation (Delta H_f).

    This is a more rigorous approximation of the mixing enthalpy using
    Miedema's semi-empirical model concepts.
    Delta H_f = f(x_i, x_j, Phi, n_ws, V)
    Since full parameters aren't in periodictable, we use a refined
    electronegativity-based proxy that captures the chemical driving force.

    Formula: Delta H_f approx sum(x_i * x_j * (Phi_i - Phi_j)^2)
    (Using electronegativity as a proxy for work function Phi)

    Args:
        composition: Dict of element -> count.

    Returns:
        Miedema's heat of formation estimate.
    """
    elements = list(composition.keys())
    counts = [composition[el] for el in elements]
    total_atoms = sum(counts)
    if total_atoms == 0:
        return 0.0

    mole_fracs = [c / total_atoms for c in counts]
    # Using electronegativity as proxy for work function (Phi)
    phis = [get_element_properties(el)['electronegativity'] for el in elements]

    delta_h_f = 0.0
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            x_i, x_j = mole_fracs[i], mole_fracs[j]
            phi_diff = phis[i] - phis[j]
            # Miedema term approximation
            term = x_i * x_j * (phi_diff ** 2)
            delta_h_f += term

    return delta_h_f


def compute_atomic_packing_factor(composition: Dict[str, float]) -> float:
    """
    Compute Atomic Packing Factor (APF).

    APF is the fraction of volume in a crystal structure that is occupied by atoms.
    For a random alloy, we approximate APF based on the ratio of atomic volumes
    to the total volume, assuming hard spheres.
    APF approx sum(x_i * V_i) / V_avg_cell
    Since we don't have the cell volume, we approximate APF relative to a
    reference close-packed structure (APF ~ 0.74 for FCC/HCP).
    We calculate the effective atomic volume ratio.

    Formula: APF_approx = (sum(x_i * R_i^3)) / (R_avg^3) * C
    Where C is a scaling constant to match typical metallic glass APF (~0.60-0.68).
    We normalize such that a single element returns ~0.65.

    Args:
        composition: Dict of element -> count.

    Returns:
        Estimated atomic packing factor.
    """
    total_atoms = sum(composition.values())
    if total_atoms == 0:
        return 0.0

    r_avg = compute_atomic_radius(composition)
    if r_avg == 0:
        return 0.0

    weighted_vol_sum = 0.0
    for el, count in composition.items():
        props = get_element_properties(el)
        r_i = props['radius']
        x_i = count / total_atoms
        weighted_vol_sum += x_i * (r_i ** 3)

    # Normalize by average volume
    avg_vol = r_avg ** 3
    if avg_vol == 0:
        return 0.0

    # Scale to typical metallic glass APF range (0.60 - 0.68)
    # For a monoatomic sphere, ratio is 1. We want ~0.65.
    raw_apf = weighted_vol_sum / avg_vol
    return raw_apf * 0.65


def compute_all_descriptors(formula: str) -> Dict[str, float]:
    """
    Compute all 10 descriptors for a given chemical formula.

    Args:
        formula: Chemical formula string (e.g., 'Zr50Cu40Al10').

    Returns:
        Dictionary of descriptor names to computed values.
    """
    composition = parse_composition(formula)

    descriptors = {
        'atomic_radius': compute_atomic_radius(composition),
        'electronegativity': compute_electronegativity(composition),
        'valence_electron_concentration': compute_valence_electron_concentration(composition),
        'atomic_size_mismatch': compute_atomic_size_mismatch(composition),
        'mixing_enthalpy': compute_mixing_enthalpy(composition),
        'atomic_size_difference': compute_atomic_size_difference(composition),
        'valence_electron_size_mismatch': compute_valence_electron_size_mismatch(composition),
        'electron_atom_ratio': compute_electron_atom_ratio(composition),
        'miedema_heat_formation': compute_miedema_heat_of_formation(composition),
        'atomic_packing_factor': compute_atomic_packing_factor(composition)
    }

    return descriptors


def apply_descriptors_to_dataframe(df: pd.DataFrame, formula_col: str = 'formula') -> pd.DataFrame:
    """
    Apply descriptor computation to a pandas DataFrame.

    Args:
        df: Input DataFrame containing a column with chemical formulas.
        formula_col: Name of the column containing formulas.

    Returns:
        DataFrame with new columns for each descriptor.
    """
    descriptor_cols = [
        'atomic_radius', 'electronegativity', 'valence_electron_concentration',
        'atomic_size_mismatch', 'mixing_enthalpy', 'atomic_size_difference',
        'valence_electron_size_mismatch', 'electron_atom_ratio',
        'miedema_heat_formation', 'atomic_packing_factor'
    ]

    # Initialize columns with NaN
    for col in descriptor_cols:
        df[col] = np.nan

    for idx, row in df.iterrows():
        try:
            desc = compute_all_descriptors(row[formula_col])
            for col in descriptor_cols:
                df.at[idx, col] = desc[col]
        except Exception as e:
            # Log warning or handle error appropriately
            print(f"Warning: Failed to compute descriptors for formula '{row[formula_col]}': {e}")
            continue

    return df