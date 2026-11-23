"""
Formula parser using pymatgen for deterministic A/B/X site assignment in perovskites.

This module provides functions to parse chemical formulas, validate perovskite structures,
assign A/B/X sites deterministically, and compute compositional fingerprints.
"""

import logging
from typing import Dict, List, Tuple, Optional, Set

from pymatgen.core import Composition, Element
from pymatgen.core.periodic_table import Element as PmgElement

logger = logging.getLogger(__name__)

class FormulaParseError(Exception):
    """Exception raised for formula parsing errors."""
    pass

# Standard perovskite oxidation states for site assignment
# Based on common perovskite chemistry (ABX3)
STANDARD_OXIDATION_STATES = {
    # A-site cations (typically +1)
    'Li': 1, 'Na': 1, 'K': 1, 'Rb': 1, 'Cs': 1, 'Fr': 1,
    'Tl': 1, 'Ag': 1, 'Cu': 1, 'Au': 1,
    'NH4': 1, 'CH3NH3': 1, 'HC(NH2)2': 1, 'C6H5NH3': 1,
    # B-site cations (typically +2 or +4)
    'Pb': 2, 'Sn': 2, 'Ge': 2, 'Ti': 4, 'Zr': 4, 'Hf': 4,
    'Mn': 2, 'Fe': 2, 'Co': 2, 'Ni': 2, 'Cu': 2, 'Zn': 2,
    'Cd': 2, 'Hg': 2, 'Mg': 2, 'Ca': 2, 'Sr': 2, 'Ba': 2,
    'V': 4, 'Nb': 4, 'Ta': 4, 'Cr': 3, 'Mo': 4, 'W': 4,
    # X-site anions (typically -1 or -2)
    'F': -1, 'Cl': -1, 'Br': -1, 'I': -1,
    'O': -2, 'S': -2, 'Se': -2, 'Te': -2,
    'N': -3, 'C': -4, 'H': 1, 'OH': -1
}

# Common perovskite families and their characteristic elements
PEROVSKITE_FAMILIES = {
    'lead-halide': {'Pb', 'Cl', 'Br', 'I', 'F'},
    'tin-halide': {'Sn', 'Cl', 'Br', 'I', 'F'},
    'germanium-halide': {'Ge', 'Cl', 'Br', 'I', 'F'},
    'oxide': {'O'},
    'double': {'Bi', 'Sb', 'Ag', 'Cu', 'Na', 'K'}
}

def parse_formula(formula_str: str) -> Composition:
    """
    Parse a chemical formula string into a pymatgen Composition.
    
    Args:
        formula_str: Chemical formula string (e.g., "CsPbI3", "CH3NH3PbBr3")
    
    Returns:
        Composition object from pymatgen
    
    Raises:
        FormulaParseError: If the formula cannot be parsed
    """
    try:
        # Handle organic-inorganic hybrid formulas
        # Replace common organic cations with placeholders for parsing
        formula_str = formula_str.strip()
        
        # Try direct parsing first
        composition = Composition(formula_str)
        return composition
    except Exception as e:
        logger.error(f"Failed to parse formula '{formula_str}': {e}")
        raise FormulaParseError(f"Cannot parse formula: {formula_str}") from e

def validate_perovskite_formula(composition: Composition) -> bool:
    """
    Validate if a composition could represent a perovskite structure.
    
    A perovskite generally follows ABX3 stoichiometry, where:
    - A is a large monovalent cation
    - B is a smaller multivalent cation
    - X is an anion (halide or oxide)
    
    Args:
        composition: Pymatgen Composition object
    
    Returns:
        True if the composition is consistent with perovskite stoichiometry
    """
    if composition is None or len(composition) == 0:
        return False
    
    # Get elemental composition
    elemental_dict = composition.get_el_amt_dict()
    
    # Check if it has at least 3 different elements (A, B, X)
    if len(elemental_dict) < 3:
        return False
    
    # Check total stoichiometry (should be roughly ABX3 = 5 atoms minimum)
    total_atoms = sum(elemental_dict.values())
    if total_atoms < 5:
        return False
    
    return True

def assign_perovskite_sites(composition: Composition) -> Dict[str, List[str]]:
    """
    Deterministically assign elements to A, B, and X sites based on chemical rules.
    
    Assignment rules:
    1. X-site (anions): Halogens (F, Cl, Br, I) and O, S, Se, Te
    2. A-site: Large monovalent cations (alkali metals, organic cations)
    3. B-site: Remaining cations (typically transition metals, post-transition metals)
    
    Args:
        composition: Pymatgen Composition object
    
    Returns:
        Dictionary with keys 'A', 'B', 'X' containing lists of element symbols
    
    Raises:
        FormulaParseError: If site assignment cannot be determined
    """
    elemental_dict = composition.get_el_amt_dict()
    
    a_sites = []
    b_sites = []
    x_sites = []
    
    # X-site anions (halogens and chalcogens)
    anions = {'F', 'Cl', 'Br', 'I', 'O', 'S', 'Se', 'Te', 'N', 'C'}
    
    # A-site candidates (large monovalent cations)
    a_candidates = {
        'Li', 'Na', 'K', 'Rb', 'Cs', 'Fr',  # Alkali metals
        'Tl', 'Ag', 'Cu', 'Au',  # Monovalent metals
        'NH4', 'CH3NH3', 'HC(NH2)2', 'C6H5NH3'  # Organic cations
    }
    
    for element_str, amount in elemental_dict.items():
        element = element_str
        
        # Skip organic cation placeholders if they exist
        if element in ['NH4', 'CH3NH3', 'HC(NH2)2', 'C6H5NH3']:
            a_sites.append(element)
            continue
        
        # Check if it's an anion (X-site)
        if element in anions:
            x_sites.append(element)
        # Check if it's a known A-site candidate
        elif element in a_candidates:
            a_sites.append(element)
        # Otherwise, assume B-site
        else:
            # Verify it's a metal/cation
            try:
                elem_obj = PmgElement(element)
                if elem_obj.is_metal or elem_obj.is_metalloid:
                    b_sites.append(element)
                else:
                    # Non-metals that aren't anions go to X-site
                    if element not in anions:
                        x_sites.append(element)
            except ValueError:
                # Unknown element, default to B-site for metals
                b_sites.append(element)
    
    # Validate assignment
    if not x_sites:
        raise FormulaParseError("Could not identify X-site anions in formula")
    
    if not (a_sites or b_sites):
        raise FormulaParseError("Could not identify A or B site cations in formula")
    
    return {
        'A': a_sites if a_sites else [],
        'B': b_sites if b_sites else [],
        'X': x_sites
    }

def compute_compositional_fingerprints(composition: Composition, 
                                      sites: Optional[Dict[str, List[str]]] = None) -> Dict[str, float]:
    """
    Compute compositional fingerprints (descriptors) for the perovskite.
    
    Computes:
    - Atomic fractions for each site
    - Weighted average properties (ionic radius, electronegativity, etc.)
    - Variance metrics for compositional heterogeneity
    
    Args:
        composition: Pymatgen Composition object
        sites: Optional pre-computed site assignment. If None, will be computed.
    
    Returns:
        Dictionary of compositional fingerprints
    """
    if sites is None:
        sites = assign_perovskite_sites(composition)
    
    elemental_dict = composition.get_el_amt_dict()
    total_atoms = sum(elemental_dict.values())
    
    fingerprints = {}
    
    # Atomic fractions for each site
    for site in ['A', 'B', 'X']:
        site_elements = sites.get(site, [])
        site_total = sum(elemental_dict.get(el, 0) for el in site_elements)
        if site_total > 0:
            fingerprints[f'atomic_fraction_{site}'] = site_total / total_atoms
            fingerprints[f'num_elements_{site}'] = len(site_elements)
        else:
            fingerprints[f'atomic_fraction_{site}'] = 0.0
            fingerprints[f'num_elements_{site}'] = 0
    
    # Compute weighted average properties
    properties_to_compute = [
        ('ionic_radius', get_ionic_radius),
        ('electronegativity', get_electronegativity),
        ('atomic_number', get_atomic_number),
        ('atomic_mass', get_atomic_mass)
    ]
    
    for prop_name, getter in properties_to_compute:
        weighted_sum = 0.0
        variance_sum = 0.0
        count = 0
        
        for element_str, amount in elemental_dict.items():
            try:
                value = getter(element_str)
                weight = amount / total_atoms
                weighted_sum += value * weight
                variance_sum += (value ** 2) * weight
                count += 1
            except (ValueError, KeyError):
                continue
        
        if count > 0:
            fingerprints[f'weighted_{prop_name}'] = weighted_sum
            fingerprints[f'variance_{prop_name}'] = max(0, variance_sum - weighted_sum ** 2)
    
    return fingerprints

def get_ionic_radius(element_str: str) -> float:
    """
    Get ionic radius for an element (in Angstroms).
    
    Uses typical oxidation states for perovskite chemistry.
    
    Args:
        element_str: Element symbol
    
    Returns:
        Ionic radius in Angstroms
    
    Raises:
        ValueError: If ionic radius is not available
    """
    # Typical ionic radii for common perovskite elements (coordination number 6)
    # Source: Shannon radii
    ionic_radii = {
        # A-site cations
        'Li': 0.76, 'Na': 1.02, 'K': 1.38, 'Rb': 1.52, 'Cs': 1.67,
        'Tl': 1.50, 'Ag': 1.15, 'Cu': 0.77,
        # B-site cations
        'Pb': 1.19, 'Sn': 1.18, 'Ge': 0.73, 'Ti': 0.605, 'Zr': 0.72, 'Hf': 0.71,
        'Mn': 0.83, 'Fe': 0.785, 'Co': 0.745, 'Ni': 0.69, 'Cu': 0.73, 'Zn': 0.74,
        'Cd': 0.95, 'Mg': 0.72, 'Ca': 1.00, 'Sr': 1.18, 'Ba': 1.35,
        'V': 0.58, 'Nb': 0.64, 'Ta': 0.64, 'Cr': 0.615, 'Mo': 0.65, 'W': 0.60,
        'Bi': 1.03, 'Sb': 0.76, 'Ag': 1.15,
        # X-site anions
        'F': 1.33, 'Cl': 1.81, 'Br': 1.96, 'I': 2.20,
        'O': 1.40, 'S': 1.84, 'Se': 1.98, 'Te': 2.21
    }
    
    if element_str in ionic_radii:
        return ionic_radii[element_str]
    
    raise ValueError(f"Ionic radius not available for {element_str}")

def get_electronegativity(element_str: str) -> float:
    """
    Get electronegativity (Pauling scale) for an element.
    
    Args:
        element_str: Element symbol
    
    Returns:
        Electronegativity value
    
    Raises:
        ValueError: If electronegativity is not available
    """
    electronegativities = {
        'Li': 0.98, 'Na': 0.93, 'K': 0.82, 'Rb': 0.82, 'Cs': 0.79,
        'Tl': 1.62, 'Ag': 1.93, 'Cu': 1.90, 'Au': 2.54,
        'Pb': 1.87, 'Sn': 1.96, 'Ge': 2.01, 'Ti': 1.54, 'Zr': 1.33, 'Hf': 1.30,
        'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Zn': 1.65,
        'Cd': 1.69, 'Mg': 1.31, 'Ca': 1.00, 'Sr': 0.95, 'Ba': 0.89,
        'V': 1.63, 'Nb': 1.60, 'Ta': 1.50, 'Cr': 1.66, 'Mo': 2.16, 'W': 2.36,
        'Bi': 2.02, 'Sb': 2.05, 'Ag': 1.93,
        'F': 3.98, 'Cl': 3.16, 'Br': 2.96, 'I': 2.66,
        'O': 3.44, 'S': 2.58, 'Se': 2.55, 'Te': 2.10,
        'N': 3.04, 'C': 2.55, 'H': 2.20
    }
    
    if element_str in electronegativities:
        return electronegativities[element_str]
    
    try:
        elem_obj = PmgElement(element_str)
        return elem_obj.X
    except ValueError:
        raise ValueError(f"Electronegativity not available for {element_str}")

def get_atomic_number(element_str: str) -> int:
    """
    Get atomic number for an element.
    
    Args:
        element_str: Element symbol
    
    Returns:
        Atomic number
    
    Raises:
        ValueError: If element is not found
    """
    try:
        elem_obj = PmgElement(element_str)
        return elem_obj.Z
    except ValueError:
        raise ValueError(f"Unknown element: {element_str}")

def get_atomic_mass(element_str: str) -> float:
    """
    Get atomic mass for an element (in amu).
    
    Args:
        element_str: Element symbol
    
    Returns:
        Atomic mass
    
    Raises:
        ValueError: If element is not found
    """
    try:
        elem_obj = PmgElement(element_str)
        return elem_obj.atomic_mass
    except ValueError:
        raise ValueError(f"Unknown element: {element_str}")

def get_deterministic_assignment(formula_str: str) -> Dict[str, any]:
    """
    Perform complete deterministic site assignment and fingerprint computation.
    
    Args:
        formula_str: Chemical formula string
    
    Returns:
        Dictionary containing:
        - 'composition': Parsed Composition object
        - 'sites': Site assignment (A, B, X lists)
        - 'fingerprints': Compositional fingerprints
        - 'valid': Whether the formula is a valid perovskite
    """
    composition = parse_formula(formula_str)
    valid = validate_perovskite_formula(composition)
    sites = assign_perovskite_sites(composition) if valid else {}
    fingerprints = compute_compositional_fingerprints(composition, sites) if valid else {}
    
    return {
        'composition': composition,
        'sites': sites,
        'fingerprints': fingerprints,
        'valid': valid
    }

def main():
    """
    Main function for testing the formula parser.
    """
    test_formulas = [
        "CsPbI3",
        "CH3NH3PbBr3",
        "FAPbI3",
        "CsSnI3",
        "BaTiO3",
        "NaNbO3"
    ]
    
    logger.info("Testing formula parser with sample perovskites:")
    for formula in test_formulas:
        try:
            result = get_deterministic_assignment(formula)
            logger.info(f"\nFormula: {formula}")
            logger.info(f"  Valid perovskite: {result['valid']}")
            logger.info(f"  Sites: A={result['sites'].get('A', [])}, "
                      f"B={result['sites'].get('B', [])}, "
                      f"X={result['sites'].get('X', [])}")
            logger.info(f"  Fingerprints: {result['fingerprints']}")
        except FormulaParseError as e:
            logger.error(f"Failed to parse {formula}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()