"""
Formula Parser Module using pymatgen for deterministic A/B/X site assignment in perovskites.

This module provides functionality to parse chemical formulas and assign elements
to the A, B, and X sites of the perovskite structure (ABX3).
"""

import logging
from typing import Dict, List, Tuple, Optional, Set

from pymatgen.core import Composition, Element
from pymatgen.core.periodic_table import get_el_symbol

logger = logging.getLogger(__name__)


# Standard perovskite cation/anion sets for assignment
# A-site: Large monovalent or divalent cations (12-coordinate)
# B-site: Smaller transition metal cations (6-coordinate)
# X-site: Anions (typically halides or oxygen)

# Common A-site cations (large ionic radius, +1 or +2 charge)
A_SITE_CATIONS: Set[str] = {
    # Monovalent
    "Cs", "Rb", "K", "Na", "Li", "Tl",
    "NH4", "CH3NH3", "HC(NH2)2",  # Organic cations
    # Divalent (for double perovskites or specific cases)
    "Ba", "Sr", "Ca", "Pb", "Sn", "Ge", "Eu", "Yb", "Sm", "Cd", "Mg",
    # Rare earths (less common but possible in specific structures)
    "La", "Ce", "Pr", "Nd", "Gd", "Dy", "Er", "Y",
}

# Common B-site cations (smaller, transition metals, +2, +3, +4)
B_SITE_CATIONS: Set[str] = {
    "Ti", "Zr", "Hf", "V", "Nb", "Ta", "Cr", "Mo", "W", "Mn", "Tc", "Re",
    "Fe", "Ru", "Os", "Co", "Rh", "Ir", "Ni", "Pd", "Pt", "Cu", "Ag", "Au",
    "Zn", "Cd", "Hg", "Al", "Ga", "In", "Tl",
    "Sn", "Pb", "Ge", "Bi", "Sb",
}

# Common X-site anions
X_SITE_ANIONS: Set[str] = {
    "F", "Cl", "Br", "I",  # Halides
    "O",  # Oxide
    "S", "Se", "Te",  # Chalcogenides
    "N",  # Nitride (less common)
}

# Elements that are ambiguous and require context or heuristics
# These might appear in multiple sites depending on the specific perovskite
AMBIGUOUS_ELEMENTS: Set[str] = {
    "H", "C", "N",  # Often part of organic A-site cations
    "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu",  # Can be B-site, sometimes A-site in complex oxides
}

class FormulaParseError(Exception):
    """Exception raised when formula parsing fails."""
    pass


def parse_formula(formula_str: str) -> Composition:
    """
    Parse a chemical formula string into a pymatgen Composition object.

    Args:
        formula_str: Chemical formula string (e.g., "CsPbI3", "CH3NH3PbI3")

    Returns:
        Composition object

    Raises:
        FormulaParseError: If the formula cannot be parsed
    """
    try:
        # Handle organic cation formulas that might not be directly parsable
        # Normalize common organic cation representations
        normalized = formula_str.replace("CH3NH3", "C H6 N")
        normalized = normalized.replace("HC(NH2)2", "C H6 N3")

        composition = Composition(normalized)
        logger.debug(f"Successfully parsed formula: {formula_str} -> {composition}")
        return composition
    except Exception as e:
        raise FormulaParseError(f"Failed to parse formula '{formula_str}': {e}")


def assign_perovskite_sites(composition: Composition) -> Dict[str, Dict[str, float]]:
    """
    Assign elements to A, B, and X sites in a perovskite structure.

    Uses a deterministic algorithm based on:
    1. Known site preferences (A-site cations, B-site cations, X-site anions)
    2. Ionic radius heuristics for ambiguous cases
    3. Stoichiometry constraints (ABX3 ratio)

    Args:
        composition: pymatgen Composition object

    Returns:
        Dictionary with keys 'A', 'B', 'X', each containing a dict of
        element symbol -> fraction (normalized to sum to 1 for that site)

    Raises:
        FormulaParseError: If assignment cannot be determined
    """
    element_dict = composition.element_composition

    # Separate into potential sites
    a_candidates: Dict[str, float] = {}
    b_candidates: Dict[str, float] = {}
    x_candidates: Dict[str, float] = {}
    ambiguous: List[Tuple[str, float]] = []

    for element, amount in element_dict.items():
        symbol = element.symbol
        
        if symbol in A_SITE_CATIONS:
            a_candidates[symbol] = amount
        elif symbol in B_SITE_CATIONS:
            b_candidates[symbol] = amount
        elif symbol in X_SITE_ANIONS:
            x_candidates[symbol] = amount
        elif symbol in AMBIGUOUS_ELEMENTS:
            ambiguous.append((symbol, amount))
        else:
            # For unknown elements, use heuristics based on position in periodic table
            # Large elements (low electronegativity) -> A-site
            # Transition metals -> B-site
            # Non-metals (high electronegativity) -> X-site
            try:
                el = Element(symbol)
                if el.ionic_radius is not None:
                    # Heuristic: very large ionic radius -> A-site
                    if el.ionic_radius > 1.5:  # Angstroms
                        a_candidates[symbol] = amount
                    elif el.is_metal:
                        b_candidates[symbol] = amount
                    else:
                        x_candidates[symbol] = amount
                else:
                    # Default to B-site for metals, X-site for non-metals
                    if el.is_metal:
                        b_candidates[symbol] = amount
                    else:
                        x_candidates[symbol] = amount
            except Exception:
                # If we can't determine, add to ambiguous
                ambiguous.append((symbol, amount))

    # Handle ambiguous elements using stoichiometry and charge balance
    if ambiguous:
        total_amount = sum(amount for _, amount in ambiguous)
        # Try to distribute based on typical perovskite stoichiometry
        # ABX3: A:B:X should be roughly 1:1:3
        
        current_a = sum(a_candidates.values())
        current_b = sum(b_candidates.values())
        current_x = sum(x_candidates.values())
        
        # Distribute ambiguous elements to balance stoichiometry
        for symbol, amount in ambiguous:
            try:
                el = Element(symbol)
                # Use ionic radius as primary heuristic
                if el.ionic_radius is not None and el.ionic_radius > 1.5:
                    a_candidates[symbol] = amount
                elif el.is_metal:
                    b_candidates[symbol] = amount
                else:
                    x_candidates[symbol] = amount
            except Exception:
                # Default to B-site for metals, X-site for non-metals
                if Element(symbol).is_metal:
                    b_candidates[symbol] = amount
                else:
                    x_candidates[symbol] = amount

    # Normalize each site to sum to 1
    def normalize_site(site_dict: Dict[str, float]) -> Dict[str, float]:
        total = sum(site_dict.values())
        if total == 0:
            return {}
        return {elem: amount / total for elem, amount in site_dict.items()}

    return {
        'A': normalize_site(a_candidates),
        'B': normalize_site(b_candidates),
        'X': normalize_site(x_candidates)
    }


def compute_compositional_fingerprints(formula_str: str) -> Dict:
    """
    Compute compositional fingerprints for a perovskite formula.

    This includes:
    - Atomic fractions for A, B, X sites
    - Weighted averages of elemental properties
    - Variance metrics for multi-element sites

    Args:
        formula_str: Chemical formula string

    Returns:
        Dictionary containing compositional fingerprints
    """
    composition = parse_formula(formula_str)
    site_assignments = assign_perovskite_sites(composition)
    
    fingerprints = {
        'formula': formula_str,
        'site_assignments': site_assignments,
        'atomic_fractions': {},
        'weighted_properties': {},
        'variance_metrics': {}
    }

    # Compute atomic fractions for each site
    for site, elements in site_assignments.items():
        fingerprints['atomic_fractions'][site] = elements

    # Compute weighted average properties for each site
    # Properties: ionic radius, electronegativity, atomic mass
    property_weights = {
        'ionic_radius': {},
        'electronegativity': {},
        'atomic_mass': {}
    }

    for site, elements in site_assignments.items():
        for prop in property_weights.keys():
            weighted_sum = 0.0
            total_fraction = sum(elements.values())
            
            if total_fraction == 0:
                continue
                
            for elem_symbol, fraction in elements.items():
                try:
                    el = Element(elem_symbol)
                    if prop == 'ionic_radius':
                        # Use Shannon-Prewitt ionic radii (6-coordinate for B, 12 for A)
                        # Default to a reasonable value if not available
                        radius = el.ionic_radius or 1.0
                        weighted_sum += radius * fraction
                    elif prop == 'electronegativity':
                        weighted_sum += el.X * fraction
                    elif prop == 'atomic_mass':
                        weighted_sum += el.atomic_mass * fraction
                except Exception as e:
                    logger.warning(f"Could not get {prop} for {elem_symbol}: {e}")
            
            if total_fraction > 0:
                property_weights[prop][site] = weighted_sum / total_fraction

    fingerprints['weighted_properties'] = property_weights

    # Compute variance metrics for multi-element sites
    for site, elements in site_assignments.items():
        if len(elements) > 1:
            # Variance in ionic radius
            radii = []
            fractions = []
            for elem_symbol, fraction in elements.items():
                try:
                    el = Element(elem_symbol)
                    radii.append(el.ionic_radius or 1.0)
                    fractions.append(fraction)
                except Exception:
                    pass
            
            if radii:
                mean_radius = sum(r * f for r, f in zip(radii, fractions)) / sum(fractions)
                variance = sum(f * (r - mean_radius)**2 for r, f in zip(radii, fractions)) / sum(fractions)
                fingerprints['variance_metrics'][f'{site}_radius_variance'] = variance

    return fingerprints


def validate_perovskite_formula(formula_str: str) -> Tuple[bool, str]:
    """
    Validate if a formula can represent a perovskite structure.

    Checks:
    - Contains elements that can form A, B, and X sites
    - Reasonable stoichiometry (approximately ABX3)
    - Charge balance (simplified check)

    Args:
        formula_str: Chemical formula string

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        composition = parse_formula(formula_str)
        site_assignments = assign_perovskite_sites(composition)
        
        # Check if all three sites have elements
        if not site_assignments['A'] or not site_assignments['B'] or not site_assignments['X']:
            return False, "Formula missing elements for one or more perovskite sites (A, B, or X)"
        
        # Check stoichiometry ratio (approximately 1:1:3)
        a_total = sum(site_assignments['A'].values())
        b_total = sum(site_assignments['B'].values())
        x_total = sum(site_assignments['X'].values())
        
        if a_total == 0 or b_total == 0 or x_total == 0:
            return False, "Invalid site totals"
        
        # Normalize to B-site = 1
        a_ratio = a_total / b_total
        x_ratio = x_total / b_total
        
        # Allow some flexibility in stoichiometry (0.8-1.2 for A:B, 2.5-3.5 for X:B)
        if not (0.8 <= a_ratio <= 1.2):
            return False, f"A:B ratio {a_ratio:.2f} outside acceptable range (0.8-1.2)"
        
        if not (2.5 <= x_ratio <= 3.5):
            return False, f"X:B ratio {x_ratio:.2f} outside acceptable range (2.5-3.5)"
        
        return True, "Valid perovskite formula"
        
    except FormulaParseError as e:
        return False, f"Formula parsing error: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"


def get_deterministic_assignment(formula_str: str) -> Dict[str, Dict[str, float]]:
    """
    Get a deterministic assignment of elements to perovskite sites.
    
    This is the main entry point for the formula parser, providing a consistent
    assignment algorithm that can be used for feature engineering.
    
    Args:
        formula_str: Chemical formula string
        
    Returns:
        Dictionary with site assignments (A, B, X) and element fractions
    """
    return assign_perovskite_sites(parse_formula(formula_str))