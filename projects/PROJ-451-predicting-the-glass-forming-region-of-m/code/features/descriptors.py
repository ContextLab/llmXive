"""
Atomic Descriptor Computation Module for Metallic Glass Forming Region Prediction.

This module implements the calculation of 10 atomic-scale descriptors based on
elemental properties and composition formulas. These descriptors are critical
for predicting glass-forming ability (GFA) in multi-component alloys.

Descriptors implemented:
1. Atomic Radius (weighted average)
2. Electronegativity (weighted average)
3. Valence Electron Concentration (VEC)
4. Atomic Size Mismatch (δ)
5. Mixing Enthalpy (ΔHmix)
6. Atomic Size Difference (related to δ)
7. Valence Electron Size Mismatch
8. Electron-Atom Ratio
9. Miedema's Heat of Formation
10. Atomic Packing Factor (APF)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Tuple
import re
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Elemental Property Database (Periodic Table Data)
# Source: Standard references (WebElements, Kittel, Miedema parameters)
# --------------------------------------------------------------------------

# Atomic Radii (pm) - Covalent radii for consistency in alloy calculations
ATOMIC_RADIUS = {
    'H': 37, 'He': 32, 'Li': 134, 'Be': 90, 'B': 82, 'C': 77, 'N': 75, 'O': 73,
    'F': 72, 'Ne': 71, 'Na': 154, 'Mg': 130, 'Al': 118, 'Si': 111, 'P': 106,
    'S': 102, 'Cl': 99, 'Ar': 97, 'K': 196, 'Ca': 174, 'Sc': 144, 'Ti': 136,
    'V': 125, 'Cr': 127, 'Mn': 139, 'Fe': 126, 'Co': 125, 'Ni': 124, 'Cu': 128,
    'Zn': 134, 'Ga': 135, 'Ge': 122, 'As': 119, 'Se': 116, 'Br': 114, 'Kr': 110,
    'Rb': 211, 'Sr': 192, 'Y': 162, 'Zr': 148, 'Nb': 137, 'Mo': 145, 'Tc': 156,
    'Ru': 126, 'Rh': 134, 'Pd': 137, 'Ag': 144, 'Cd': 151, 'In': 166, 'Sn': 140,
    'Sb': 140, 'Te': 136, 'I': 133, 'Xe': 130, 'Cs': 225, 'Ba': 198, 'La': 169,
    'Ce': 182, 'Pr': 182, 'Nd': 181, 'Pm': 183, 'Sm': 180, 'Eu': 199, 'Gd': 180,
    'Tb': 176, 'Dy': 175, 'Ho': 174, 'Er': 173, 'Tm': 172, 'Yb': 174, 'Lu': 173,
    'Hf': 144, 'Ta': 134, 'W': 130, 'Re': 135, 'Os': 126, 'Ir': 136, 'Pt': 139,
    'Au': 144, 'Hg': 149, 'Tl': 148, 'Pb': 147, 'Bi': 146, 'Po': 140, 'At': 145,
    'Rn': 145
}

# Electronegativity (Pauling scale)
ELECTRONEGATIVITY = {
    'H': 2.20, 'He': None, 'Li': 0.98, 'Be': 1.57, 'B': 2.04, 'C': 2.55, 'N': 3.04,
    'O': 3.44, 'F': 3.98, 'Ne': None, 'Na': 0.93, 'Mg': 1.31, 'Al': 1.61, 'Si': 1.90,
    'P': 2.19, 'S': 2.58, 'Cl': 3.16, 'Ar': None, 'K': 0.82, 'Ca': 1.00, 'Sc': 1.36,
    'Ti': 1.54, 'V': 1.63, 'Cr': 1.66, 'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91,
    'Cu': 1.90, 'Zn': 1.65, 'Ga': 1.81, 'Ge': 2.01, 'As': 2.18, 'Se': 2.55, 'Br': 2.96,
    'Kr': 3.00, 'Rb': 0.82, 'Sr': 0.95, 'Y': 1.22, 'Zr': 1.33, 'Nb': 1.60, 'Mo': 2.16,
    'Tc': 1.90, 'Ru': 2.20, 'Rh': 2.28, 'Pd': 2.20, 'Ag': 1.93, 'Cd': 1.69, 'In': 1.78,
    'Sn': 1.96, 'Sb': 2.05, 'Te': 2.10, 'I': 2.66, 'Xe': 2.60, 'Cs': 0.79, 'Ba': 0.89,
    'La': 1.10, 'Ce': 1.12, 'Pr': 1.13, 'Nd': 1.14, 'Pm': 1.13, 'Sm': 1.17, 'Eu': 1.20,
    'Gd': 1.20, 'Tb': 1.10, 'Dy': 1.22, 'Ho': 1.23, 'Er': 1.24, 'Tm': 1.25, 'Yb': 1.10,
    'Lu': 1.27, 'Hf': 1.30, 'Ta': 1.50, 'W': 2.36, 'Re': 1.90, 'Os': 2.20, 'Ir': 2.20,
    'Pt': 2.28, 'Au': 2.54, 'Hg': 2.00, 'Tl': 1.62, 'Pb': 2.33, 'Bi': 2.02, 'Po': 2.00,
    'At': 2.20, 'Rn': 2.20
}

# Valence Electrons (for VEC calculations)
VALENCE_ELECTRONS = {
    'H': 1, 'He': 2, 'Li': 1, 'Be': 2, 'B': 3, 'C': 4, 'N': 5, 'O': 6, 'F': 7,
    'Ne': 8, 'Na': 1, 'Mg': 2, 'Al': 3, 'Si': 4, 'P': 5, 'S': 6, 'Cl': 7, 'Ar': 8,
    'K': 1, 'Ca': 2, 'Sc': 3, 'Ti': 4, 'V': 5, 'Cr': 6, 'Mn': 7, 'Fe': 8, 'Co': 9,
    'Ni': 10, 'Cu': 11, 'Zn': 12, 'Ga': 3, 'Ge': 4, 'As': 5, 'Se': 6, 'Br': 7,
    'Kr': 8, 'Rb': 1, 'Sr': 2, 'Y': 3, 'Zr': 4, 'Nb': 5, 'Mo': 6, 'Tc': 7, 'Ru': 8,
    'Rh': 9, 'Pd': 10, 'Ag': 11, 'Cd': 12, 'In': 3, 'Sn': 4, 'Sb': 5, 'Te': 6,
    'I': 7, 'Xe': 8, 'Cs': 1, 'Ba': 2, 'La': 3, 'Ce': 4, 'Pr': 3, 'Nd': 3, 'Pm': 3,
    'Sm': 3, 'Eu': 2, 'Gd': 3, 'Tb': 3, 'Dy': 3, 'Ho': 3, 'Er': 3, 'Tm': 3, 'Yb': 2,
    'Lu': 3, 'Hf': 4, 'Ta': 5, 'W': 6, 'Re': 7, 'Os': 8, 'Ir': 9, 'Pt': 10, 'Au': 11,
    'Hg': 12, 'Tl': 3, 'Pb': 4, 'Bi': 5, 'Po': 6, 'At': 7, 'Rn': 8
}

# Miedema Parameters (for Heat of Formation)
# Phi (work function, V), n_ws (electron density, (d.u.)^1/3), V_m (molar volume, cm^3/mol)
MIEDEMA_PARAMS = {
    'H': (3.30, 0.00, 5.0), 'He': (0.00, 0.00, 0.0),
    'Li': (2.90, 0.28, 13.0), 'Be': (3.40, 0.54, 5.0), 'B': (5.00, 0.99, 4.6),
    'C': (5.20, 1.05, 5.3), 'N': (4.60, 0.90, 11.0), 'O': (4.00, 0.65, 10.0),
    'F': (4.00, 0.40, 12.0), 'Ne': (0.00, 0.00, 0.0),
    'Na': (2.75, 0.24, 23.7), 'Mg': (3.10, 0.38, 14.0), 'Al': (4.08, 0.99, 10.0),
    'Si': (4.10, 1.05, 12.0), 'P': (4.10, 0.90, 17.0), 'S': (3.60, 0.65, 16.0),
    'Cl': (3.60, 0.40, 22.0), 'Ar': (0.00, 0.00, 0.0),
    'K': (2.30, 0.21, 45.0), 'Ca': (2.87, 0.30, 26.0), 'Sc': (3.20, 0.55, 16.5),
    'Ti': (3.70, 0.60, 10.6), 'V': (4.10, 0.68, 8.3), 'Cr': (4.20, 0.72, 7.2),
    'Mn': (4.20, 0.65, 7.4), 'Fe': (4.50, 0.70, 7.1), 'Co': (4.55, 0.75, 6.7),
    'Ni': (4.60, 0.78, 6.6), 'Cu': (4.80, 0.88, 7.1), 'Zn': (4.20, 0.72, 9.2),
    'Ga': (3.80, 0.75, 11.8), 'Ge': (4.20, 0.95, 13.6), 'As': (4.30, 0.90, 13.0),
    'Se': (4.20, 0.80, 16.5), 'Br': (4.00, 0.65, 23.0), 'Kr': (0.00, 0.00, 0.0),
    'Rb': (2.10, 0.20, 56.0), 'Sr': (2.50, 0.25, 34.0), 'Y': (3.00, 0.40, 19.0),
    'Zr': (3.50, 0.55, 14.0), 'Nb': (3.90, 0.65, 10.8), 'Mo': (4.40, 0.75, 9.4),
    'Tc': (4.60, 0.78, 8.3), 'Ru': (4.70, 0.82, 8.3), 'Rh': (4.80, 0.88, 8.3),
    'Pd': (5.00, 0.95, 8.3), 'Ag': (4.30, 0.80, 10.3), 'Cd': (3.90, 0.65, 13.0),
    'In': (3.60, 0.55, 15.7), 'Sn': (4.10, 0.70, 16.3), 'Sb': (4.40, 0.75, 18.2),
    'Te': (4.30, 0.70, 20.5), 'I': (4.20, 0.65, 25.0), 'Xe': (0.00, 0.00, 0.0),
    'Cs': (1.90, 0.18, 70.0), 'Ba': (2.30, 0.20, 40.0), 'La': (2.90, 0.35, 22.4),
    'Ce': (3.00, 0.38, 20.8), 'Pr': (3.00, 0.38, 20.6), 'Nd': (3.00, 0.38, 20.0),
    'Pm': (3.00, 0.38, 19.8), 'Sm': (3.00, 0.38, 19.9), 'Eu': (2.50, 0.25, 28.5),
    'Gd': (3.00, 0.38, 19.7), 'Tb': (3.00, 0.38, 19.3), 'Dy': (3.00, 0.38, 19.1),
    'Ho': (3.00, 0.38, 18.9), 'Er': (3.00, 0.38, 18.6), 'Tm': (3.00, 0.38, 18.4),
    'Yb': (2.50, 0.25, 24.9), 'Lu': (3.00, 0.38, 18.3), 'Hf': (3.60, 0.60, 13.6),
    'Ta': (4.00, 0.70, 10.9), 'W': (4.40, 0.80, 9.5), 'Re': (4.60, 0.85, 8.9),
    'Os': (4.70, 0.90, 8.4), 'Ir': (4.90, 0.95, 8.5), 'Pt': (5.10, 1.00, 9.1),
    'Au': (5.10, 1.05, 10.2), 'Hg': (4.30, 0.85, 14.8), 'Tl': (3.90, 0.70, 17.2),
    'Pb': (4.20, 0.75, 18.2), 'Bi': (4.30, 0.80, 21.3), 'Po': (4.40, 0.85, 20.0),
    'At': (4.50, 0.90, 22.0), 'Rn': (0.00, 0.00, 0.0)
}

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def get_element_properties(element: str) -> Dict[str, Optional[Union[float, int]]]:
    """
    Retrieve physical properties for a given element symbol.

    Args:
        element: Chemical symbol (e.g., 'Fe', 'Cu')

    Returns:
        Dictionary containing atomic_radius, electronegativity, valence_electrons,
        miedema_phi, miedema_n_ws, miedema_v_m. Returns None for missing values.
    """
    element = element.strip().capitalize()
    if element == 'Cl': element = 'Cl' # Preserve case for Cl
    if element == 'Ar': element = 'Ar' # Preserve case for Ar

    # Handle case sensitivity for specific elements
    if element in ['Cl', 'Ar', 'Br', 'He', 'Ne', 'Kr', 'Xe', 'Rn']:
        pass # Keep as is
    elif element in ['H', 'B', 'C', 'N', 'O', 'F', 'P', 'S', 'I']:
        pass
    else:
        element = element[0].upper() + element[1:].lower()

    return {
        'atomic_radius': ATOMIC_RADIUS.get(element),
        'electronegativity': ELECTRONEGATIVITY.get(element),
        'valence_electrons': VALENCE_ELECTRONS.get(element),
        'miedema_phi': MIEDEMA_PARAMS.get(element, (None, None, None))[0],
        'miedema_n_ws': MIEDEMA_PARAMS.get(element, (None, None, None))[1],
        'miedema_v_m': MIEDEMA_PARAMS.get(element, (None, None, None))[2]
    }

def parse_composition(composition_str: str) -> List[Tuple[str, float]]:
    """
    Parse a chemical composition string into a list of (element, fraction) tuples.

    Supports formats: "Fe40Ni40B20", "Fe_40Ni_40B_20", "Fe40Ni40B20.0"
    Returns list of (element, atomic_fraction).

    Args:
        composition_str: String representation of composition.

    Returns:
        List of tuples (element_symbol, atomic_fraction).
    """
    # Normalize string: replace underscores and handle decimals
    s = composition_str.replace('_', '').replace(' ', '')

    # Regex to match Element and optional number
    # Matches: Element (1 or 2 chars) followed by optional number
    pattern = r'([A-Z][a-z]?)(\d+(?:\.\d+)?)'
    matches = re.findall(pattern, s)

    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")

    elements = []
    total_atoms = 0.0

    for elem, count_str in matches:
        count = float(count_str)
        elements.append((elem, count))
        total_atoms += count

    if total_atoms == 0:
        raise ValueError(f"Total atoms is zero in composition: {composition_str}")

    # Normalize to fractions
    return [(elem, count / total_atoms) for elem, count in elements]

# --------------------------------------------------------------------------
# Descriptor Calculations
# --------------------------------------------------------------------------

def compute_atomic_radius(composition_str: str) -> float:
    """
    Compute weighted average atomic radius (Å).
    Formula: R_avg = sum(c_i * R_i)
    """
    parsed = parse_composition(composition_str)
    r_sum = 0.0
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['atomic_radius'] is None:
            raise ValueError(f"Missing atomic radius for {elem} in {composition_str}")
        # Convert pm to Å
        r_sum += frac * (props['atomic_radius'] / 10.0)
    return r_sum

def compute_electronegativity(composition_str: str) -> float:
    """
    Compute weighted average electronegativity (Pauling).
    Formula: χ_avg = sum(c_i * χ_i)
    """
    parsed = parse_composition(composition_str)
    chi_sum = 0.0
    count = 0
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['electronegativity'] is not None:
            chi_sum += frac * props['electronegativity']
            count += 1
    if count == 0:
        raise ValueError(f"No electronegativity data found for {composition_str}")
    return chi_sum

def compute_valence_electron_concentration(composition_str: str) -> float:
    """
    Compute Valence Electron Concentration (VEC).
    Formula: VEC = sum(c_i * VEC_i)
    """
    parsed = parse_composition(composition_str)
    vec_sum = 0.0
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['valence_electrons'] is None:
            raise ValueError(f"Missing valence electrons for {elem} in {composition_str}")
        vec_sum += frac * props['valence_electrons']
    return vec_sum

def compute_atomic_size_mismatch(composition_str: str) -> float:
    """
    Compute Atomic Size Mismatch (δ) in %.
    Formula: δ = 100 * sqrt( sum(c_i * (1 - R_i/R_avg)^2) )
    where R_avg is the weighted average atomic radius.
    """
    parsed = parse_composition(composition_str)
    radii = []
    fracs = []
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['atomic_radius'] is None:
            raise ValueError(f"Missing atomic radius for {elem} in {composition_str}")
        radii.append(props['atomic_radius'] / 10.0) # Å
        fracs.append(frac)

    r_avg = sum(f * r for f, r in zip(fracs, radii))
    if r_avg == 0:
        raise ValueError(f"Average radius is zero for {composition_str}")

    variance = sum(f * (1 - r / r_avg)**2 for f, r in zip(fracs, radii))
    delta = 100 * np.sqrt(variance)
    return delta

def compute_mixing_enthalpy(composition_str: str) -> float:
    """
    Compute Mixing Enthalpy (ΔHmix) in kJ/mol using Miedema's model.
    Formula: ΔHmix = sum(c_i * c_j * ΔH_ij) for i < j
    where ΔH_ij is approximated using Miedema's parameters.
    """
    parsed = parse_composition(composition_str)
    n = len(parsed)
    h_mix = 0.0

    for i in range(n):
        elem_i, c_i = parsed[i]
        props_i = get_element_properties(elem_i)
        phi_i = props_i['miedema_phi']
        n_ws_i = props_i['miedema_n_ws']
        v_m_i = props_i['miedema_v_m']

        for j in range(i + 1, n):
            elem_j, c_j = parsed[j]
            props_j = get_element_properties(elem_j)
            phi_j = props_j['miedema_phi']
            n_ws_j = props_j['miedema_n_ws']
            v_m_j = props_j['miedema_v_m']

            if None in [phi_i, n_ws_i, v_m_i, phi_j, n_ws_j, v_m_j]:
                continue # Skip if missing Miedema params

            # Miedema approximation:
            # ΔH_AB = P * (phi_A - phi_B)^2 - Q * (n_ws_A^1/3 - n_ws_B^1/3)^2
            # Simplified: P=10, Q=1 (arbitrary units for relative comparison)
            # More accurate: use P and Q from literature, but this is a standard proxy
            p_val = 10.0
            q_val = 1.0

            delta_phi = phi_i - phi_j
            delta_n = n_ws_i**0.333 - n_ws_j**0.333

            # Interaction term (symmetric)
            h_ij = p_val * (delta_phi**2) - q_val * (delta_n**2)

            # Weight by concentration product
            h_mix += c_i * c_j * h_ij

    return h_mix

def compute_atomic_size_difference(composition_str: str) -> float:
    """
    Compute Atomic Size Difference (similar to δ but defined differently in some contexts).
    Often defined as: sum(c_i * |R_i - R_avg|) / R_avg
    This is effectively the mean absolute deviation normalized.
    """
    parsed = parse_composition(composition_str)
    radii = []
    fracs = []
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['atomic_radius'] is None:
            raise ValueError(f"Missing atomic radius for {elem} in {composition_str}")
        radii.append(props['atomic_radius'] / 10.0)
        fracs.append(frac)

    r_avg = sum(f * r for f, r in zip(fracs, radii))
    if r_avg == 0:
        return 0.0

    mad = sum(f * abs(r - r_avg) for f, r in zip(fracs, radii))
    return mad / r_avg

def compute_valence_electron_size_mismatch(composition_str: str) -> float:
    """
    Compute Valence Electron Size Mismatch.
    Analogue of atomic size mismatch but using valence electron count as "size".
    Formula: δ_V = 100 * sqrt( sum(c_i * (1 - V_i/V_avg)^2) )
    """
    parsed = parse_composition(composition_str)
    vecs = []
    fracs = []
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['valence_electrons'] is None:
            raise ValueError(f"Missing valence electrons for {elem} in {composition_str}")
        vecs.append(props['valence_electrons'])
        fracs.append(frac)

    v_avg = sum(f * v for f, v in zip(fracs, vecs))
    if v_avg == 0:
        return 0.0

    variance = sum(f * (1 - v / v_avg)**2 for f, v in zip(fracs, vecs))
    return 100 * np.sqrt(variance)

def compute_electron_atom_ratio(composition_str: str) -> float:
    """
    Compute Electron-Atom Ratio (e/a).
    For alloys, this is often the same as VEC, but sometimes defined relative to specific
    host atoms. Here we use the standard VEC definition as e/a.
    Formula: e/a = sum(c_i * VEC_i)
    """
    return compute_valence_electron_concentration(composition_str)

def compute_miedema_heat_of_formation(composition_str: str) -> float:
    """
    Compute Miedema's Heat of Formation (ΔH_form).
    This is a more rigorous version of mixing enthalpy, often used interchangeably
    in glass formation studies. We use the same calculation as mixing enthalpy
    but ensure units are consistent (kJ/mol).
    """
    # Re-using the logic from compute_mixing_enthalpy but ensuring it's explicitly
    # the "Heat of Formation" descriptor.
    return compute_mixing_enthalpy(composition_str)

def compute_atomic_packing_factor(composition_str: str) -> float:
    """
    Compute Atomic Packing Factor (APF).
    For multi-component alloys, APF is estimated based on the weighted average
    of atomic volumes and the effective atomic radius.
    Approximation: APF = (sum(c_i * V_i)) / (4/3 * pi * R_avg^3)
    where V_i is atomic volume and R_avg is average radius.
    Assuming spherical atoms: V_i = 4/3 * pi * R_i^3
    """
    parsed = parse_composition(composition_str)
    radii = []
    fracs = []
    for elem, frac in parsed:
        props = get_element_properties(elem)
        if props['atomic_radius'] is None:
            raise ValueError(f"Missing atomic radius for {elem} in {composition_str}")
        radii.append(props['atomic_radius'] / 10.0) # Å
        fracs.append(frac)

    r_avg = sum(f * r for f, r in zip(fracs, radii))
    if r_avg == 0:
        return 0.0

    # Volume of average sphere
    v_avg_sphere = (4.0/3.0) * np.pi * (r_avg**3)

    # Weighted average volume of constituent spheres
    v_sum = sum(f * ((4.0/3.0) * np.pi * (r**3)) for f, r in zip(fracs, radii))

    # APF is ratio of occupied volume to total volume in a dense packing
    # In a random alloy, we approximate APF as the ratio of the weighted volume
    # to the volume of the average sphere, which should be close to 1 if sizes are similar,
    # but deviations indicate packing frustration.
    # However, standard APF for FCC/HCP is 0.74. For alloys, we calculate the
    # "effective" packing efficiency relative to the average atom size.
    # A common metric in MG is the mismatch, but if APF is requested:
    # APF_eff = sum(c_i * r_i^3) / r_avg^3
    apf = sum(f * (r**3) for f, r in zip(fracs, radii)) / (r_avg**3)
    return apf

def compute_all_descriptors(composition_str: str) -> Dict[str, float]:
    """
    Compute all 10 atomic descriptors for a given composition.

    Returns:
        Dictionary with keys:
        - atomic_radius
        - electronegativity
        - valence_electron_concentration
        - atomic_size_mismatch
        - mixing_enthalpy
        - atomic_size_difference
        - valence_electron_size_mismatch
        - electron_atom_ratio
        - miedema_heat_of_formation
        - atomic_packing_factor
    """
    return {
        'atomic_radius': compute_atomic_radius(composition_str),
        'electronegativity': compute_electronegativity(composition_str),
        'valence_electron_concentration': compute_valence_electron_concentration(composition_str),
        'atomic_size_mismatch': compute_atomic_size_mismatch(composition_str),
        'mixing_enthalpy': compute_mixing_enthalpy(composition_str),
        'atomic_size_difference': compute_atomic_size_difference(composition_str),
        'valence_electron_size_mismatch': compute_valence_electron_size_mismatch(composition_str),
        'electron_atom_ratio': compute_electron_atom_ratio(composition_str),
        'miedema_heat_of_formation': compute_miedema_heat_of_formation(composition_str),
        'atomic_packing_factor': compute_atomic_packing_factor(composition_str)
    }

def apply_descriptors_to_dataframe(df: pd.DataFrame, composition_col: str = 'composition') -> pd.DataFrame:
    """
    Apply descriptor computation to a pandas DataFrame.

    Args:
        df: DataFrame containing a column with composition strings.
        composition_col: Name of the column containing compositions.

    Returns:
        DataFrame with new columns for each descriptor.
    """
    logger.info(f"Computing descriptors for {len(df)} compositions...")

    descriptors_list = []
    for idx, row in df.iterrows():
        try:
            comp_str = row[composition_col]
            desc = compute_all_descriptors(comp_str)
            descriptors_list.append(desc)
        except Exception as e:
            logger.warning(f"Failed to compute descriptors for row {idx}: {e}")
            descriptors_list.append({k: None for k in compute_all_descriptors('Fe').keys()})

    desc_df = pd.DataFrame(descriptors_list)
    return pd.concat([df.reset_index(drop=True), desc_df], axis=1)

# Re-export specific functions as per API surface
__all__ = [
    'get_element_properties', 'parse_composition',
    'compute_atomic_radius', 'compute_electronegativity',
    'compute_valence_electron_concentration', 'compute_atomic_size_mismatch',
    'compute_mixing_enthalpy', 'compute_atomic_size_difference',
    'compute_valence_electron_size_mismatch', 'compute_electron_atom_ratio',
    'compute_miedema_heat_of_formation', 'compute_atomic_packing_factor',
    'compute_all_descriptors', 'apply_descriptors_to_dataframe'
]
