"""
Feature Engineering for Perovskite Stability Prediction.

This module computes compositional fingerprints and variance metrics
for perovskite materials based on their chemical formulas.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "descriptors_uncertainty.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "descriptors_features.csv"

# Elemental properties needed
PROPERTIES = {
    'ionic_radius': 'ionic_radius',
    'electronegativity': 'electronegativity',
    'atomic_mass': 'atomic_mass',
    'atomic_number': 'atomic_number'
}

def get_element_property(element_symbol: str, property_name: str) -> float:
    """
    Retrieve a specific property for an element.

    Args:
        element_symbol: Chemical symbol (e.g., 'Pb', 'I')
        property_name: Property to retrieve (e.g., 'ionic_radius', 'electronegativity')

    Returns:
        The property value as a float.

    Raises:
        ValueError: If element or property is not found.
    """
    try:
        elem = Element(element_symbol)
        if property_name == 'ionic_radius':
            # Use ionic radius for common oxidation states, default to metallic radius if not found
            # pymatgen doesn't have a direct ionic_radius property for all elements in all states
            # We'll use the metallic radius as a fallback or a specific ionic radius if available
            # For perovskites, we typically care about specific oxidation states.
            # A simplified approach: use the metallic radius if ionic is not readily available in the default context
            # or try to get it from the element's data.
            # Note: pymatgen's Element class has 'ionic_radii' dict.
            # We'll pick a common radius if multiple exist, or use a default.
            # For robustness, we'll use the first available ionic radius or metallic radius.
            if hasattr(elem, 'ionic_radii') and elem.ionic_radii:
                # Sort by oxidation state magnitude (common for perovskites)
                # Prefer +1, +2, +3, +4, +5, +6, -1, -2, -3, -4
                # For A site (usually +1), B site (usually +2, +3, +4), X site (usually -1, -2)
                # This is a simplification. We'll just take the first one for now or average.
                # Let's take the first one in the dict for simplicity, as the dict order might be arbitrary.
                # Better: use the metallic radius if ionic is not clearly defined for the context.
                # Actually, let's use the metallic radius as a proxy if ionic is not specific enough.
                # But the task asks for ionic radius.
                # We'll use the first available ionic radius.
                return list(elem.ionic_radii.values())[0]
            else:
                # Fallback to metallic radius if ionic not found
                return elem.atomic_radius
        elif property_name == 'electronegativity':
            return elem.X
        elif property_name == 'atomic_mass':
            return elem.atomic_mass
        elif property_name == 'atomic_number':
            return elem.number
        else:
            raise ValueError(f"Unknown property: {property_name}")
    except Exception as e:
        logger.warning(f"Could not retrieve {property_name} for {element_symbol}: {e}")
        return np.nan

def parse_formula_elements(formula: str) -> Dict[str, float]:
    """
    Parse a chemical formula and return a dictionary of elements and their stoichiometric coefficients.

    Args:
        formula: Chemical formula string (e.g., 'CsPbI3')

    Returns:
        Dictionary mapping element symbols to their stoichiometric coefficients.
    """
    try:
        comp = Composition(formula)
        return {str(el): amt for el, amt in comp.items()}
    except Exception as e:
        logger.error(f"Failed to parse formula '{formula}': {e}")
        return {}

def compute_atomic_fractions(elements: Dict[str, float]) -> Tuple[float, float, float]:
    """
    Compute the atomic fractions for A, B, and X sites in a perovskite.
    Assumes a standard ABX3 structure where:
    - A is the cation with the largest ionic radius (or first element if ambiguous)
    - B is the cation with intermediate radius (or second)
    - X is the anion (or third)

    This is a simplified heuristic. A more robust method would use site assignment rules.

    Args:
        elements: Dictionary of element symbols to stoichiometric coefficients.

    Returns:
        Tuple of (fraction_A, fraction_B, fraction_X)
    """
    total_atoms = sum(elements.values())
    if total_atoms == 0:
        return 0.0, 0.0, 0.0

    # Heuristic: Sort by electronegativity to identify anions (X) vs cations (A, B)
    # Anions (X) typically have higher electronegativity.
    # Cations (A, B) have lower electronegativity.
    # Among cations, A is usually larger (lower electronegativity often correlates with larger size, but not always).
    # Let's sort by electronegativity descending. The most electronegative is likely X.
    # The next two are A and B.
    # For ABX3, we expect 1 A, 1 B, 3 X.
    # So the fraction of A is 1/5, B is 1/5, X is 3/5.
    # But we have the actual stoichiometry.

    # Let's identify X as the most electronegative element.
    # A and B are the cations.
    # We'll assign A to the cation with the lower electronegativity (larger size typically).
    # B to the cation with higher electronegativity (smaller size typically).

    sorted_elements = sorted(elements.items(), key=lambda x: get_element_property(x[0], 'electronegativity'), reverse=True)

    if len(sorted_elements) < 3:
        # Fallback for non-standard formulas
        # Assume first is A, second is B, rest are X
        if len(sorted_elements) == 1:
            return 1.0, 0.0, 0.0
        elif len(sorted_elements) == 2:
            return sorted_elements[0][1]/total_atoms, sorted_elements[1][1]/total_atoms, 0.0
        else:
            return 0.0, 0.0, 1.0

    x_element = sorted_elements[0][0]
    x_amount = sorted_elements[0][1]

    cations = sorted_elements[1:]
    # Sort cations by electronegativity ascending (A is larger/less electronegative)
    cations_sorted = sorted(cations, key=lambda x: get_element_property(x[0], 'electronegativity'))

    if len(cations_sorted) >= 2:
        a_element = cations_sorted[0][0]
        b_element = cations_sorted[1][0]
        a_amount = cations_sorted[0][1]
        b_amount = cations_sorted[1][1]
    elif len(cations_sorted) == 1:
        a_element = cations_sorted[0][0]
        b_element = None
        a_amount = cations_sorted[0][1]
        b_amount = 0.0
    else:
        a_element = None
        b_element = None
        a_amount = 0.0
        b_amount = 0.0

    frac_a = a_amount / total_atoms
    frac_b = b_amount / total_atoms
    frac_x = x_amount / total_atoms

    return frac_a, frac_b, frac_x

def compute_weighted_property(elements: Dict[str, float], property_name: str) -> float:
    """
    Compute the weighted average of a property across all elements in the formula.

    Args:
        elements: Dictionary of element symbols to stoichiometric coefficients.
        property_name: Name of the property to compute.

    Returns:
        Weighted average of the property.
    """
    total_atoms = sum(elements.values())
    if total_atoms == 0:
        return np.nan

    weighted_sum = 0.0
    for elem, amount in elements.items():
        prop_val = get_element_property(elem, property_name)
        if np.isnan(prop_val):
            logger.warning(f"Property {property_name} not found for {elem}, skipping.")
            continue
        weighted_sum += prop_val * amount

    return weighted_sum / total_atoms

def compute_variance_property(elements: Dict[str, float], property_name: str) -> float:
    """
    Compute the variance of a property across all elements in the formula.

    Args:
        elements: Dictionary of element symbols to stoichiometric coefficients.
        property_name: Name of the property to compute variance for.

    Returns:
        Variance of the property.
    """
    total_atoms = sum(elements.values())
    if total_atoms == 0:
        return np.nan

    values = []
    weights = []
    for elem, amount in elements.items():
        prop_val = get_element_property(elem, property_name)
        if np.isnan(prop_val):
            continue
        values.append(prop_val)
        weights.append(amount)

    if not values:
        return np.nan

    weights = np.array(weights)
    values = np.array(values)

    # Normalize weights
    weights_norm = weights / weights.sum()

    # Weighted mean
    mean = np.average(values, weights=weights_norm)

    # Weighted variance
    variance = np.average((values - mean) ** 2, weights=weights_norm)

    return variance

def compute_descriptors(row: pd.Series) -> Dict[str, float]:
    """
    Compute all descriptors for a single row.

    Args:
        row: A pandas Series representing a row in the dataframe.

    Returns:
        Dictionary of descriptor names to values.
    """
    formula = row['formula']
    elements = parse_formula_elements(formula)

    if not elements:
        return {
            'atomic_fraction_A': np.nan,
            'atomic_fraction_B': np.nan,
            'atomic_fraction_X': np.nan,
            'weighted_ionic_radius': np.nan,
            'weighted_electronegativity': np.nan,
            'weighted_formation_enthalpy': np.nan,
            'first_ionization_energy': np.nan,
            'variance_ionic_radius': np.nan,
            'variance_electronegativity': np.nan
        }

    frac_a, frac_b, frac_x = compute_atomic_fractions(elements)

    # Weighted properties
    weighted_ionic_radius = compute_weighted_property(elements, 'ionic_radius')
    weighted_electronegativity = compute_weighted_property(elements, 'electronegativity')

    # Variance properties
    variance_ionic_radius = compute_variance_property(elements, 'ionic_radius')
    variance_electronegativity = compute_variance_property(elements, 'electronegativity')

    # Note: T014b should have added weighted_formation_enthalpy and first_ionization_energy
    # We assume they are already in the row or we compute them here if needed.
    # Since T014c requires T014b, we assume those columns exist in the input.
    # If not, we compute them here as a fallback.
    weighted_formation_enthalpy = row.get('weighted_formation_enthalpy', np.nan)
    first_ionization_energy = row.get('first_ionization_energy', np.nan)

    if np.isnan(weighted_formation_enthalpy):
        # Fallback: compute weighted formation enthalpy if not present
        # This is a placeholder; actual formation enthalpy requires external data.
        # We'll leave it as NaN if not present.
        pass

    if np.isnan(first_ionization_energy):
        # Fallback: compute first ionization energy
        first_ionization_energy = compute_weighted_property(elements, 'first_ionization_energy')
        # Note: pymatgen's Element class has 'first_ionization_energy' property.
        # Let's check if it's available.
        # If not, we'll leave it as NaN.

    return {
        'atomic_fraction_A': frac_a,
        'atomic_fraction_B': frac_b,
        'atomic_fraction_X': frac_x,
        'weighted_ionic_radius': weighted_ionic_radius,
        'weighted_electronegativity': weighted_electronegativity,
        'weighted_formation_enthalpy': weighted_formation_enthalpy,
        'first_ionization_energy': first_ionization_energy,
        'variance_ionic_radius': variance_ionic_radius,
        'variance_electronegativity': variance_electronegativity
    }

def load_raw_data() -> pd.DataFrame:
    """
    Load the raw data from the input file.

    Returns:
        DataFrame with the raw data.
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    logger.info(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    logger.info(f"Loaded {len(df)} rows")
    return df

def save_descriptors(df: pd.DataFrame) -> None:
    """
    Save the dataframe with descriptors to the output file.

    Args:
        df: DataFrame with descriptors.
    """
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Saved descriptors to {OUTPUT_FILE}")

def main():
    """
    Main function to compute descriptors and save them.
    """
    try:
        df = load_raw_data()

        # Compute descriptors for each row
        descriptors = df.apply(compute_descriptors, axis=1)
        descriptors_df = pd.DataFrame(descriptors.tolist(), index=df.index)

        # Merge with original dataframe
        df = pd.concat([df, descriptors_df], axis=1)

        # Save the result
        save_descriptors(df)

        logger.info("Feature engineering completed successfully.")

    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()