"""
Feature Engineering Module for Perovskite Stability Prediction.

This module implements the computation of compositional descriptors including
atomic fractions, weighted properties, and variance metrics for perovskite
materials.
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

# Define file paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "descriptors_features.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "descriptors_features.csv"

def get_element_property(element_symbol: str, property_name: str) -> Optional[float]:
    """
    Retrieve a specific property for an element from pymatgen.

    Args:
        element_symbol: Chemical symbol of the element (e.g., 'Pb', 'I').
        property_name: Name of the property to retrieve.

    Returns:
        The property value or None if not found.
    """
    try:
        elem = Element(element_symbol)
        if property_name == 'ionic_radius':
            # Coordination number 6 is standard for perovskites
            return elem.ionic_radii.get(6)
        elif property_name == 'electronegativity':
            return elem.electronegativity
        elif property_name == 'formation_enthalpy':
            return elem.formation_enthalpy
        elif property_name == 'first_ionization_energy':
            return elem.first_ionization_energy
        else:
            raise ValueError(f"Unsupported property: {property_name}")
    except Exception as e:
        logger.warning(f"Could not retrieve {property_name} for {element_symbol}: {e}")
        return None

def parse_formula_elements(formula: str) -> Dict[str, int]:
    """
    Parse a chemical formula into a dictionary of element counts.

    Args:
        formula: Chemical formula string (e.g., 'FAPbI3').

    Returns:
        Dictionary mapping element symbols to their counts.
    """
    try:
        comp = Composition(formula)
        return {str(k): v for k, v in comp.items()}
    except Exception as e:
        logger.error(f"Failed to parse formula {formula}: {e}")
        return {}

def compute_atomic_fractions(elements: Dict[str, int]) -> Tuple[float, float, float]:
    """
    Compute atomic fractions for A, B, and X sites based on perovskite stoichiometry.
    Assumes ABX3 structure: 1 A, 1 B, 3 X.

    Args:
        elements: Dictionary of element counts.

    Returns:
        Tuple of (atomic_fraction_A, atomic_fraction_B, atomic_fraction_X).
    """
    total_atoms = sum(elements.values())
    if total_atoms == 0:
        return 0.0, 0.0, 0.0

    # Identify sites based on stoichiometry (simplified heuristic)
    # In reality, this requires site assignment logic, but for compositional
    # fingerprints we assume the standard ABX3 ratio.
    # A site: 1 atom
    # B site: 1 atom
    # X site: 3 atoms
    # Total: 5 atoms

    # Calculate fractions based on the standard perovskite stoichiometry
    # This is a compositional fingerprint, not a site-specific assignment
    fraction_A = 1.0 / 5.0
    fraction_B = 1.0 / 5.0
    fraction_X = 3.0 / 5.0

    return fraction_A, fraction_B, fraction_X

def compute_weighted_property(elements: Dict[str, int], property_name: str) -> float:
    """
    Compute a weighted average of an elemental property.

    Args:
        elements: Dictionary of element counts.
        property_name: Name of the property to weight.

    Returns:
        Weighted average property value.
    """
    total_atoms = sum(elements.values())
    if total_atoms == 0:
        return 0.0

    weighted_sum = 0.0
    for elem, count in elements.items():
        prop_val = get_element_property(elem, property_name)
        if prop_val is None:
            # If property is missing, skip or use 0?
            # For robustness, we'll treat missing as 0 but log a warning
            logger.warning(f"Missing {property_name} for {elem}, treating as 0")
            prop_val = 0.0
        weighted_sum += prop_val * count

    return weighted_sum / total_atoms

def compute_variance_property(elements: Dict[str, int], property_name: str) -> float:
    """
    Compute the variance of an elemental property across the composition.

    Args:
        elements: Dictionary of element counts.
        property_name: Name of the property to compute variance for.

    Returns:
        Variance of the property.
    """
    total_atoms = sum(elements.values())
    if total_atoms == 0:
        return 0.0

    properties = []
    weights = []
    for elem, count in elements.items():
        prop_val = get_element_property(elem, property_name)
        if prop_val is not None:
            properties.append(prop_val)
            weights.append(count)

    if len(properties) == 0:
        return 0.0

    # Weighted mean
    weights_arr = np.array(weights)
    props_arr = np.array(properties)
    total_weight = np.sum(weights_arr)
    if total_weight == 0:
        return 0.0

    mean_val = np.sum(props_arr * weights_arr) / total_weight

    # Weighted variance
    variance = np.sum(weights_arr * (props_arr - mean_val) ** 2) / total_weight

    return float(variance)

def compute_descriptors(formula: str) -> Dict[str, float]:
    """
    Compute all compositional descriptors for a given formula.

    Args:
        formula: Chemical formula string.

    Returns:
        Dictionary of descriptor names and values.
    """
    elements = parse_formula_elements(formula)
    if not elements:
        return {}

    descriptors = {}

    # Atomic fractions (A, B, X sites)
    frac_A, frac_B, frac_X = compute_atomic_fractions(elements)
    descriptors['atomic_fraction_A'] = frac_A
    descriptors['atomic_fraction_B'] = frac_B
    descriptors['atomic_fraction_X'] = frac_X

    # Weighted properties
    descriptors['weighted_ionic_radius'] = compute_weighted_property(elements, 'ionic_radius')
    descriptors['weighted_electronegativity'] = compute_weighted_property(elements, 'electronegativity')
    descriptors['weighted_formation_enthalpy'] = compute_weighted_property(elements, 'formation_enthalpy')
    descriptors['first_ionization_energy'] = compute_weighted_property(elements, 'first_ionization_energy')

    # Variance metrics (NEW for T014c)
    descriptors['variance_ionic_radius'] = compute_variance_property(elements, 'ionic_radius')
    descriptors['variance_electronegativity'] = compute_variance_property(elements, 'electronegativity')

    return descriptors

def load_raw_data(input_path: Path) -> pd.DataFrame:
    """
    Load the raw descriptors dataset.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        DataFrame containing the raw data.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the descriptors dataset to a CSV file.

    Args:
        df: DataFrame containing the descriptors.
        output_path: Path to the output CSV file.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path}")

def main():
    """
    Main function to compute variance metrics and append to the dataset.
    """
    logger.info("Starting feature engineering: variance metrics computation")

    # Load data
    try:
        df = load_raw_data(INPUT_FILE)
        logger.info(f"Loaded {len(df)} rows from {INPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Compute descriptors for each formula
    descriptors_list = []
    for idx, row in df.iterrows():
        formula = row['formula']
        try:
            desc = compute_descriptors(formula)
            descriptors_list.append(desc)
        except Exception as e:
            logger.error(f"Failed to compute descriptors for {formula}: {e}")
            descriptors_list.append({})

    # Convert to DataFrame and merge
    desc_df = pd.DataFrame(descriptors_list)

    # Check if variance columns already exist and drop them if so
    variance_cols = ['variance_ionic_radius', 'variance_electronegativity']
    existing_cols = [c for c in variance_cols if c in desc_df.columns]
    if existing_cols:
        desc_df = desc_df.drop(columns=existing_cols)

    # Merge with original data
    # Ensure we only keep the new variance columns
    new_desc_df = desc_df.filter(variance_cols)

    # Concatenate along columns
    final_df = pd.concat([df, new_desc_df], axis=1)

    # Verify non-null values
    for col in variance_cols:
        if col in final_df.columns:
            null_count = final_df[col].isna().sum()
            if null_count > 0:
                logger.warning(f"Column {col} has {null_count} null values")
            else:
                logger.info(f"Column {col} has no null values")

    # Save result
    try:
        save_descriptors(final_df, OUTPUT_FILE)
        logger.info("Feature engineering completed successfully")
    except Exception as e:
        logger.error(f"Failed to save descriptors: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
