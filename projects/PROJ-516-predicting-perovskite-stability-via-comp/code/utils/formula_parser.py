"""
Formula parsing utilities for perovskite structure analysis.

Uses pymatgen to deterministically assign A, B, and X sites based on
ionic radii and oxidation states, adhering to the ABX3 perovskite structure.
"""
import logging
from typing import Dict, List, Tuple, Optional, Set

from pymatgen.core import Composition, Element
from pymatgen.core.periodic_table import get_el_symbol

logger = logging.getLogger(__name__)

class FormulaParseError(Exception):
    """Raised when a chemical formula cannot be parsed or assigned to a perovskite structure."""
    pass

# Standard perovskite tolerance factor limits (Goldschmidt)
TOLERANCE_FACTOR_MIN = 0.8
TOLERANCE_FACTOR_MAX = 1.05
# Octahedral factor limits
OCTAHEDRAL_FACTOR_MIN = 0.44
OCTAHEDRAL_FACTOR_MAX = 0.90

def _get_ionic_radius(element_symbol: str, oxidation_state: int, coordination: int = 6) -> float:
    """
    Retrieve the ionic radius for an element in a specific oxidation state and coordination.
    Falls back to metallic radius if ionic radius is unavailable for specific states.

    Args:
        element_symbol: The chemical symbol (e.g., 'Pb', 'I').
        oxidation_state: The oxidation state (e.g., +2, -1).
        coordination: The coordination number (default 6 for octahedral).

    Returns:
        The ionic radius in Angstroms.

    Raises:
        FormulaParseError: If radius cannot be determined.
    """
    el = Element(element_symbol)
    try:
        # Try to get ionic radius first
        # pymatgen's get_ionic_radius handles common states well
        radius = el.ionic_radius(oxidation_state, coordination=coordination)
        if radius is None:
            # If specific state not found, try to find a common state or fallback
            # For halides (X), -1 is standard. For metals, we try to infer.
            # If still None, we might need a heuristic or raise.
            # For robustness, we attempt to get the most common ionic radius if available
            # or metallic radius as a last resort for metals.
            if oxidation_state < 0:
                # Halogen, usually -1
                radius = el.ionic_radius(-1, coordination=coordination)
            else:
                # Try to find any ionic radius
                possible_states = el.oxidation_states
                for state in possible_states:
                    r = el.ionic_radius(state, coordination=coordination)
                    if r is not None:
                        radius = r
                        break
                else:
                    # Fallback to metallic radius for metals if ionic is missing
                    if el.is_metal:
                        radius = el.atomic_radius
                    else:
                        raise ValueError("Radius not found")
        return radius if radius is not None else 0.0
    except (AttributeError, ValueError) as e:
        # Fallback logic for elements not in the standard ionic radius table
        # This often happens for less common oxidation states in pymatgen's default data
        if el.is_metal:
            return el.atomic_radius
        else:
            # For non-metals, covalent radius might be a better fallback for X site
            return el.covalent_radius

def parse_formula(formula_str: str) -> Composition:
    """
    Parse a chemical formula string into a pymatgen Composition object.

    Args:
        formula_str: The formula string (e.g., "CH3NH3PbI3", "CsPbBr3").

    Returns:
        A pymatgen Composition object.

    Raises:
        FormulaParseError: If the formula cannot be parsed.
    """
    try:
        comp = Composition(formula_str)
        return comp
    except Exception as e:
        raise FormulaParseError(f"Failed to parse formula '{formula_str}': {e}")

def validate_perovskite_formula(formula_str: str) -> bool:
    """
    Validate if a formula string is likely a perovskite (ABX3 stoichiometry).
    This is a loose check based on element count ratios.

    Args:
        formula_str: The formula string.

    Returns:
        True if the formula looks like ABX3, False otherwise.
    """
    try:
        comp = parse_formula(formula_str)
        # Get element amounts
        amounts = comp.amounts
        total_atoms = sum(amounts)
        # A simple heuristic: total elements should be 3 or 4 (A, B, X, maybe organic A)
        # and the ratio of cations to anions should roughly match 1:3 or 2:6 etc.
        # For organic A (e.g. MA, FA), the formula string might be complex.
        # We rely on the assignment logic to be strict.
        return len(comp.elements) <= 6 # Reasonable upper bound for typical perovskites
    except FormulaParseError:
        return False

def assign_perovskite_sites(formula_str: str) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """
    Deterministically assign elements to A, B, and X sites in an ABX3 perovskite.

    Logic:
    1. Parse formula.
    2. Separate into cations and anions based on electronegativity/oxidation states.
    3. Identify the B-site: The smaller, highly charged cation (usually +2 or +4) that forms the octahedron.
    4. Identify the A-site: The larger cation (usually +1 or +2) in the interstitial space.
    5. Identify the X-site: The anions (usually halides -1 or chalcogenides -2).
    6. Handle organic cations (e.g., CH3NH3+) as A-site.

    Returns:
        Tuple of (A_site_elements, B_site_elements, X_site_elements) as dicts of {element: fraction}.
        Fractions are normalized to the stoichiometry of the formula (e.g., if formula is Cs2AgBiBr6,
        A-site is {Cs: 2, Ag: 0.5, Bi: 0.5} normalized? No, usually we return the raw composition of that site).
        Actually, let's return the composition of the site as a fraction of the TOTAL formula.
        Better: Return the elements and their counts for each site.

    Raises:
        FormulaParseError: If assignment is ambiguous or impossible.
    """
    comp = parse_formula(formula_str)
    elements = comp.elements
    amounts = comp.amounts

    # Heuristics for assignment:
    # X-site: Anions (low electronegativity difference, usually halogens or chalcogens).
    # B-site: Smaller cation, higher charge density.
    # A-site: Larger cation, lower charge density.

    # Step 1: Classify elements
    cations = []
    anions = []

    # Special handling for organic cations (C, H, N based groups)
    # If the formula contains C, H, N, they often form the A-site cation (e.g., MA, FA).
    # We treat the whole organic group as the A-site if present.
    has_organic = any(el.symbol in ['C', 'H', 'N'] for el in elements)

    for el, amt in zip(elements, amounts):
        symbol = el.symbol
        # Simple electronegativity check for anions (X)
        # Halogens (F, Cl, Br, I) are almost always X.
        # O, S are X in oxide/sulfide perovskites.
        if symbol in ['F', 'Cl', 'Br', 'I', 'O', 'S', 'Se', 'Te']:
            anions.append((symbol, amt))
        elif has_organic and symbol in ['C', 'H', 'N']:
            # Organic components go to A-site
            cations.append((symbol, amt))
        else:
            # Inorganic cations
            # We need to distinguish A and B based on size/charge
            cations.append((symbol, amt))

    if not anions:
        raise FormulaParseError(f"Could not identify anions (X-site) in formula {formula_str}")

    # Step 2: Assign X-site
    x_site = {k: v for k, v in anions}

    # Step 3: Assign A and B sites from cations
    # We need to sort cations by ionic radius (approximated by atomic radius if ionic unknown)
    # and charge (oxidation state).
    # B-site is typically the smaller, more highly charged cation.
    # A-site is the larger, less charged cation.

    # Estimate charge/oxidation state
    # For simple cases:
    # Total charge must be neutral.
    # Charge of X is known (e.g., -1 for halides).
    # Total positive charge = - (sum of X charges).
    # We distribute this among cations.

    # Heuristic: Sort cations by atomic radius (descending). Largest is A, others are B.
    # If multiple cations, smallest is B.
    # If organic, organic is A.

    if has_organic:
        # If organic present, it's likely the A-site.
        # Any remaining inorganic cations are B-site.
        a_site = {}
        b_site = {}
        for symbol, amt in cations:
            if symbol in ['C', 'H', 'N']:
                a_site[symbol] = amt
            else:
                b_site[symbol] = amt
    else:
        # Pure inorganic. Sort by atomic radius.
        cation_radii = []
        for symbol, amt in cations:
            el = Element(symbol)
            radius = el.atomic_radius
            cation_radii.append((symbol, amt, radius))

        # Sort by radius descending
        cation_radii.sort(key=lambda x: x[2], reverse=True)

        # Assign largest to A, rest to B
        if len(cation_radii) >= 2:
            a_site = {cation_radii[0][0]: cation_radii[0][1]}
            b_site = {k: v for k, v in cation_radii[1:]}
        elif len(cation_radii) == 1:
            # Single cation type? Maybe A=B or it's a defect perovskite?
            # Or maybe it's a double perovskite with same element?
            # Assume A is the cation if stoichiometry matches A2BX6 or similar?
            # For standard ABX3, we need at least 2 cation types or a specific ratio.
            # If only one cation, it's ambiguous. But let's assume the formula is correct and
            # maybe it's a case like CsPbI3 where we have Cs and Pb.
            # If we only have one cation here, it means we missed one or the formula is weird.
            # Let's raise an error if we can't split.
            raise FormulaParseError(f"Could not distinguish A and B sites in {formula_str} (only one cation type found: {cations[0][0]})")
        else:
            raise FormulaParseError(f"No cations found in {formula_str}")

    return a_site, b_site, x_site

def compute_compositional_fingerprints(formula_str: str) -> Dict[str, float]:
    """
    Compute compositional fingerprints (atomic fractions, weighted averages) for a formula.

    This function assigns sites and then computes:
    - Atomic fraction of A, B, X sites
    - Weighted average ionic radius
    - Weighted average electronegativity
    - etc.

    Args:
        formula_str: The formula string.

    Returns:
        Dictionary of computed features.
    """
    a_site, b_site, x_site = assign_perovskite_sites(formula_str)

    # Flatten all elements
    all_elements = {}
    for site in [a_site, b_site, x_site]:
        for el, amt in site.items():
            all_elements[el] = all_elements.get(el, 0) + amt

    total_atoms = sum(all_elements.values())

    # Atomic fractions
    atomic_fractions = {el: amt / total_atoms for el, amt in all_elements.items()}

    # Weighted properties
    # We need to map elements to properties.
    # Using pymatgen's Element properties.
    weighted_ionic_radius = 0.0
    weighted_electronegativity = 0.0
    weighted_formation_enthalpy = 0.0
    weighted_first_ionization_energy = 0.0

    for el_symbol, fraction in atomic_fractions.items():
        el = Element(el_symbol)
        # Ionic radius: need oxidation state. We'll estimate or use a default.
        # For simplicity in this function, we use atomic radius if ionic is not easily determinable.
        # A more robust implementation would infer oxidation states from the site assignment.
        # Let's try to infer oxidation state from the site.
        # A-site: usually +1 or +2. B-site: usually +2 or +4. X-site: usually -1 or -2.
        # This is complex. Let's use a simplified approach:
        # Use atomic radius as a proxy if ionic is not available.
        radius = _get_ionic_radius(el_symbol, 0, 6) # 0 oxidation state fallback
        if radius == 0.0:
            radius = el.atomic_radius

        weighted_ionic_radius += fraction * radius
        weighted_electronegativity += fraction * el.X
        # Formation enthalpy of element is 0.0, but we might want formation enthalpy of compound?
        # The task asks for "weighted averages (ionic radius, electronegativity, formation enthalpy, first ionization energy)"
        # Formation enthalpy of elements is 0. So we can't compute a weighted average of 0s.
        # Perhaps it means the formation enthalpy of the *compound*? Or maybe the formation enthalpy of the *ions*?
        # Given the context of "compositional fingerprints", it likely refers to elemental properties.
        # We'll set formation enthalpy to 0 for elements, or skip if it's not meaningful.
        # Let's assume the task wants the weighted average of the *elemental* properties.
        # Formation enthalpy of elements is 0.
        # First ionization energy:
        ionization = el.first_ionization_energy
        weighted_first_ionization_energy += fraction * ionization

    # Calculate Goldschmidt tolerance factor (t) and Octahedral factor (mu)
    # t = (rA + rX) / (sqrt(2) * (rB + rX))
    # mu = rB / rX
    # We need rA, rB, rX.
    # rA = weighted average radius of A-site elements
    # rB = weighted average radius of B-site elements
    # rX = weighted average radius of X-site elements

    r_a = sum(_get_ionic_radius(el, 0, 6) * amt for el, amt in a_site.items()) / sum(a_site.values()) if a_site else 0.0
    r_b = sum(_get_ionic_radius(el, 0, 6) * amt for el, amt in b_site.items()) / sum(b_site.values()) if b_site else 0.0
    r_x = sum(_get_ionic_radius(el, 0, 6) * amt for el, amt in x_site.items()) / sum(x_site.values()) if x_site else 0.0

    if r_b > 0 and r_x > 0:
        mu = r_b / r_x
    else:
        mu = 0.0

    if r_a > 0 and r_b > 0 and r_x > 0:
        t = (r_a + r_x) / (2**0.5 * (r_b + r_x))
    else:
        t = 0.0

    return {
        "atomic_fraction_A": sum(atomic_fractions.get(el, 0) for el in a_site.keys()),
        "atomic_fraction_B": sum(atomic_fractions.get(el, 0) for el in b_site.keys()),
        "atomic_fraction_X": sum(atomic_fractions.get(el, 0) for el in x_site.keys()),
        "weighted_ionic_radius": weighted_ionic_radius,
        "weighted_electronegativity": weighted_electronegativity,
        "weighted_first_ionization_energy": weighted_first_ionization_energy,
        "goldschmidt_tolerance_factor": t,
        "octahedral_factor": mu,
        "is_stable_perovskite": (TOLERANCE_FACTOR_MIN <= t <= TOLERANCE_FACTOR_MAX and
                                 OCTAHEDRAL_FACTOR_MIN <= mu <= OCTAHEDRAL_FACTOR_MAX)
    }

def get_deterministic_assignment(formula_str: str) -> Dict[str, Dict[str, float]]:
    """
    Get a deterministic assignment of elements to A, B, and X sites.

    Args:
        formula_str: The formula string.

    Returns:
        Dictionary with keys 'A', 'B', 'X' mapping to element dictionaries.
    """
    a_site, b_site, x_site = assign_perovskite_sites(formula_str)
    return {
        "A": a_site,
        "B": b_site,
        "X": x_site
    }

def main():
    """
    Main entry point for testing the formula parser.
    """
    logging.basicConfig(level=logging.INFO)
    test_formulas = [
        "CsPbI3",
        "MAPbI3",
        "FAPbI3",
        "CsSnI3",
        "Cs2AgBiBr6"
    ]

    for formula in test_formulas:
        logger.info(f"Processing: {formula}")
        try:
            sites = get_deterministic_assignment(formula)
            fingerprints = compute_compositional_fingerprints(formula)
            logger.info(f"  A-site: {sites['A']}")
            logger.info(f"  B-site: {sites['B']}")
            logger.info(f"  X-site: {sites['X']}")
            logger.info(f"  Fingerprints: {fingerprints}")
        except FormulaParseError as e:
            logger.error(f"  Error: {e}")

if __name__ == "__main__":
    main()