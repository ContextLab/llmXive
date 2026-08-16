import math
import logging
from typing import Dict, Tuple, Optional, List, Any
import pandas as pd
import re
from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event

# Constants for oxidation states and ionic radii
# Using standard oxidation states for perovskite A and B sites
COMMON_OXIDATION_STATES = {
    'A': {
        'K': [1], 'Rb': [1], 'Cs': [1], 'Ba': [2], 'Sr': [2], 'Ca': [2], 'Na': [1], 'Li': [1]
    },
    'B': {
        'Ti': [4], 'Zr': [4], 'Hf': [4], 'Sn': [4], 'Ge': [4], 'Nb': [5], 'Ta': [5],
        'V': [5], 'Mn': [4], 'Fe': [3], 'Co': [3], 'Ni': [3], 'Cu': [3], 'Cr': [3],
        'Al': [3], 'Ga': [3], 'In': [3], 'Sc': [3], 'Y': [3], 'La': [3], 'Ce': [3],
        'Pr': [3], 'Nd': [3], 'Sm': [3], 'Eu': [3], 'Gd': [3], 'Tb': [3], 'Dy': [3],
        'Ho': [3], 'Er': [3], 'Tm': [3], 'Yb': [3], 'Lu': [3]
    },
    'X': {
        'F': [-1], 'Cl': [-1], 'Br': [-1], 'I': [-1], 'O': [-2], 'S': [-2]
    }
}

# Ionic radii in Angstroms (Shannon radii for coordination number 12 for A, 6 for B, 6 for X)
# Source: Shannon, R. D. (1976). Revised effective ionic radii and systematic studies of interatomic distances in halides and chalcogenides. Acta Crystallographica Section A: Crystal Physics, Diffraction, Theoretical and General Crystallography, 32(5), 751-767.
IONIC_RADII = {
    # A-site (CN=12)
    'K': 1.64, 'Rb': 1.72, 'Cs': 1.88, 'Ba': 1.61, 'Sr': 1.44, 'Ca': 1.34, 'Na': 1.39, 'Li': 1.00,
    # B-site (CN=6)
    'Ti': 0.605, 'Zr': 0.72, 'Hf': 0.71, 'Sn': 0.69, 'Ge': 0.53, 'Nb': 0.64, 'Ta': 0.64,
    'V': 0.54, 'Mn': 0.53, 'Fe': 0.645, 'Co': 0.61, 'Ni': 0.60, 'Cu': 0.73, 'Cr': 0.615,
    'Al': 0.535, 'Ga': 0.62, 'In': 0.80, 'Sc': 0.745, 'Y': 0.90, 'La': 1.032, 'Ce': 1.01,
    'Pr': 0.99, 'Nd': 0.983, 'Sm': 0.958, 'Eu': 0.947, 'Gd': 0.938, 'Tb': 0.923, 'Dy': 0.912,
    'Ho': 0.901, 'Er': 0.89, 'Tm': 0.88, 'Yb': 0.868, 'Lu': 0.861,
    # X-site (CN=6)
    'F': 1.33, 'Cl': 1.81, 'Br': 1.96, 'I': 2.20, 'O': 1.40, 'S': 1.84
}

# Electronegativity (Pauling scale)
ELECTRONEGATIVITY = {
    'K': 0.82, 'Rb': 0.82, 'Cs': 0.79, 'Ba': 0.89, 'Sr': 0.95, 'Ca': 1.00, 'Na': 0.93, 'Li': 0.98,
    'Ti': 1.54, 'Zr': 1.33, 'Hf': 1.30, 'Sn': 1.96, 'Ge': 2.01, 'Nb': 1.60, 'Ta': 1.50,
    'V': 1.63, 'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Cr': 1.66,
    'Al': 1.61, 'Ga': 1.81, 'In': 1.78, 'Sc': 1.36, 'Y': 1.22, 'La': 1.10, 'Ce': 1.12,
    'Pr': 1.13, 'Nd': 1.14, 'Sm': 1.17, 'Eu': 1.20, 'Gd': 1.20, 'Tb': 1.20, 'Dy': 1.22,
    'Ho': 1.23, 'Er': 1.24, 'Tm': 1.25, 'Yb': 1.10, 'Lu': 1.27,
    'F': 3.98, 'Cl': 3.16, 'Br': 2.96, 'I': 2.66, 'O': 3.44, 'S': 2.58
}

logger = get_logger(__name__)

def parse_formula(formula: str) -> Optional[Dict[str, int]]:
    """
    Parse a chemical formula string into a dictionary of elements and counts.
    Handles simple formulas like 'ABX3' or 'BaTiO3'.
    """
    if not formula or not isinstance(formula, str):
        return None

    # Remove whitespace and convert to uppercase
    formula = formula.strip().upper()

    # Simple regex to match element symbols and their counts
    # Matches element (e.g., Ba, Ti, O) followed by optional number
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula)

    if not matches:
        return None

    result = {}
    for element, count in matches:
        count = int(count) if count else 1
        if element in result:
            result[element] += count
        else:
            result[element] = count

    return result

def get_ionic_radius(element: str, oxidation_state: Optional[int] = None) -> Optional[float]:
    """
    Get the ionic radius for an element.
    Returns None if the element or oxidation state is not found.
    """
    if element not in IONIC_RADII:
        return None
    return IONIC_RADII[element]

def get_element_electronegativity(element: str) -> Optional[float]:
    """
    Get the electronegativity for an element.
    Returns None if the element is not found.
    """
    if element not in ELECTRONEGATIVITY:
        return None
    return ELECTRONEGATIVITY[element]

def determine_oxidation_states(parsed_formula: Dict[str, int]) -> Optional[Dict[str, int]]:
    """
    Determine the oxidation states for elements in a perovskite ABX3 structure.
    Returns None if oxidation states cannot be unambiguously determined.
    """
    if len(parsed_formula) != 3:
        return None

    # Identify A, B, and X sites based on stoichiometry
    # ABX3: A has count 1, B has count 1, X has count 3
    elements = list(parsed_formula.keys())
    counts = list(parsed_formula.values())

    # Find the element with count 3 (X site)
    x_element = None
    a_elements = []
    b_elements = []

    for elem, count in parsed_formula.items():
        if count == 3:
            x_element = elem
        elif count == 1:
            # Need to distinguish A and B
            # A is typically alkali/alkaline earth, B is transition metal
            if elem in COMMON_OXIDATION_STATES['A']:
                a_elements.append(elem)
            elif elem in COMMON_OXIDATION_STATES['B']:
                b_elements.append(elem)
            else:
                # Check if it's in A or B lists
                if elem in COMMON_OXIDATION_STATES.get('A', {}):
                    a_elements.append(elem)
                elif elem in COMMON_OXIDATION_STATES.get('B', {}):
                    b_elements.append(elem)

    if x_element is None or len(a_elements) != 1 or len(b_elements) != 1:
        return None

    a_element = a_elements[0]
    b_element = b_elements[0]

    # Determine oxidation states
    # For perovskite: A is +1 or +2, B is +3, +4, or +5, X is -1 or -2
    # Charge balance: A_ox + B_ox + 3*X_ox = 0

    a_ox_options = COMMON_OXIDATION_STATES.get('A', {}).get(a_element, [])
    b_ox_options = COMMON_OXIDATION_STATES.get('B', {}).get(b_element, [])
    x_ox_options = COMMON_OXIDATION_STATES.get('X', {}).get(x_element, [])

    if not a_ox_options or not b_ox_options or not x_ox_options:
        return None

    # Find valid combination
    for a_ox in a_ox_options:
        for b_ox in b_ox_options:
            for x_ox in x_ox_options:
                if a_ox + b_ox + 3 * x_ox == 0:
                    return {a_element: a_ox, b_element: b_ox, x_element: x_ox}

    return None

def calculate_tolerance_factor(r_a: float, r_b: float, r_x: float) -> float:
    """
    Calculate the Goldschmidt tolerance factor (t).
    t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    """
    if r_b + r_x == 0:
        return float('nan')
    return (r_a + r_x) / (math.sqrt(2) * (r_b + r_x))

def calculate_octahedral_factor(r_b: float, r_x: float) -> float:
    """
    Calculate the octahedral factor (μ).
    μ = r_B / r_X
    """
    if r_x == 0:
        return float('nan')
    return r_b / r_x

def calculate_electronegativity_difference(parsed_formula: Dict[str, int], oxidation_states: Dict[str, int]) -> float:
    """
    Calculate the electronegativity difference between B and X sites.
    """
    # Identify B and X elements
    b_element = None
    x_element = None

    for elem, count in parsed_formula.items():
        if count == 1:
            if elem in oxidation_states and oxidation_states[elem] > 0:
                # Likely B site (higher oxidation state)
                if elem not in ['K', 'Rb', 'Cs', 'Ba', 'Sr', 'Ca', 'Na', 'Li']:
                    b_element = elem
        elif count == 3:
            x_element = elem

    if b_element is None or x_element is None:
        return float('nan')

    chi_b = get_element_electronegativity(b_element)
    chi_x = get_element_electronegativity(x_element)

    if chi_b is None or chi_x is None:
        return float('nan')

    return abs(chi_b - chi_x)

def calculate_ionic_radius_mismatch(parsed_formula: Dict[str, int], oxidation_states: Dict[str, int]) -> float:
    """
    Calculate the ionic radius mismatch between A and B sites.
    """
    # Identify A and B elements
    a_element = None
    b_element = None

    for elem, count in parsed_formula.items():
        if count == 1:
            if elem in oxidation_states:
                ox = oxidation_states[elem]
                if ox <= 2:
                    a_element = elem
                else:
                    b_element = elem

    if a_element is None or b_element is None:
        return float('nan')

    r_a = get_ionic_radius(a_element, oxidation_states.get(a_element))
    r_b = get_ionic_radius(b_element, oxidation_states.get(b_element))

    if r_a is None or r_b is None:
        return float('nan')

    # Simple mismatch metric: |r_A - r_B| / (r_A + r_B)
    if r_a + r_b == 0:
        return float('nan')

    return abs(r_a - r_b) / (r_a + r_b)

def calculate_all_descriptors(formula: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], bool, str]:
    """
    Calculate all descriptors for a given formula.
    Returns: (tolerance_factor, octahedral_factor, ionic_radius_mismatch, electronegativity_diff, is_valid, exclusion_reason)
    """
    parsed = parse_formula(formula)
    if parsed is None:
        return None, None, None, None, False, "Failed to parse formula"

    oxidation_states = determine_oxidation_states(parsed)
    if oxidation_states is None:
        return None, None, None, None, False, "Ambiguous oxidation states"

    # Identify A, B, X elements
    a_element = None
    b_element = None
    x_element = None

    for elem, count in parsed.items():
        if count == 3:
            x_element = elem
        elif count == 1:
            ox = oxidation_states[elem]
            if ox <= 2:
                a_element = elem
            else:
                b_element = elem

    if a_element is None or b_element is None or x_element is None:
        return None, None, None, None, False, "Could not identify A, B, X sites"

    # Get ionic radii
    r_a = get_ionic_radius(a_element, oxidation_states.get(a_element))
    r_b = get_ionic_radius(b_element, oxidation_states.get(b_element))
    r_x = get_ionic_radius(x_element, oxidation_states.get(x_element))

    if r_a is None:
        return None, None, None, None, False, f"Missing ionic radius for A-site element: {a_element}"
    if r_b is None:
        return None, None, None, None, False, f"Missing ionic radius for B-site element: {b_element}"
    if r_x is None:
        return None, None, None, None, False, f"Missing ionic radius for X-site element: {x_element}"

    # Calculate descriptors
    t = calculate_tolerance_factor(r_a, r_b, r_x)
    mu = calculate_octahedral_factor(r_b, r_x)
    mismatch = calculate_ionic_radius_mismatch(parsed, oxidation_states)
    chi_diff = calculate_electronegativity_difference(parsed, oxidation_states)

    return t, mu, mismatch, chi_diff, True, ""

def process_dataframe(df: pd.DataFrame, formula_col: str = 'formula') -> pd.DataFrame:
    """
    Process a dataframe to calculate descriptors for each formula.
    Logs exclusion reasons for invalid formulas.
    """
    results = []
    excluded_count = 0

    for idx, row in df.iterrows():
        formula = row[formula_col]
        t, mu, mismatch, chi_diff, is_valid, reason = calculate_all_descriptors(formula)

        if is_valid:
            results.append({
                'tolerance_factor': t,
                'octahedral_factor': mu,
                'ionic_radius_mismatch': mismatch,
                'electronegativity_diff': chi_diff,
                'excluded': False,
                'exclusion_reason': ''
            })
        else:
            excluded_count += 1
            log_exclusion_reason(reason, formula)
            results.append({
                'tolerance_factor': None,
                'octahedral_factor': None,
                'ionic_radius_mismatch': None,
                'electronegativity_diff': None,
                'excluded': True,
                'exclusion_reason': reason
            })

    results_df = pd.DataFrame(results)
    df_descriptors = pd.concat([df.reset_index(drop=True), results_df], axis=1)

    logger.info(f"Processed {len(df)} formulas. Excluded: {excluded_count}, Valid: {len(df) - excluded_count}")

    return df_descriptors

# Wrapper functions for compatibility with existing code
def get_ionic_radius_wrapper(element: str, oxidation_state: Optional[int] = None) -> Optional[float]:
    return get_ionic_radius(element, oxidation_state)

def get_element_electronegativity_wrapper(element: str) -> Optional[float]:
    return get_element_electronegativity(element)

def calculate_tolerance_factor_wrapper(r_a: float, r_b: float, r_x: float) -> float:
    return calculate_tolerance_factor(r_a, r_b, r_x)

def calculate_octahedral_factor_wrapper(r_b: float, r_x: float) -> float:
    return calculate_octahedral_factor(r_b, r_x)

def calculate_electronegativity_difference_wrapper(parsed_formula: Dict[str, int], oxidation_states: Dict[str, int]) -> float:
    return calculate_electronegativity_difference(parsed_formula, oxidation_states)

def calculate_ionic_radius_mismatch_wrapper(parsed_formula: Dict[str, int], oxidation_states: Dict[str, int]) -> float:
    return calculate_ionic_radius_mismatch(parsed_formula, oxidation_states)