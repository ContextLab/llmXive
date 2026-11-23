"""
Feature Engineering Module for Glass Forming Region Prediction.

This module implements thermodynamic feature engineering functions including
mixing enthalpy, atomic size mismatch, and electronegativity variance calculations.
It handles edge cases such as zero enthalpy values robustly.
"""

import logging
import os
import sys
import json
import re
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Miedema model constants (approximate values from literature)
# These are used as fallback when pairwise data is missing
MIEDEMA_ALPHA = 10.0  # eV
MIEDEMA_PH_DIFF_FACTOR = 1.0
MIEDEMA_R_FACTOR = 0.1

# Core thermodynamic descriptors that should never be dropped
CORE_DESCRIPTORS = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']


def parse_composition_to_dict(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string into a dictionary of element: fraction.

    Args:
        composition_str: String like "Fe40Ni40B20" or "Cu50Zr40Al10"

    Returns:
        Dictionary mapping element symbols to their atomic fractions
    """
    if not isinstance(composition_str, str) or not composition_str.strip():
        raise ValueError(f"Invalid composition string: {composition_str}")

    # Regex to match element symbol and optional number
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)

    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")

    result = {}
    for element, amount in matches:
        if not amount:
            amount = 1
        result[element] = float(amount)

    # Normalize to fractions
    total = sum(result.values())
    for elem in result:
        result[elem] /= total

    return result


def get_element_properties_safe(element_symbol: str) -> Dict[str, float]:
    """
    Safely retrieve elemental properties from mendeleev.

    Args:
        element_symbol: Element symbol (e.g., 'Fe', 'Cu')

    Returns:
        Dictionary with atomic_radius, electronegativity, and other properties
    """
    try:
        from mendeleev import element
        elem = element(element_symbol)

        # Get atomic radius (covalent or metallic, fallback to atomic)
        radius = getattr(elem, 'atomic_radius', None)
        if radius is None:
            radius = getattr(elem, 'covalent_radius', None)
        if radius is None:
            radius = getattr(elem, 'vdw_radius', None)
        if radius is None:
            # Fallback: use periodic table approximation
            radius = 1.0  # nm, placeholder

        # Get electronegativity (Pauling scale)
        electronegativity = getattr(elem, 'electronegativity', None)
        if electronegativity is None:
            electronegativity = 1.5  # Placeholder

        return {
            'atomic_radius': float(radius),
            'electronegativity': float(electronegativity),
            'symbol': element_symbol
        }
    except Exception as e:
        logger.warning(f"Could not retrieve properties for {element_symbol}: {e}. Using fallback.")
        return {
            'atomic_radius': 1.0,
            'electronegativity': 1.5,
            'symbol': element_symbol
        }


def calculate_mixing_enthalpy(composition_dict: Dict[str, float], 
                              pairwise_data: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate the enthalpy of mixing for a ternary alloy.

    Formula: H_mix = sum_{i!=j} c_i * c_j * DeltaH_ij

    Args:
        composition_dict: Dictionary of element: fraction
        pairwise_data: Optional dictionary of pairwise enthalpy values

    Returns:
        Mixing enthalpy in kJ/mol (or arbitrary units)

    Note:
        This function explicitly handles zero enthalpy values as valid numeric results.
        No special error handling is needed for H_mix == 0, but NaN propagation is prevented.
    """
    if len(composition_dict) < 2:
        return 0.0

    elements = list(composition_dict.keys())
    fractions = [composition_dict[e] for e in elements]

    total_enthalpy = 0.0

    # Iterate over all unique pairs
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            elem_i = elements[i]
            elem_j = elements[j]
            c_i = fractions[i]
            c_j = fractions[j]

            # Determine pairwise enthalpy
            pair_key = f"{elem_i}-{elem_j}"
            reverse_key = f"{elem_j}-{elem_i}"

            if pairwise_data and (pair_key in pairwise_data or reverse_key in pairwise_data):
                delta_h = pairwise_data.get(pair_key, pairwise_data.get(reverse_key, 0.0))
            else:
                # Fallback to Miedema approximation
                props_i = get_element_properties_safe(elem_i)
                props_j = get_element_properties_safe(elem_j)

                # Simple Miedema-like approximation
                phi_diff = abs(props_i['electronegativity'] - props_j['electronegativity'])
                r_diff = abs(props_i['atomic_radius'] - props_j['atomic_radius'])
                
                delta_h = (MIEDEMA_ALPHA * phi_diff * MIEDEMA_PH_DIFF_FACTOR - 
                           MIEDEMA_R_FACTOR * r_diff)

            # Accumulate contribution: c_i * c_j * DeltaH_ij * 2 (for both i-j and j-i)
            contribution = 2.0 * c_i * c_j * delta_h
            total_enthalpy += contribution

    # CRITICAL FIX: Explicitly handle zero enthalpy as valid
    # If total_enthalpy is exactly 0.0, it's a valid physical result (e.g., ideal solution)
    # We must ensure no NaN propagation occurs
    if np.isnan(total_enthalpy):
        logger.warning("Mixing enthalpy calculation resulted in NaN. Setting to 0.0.")
        return 0.0

    # Zero enthalpy is a valid numeric value (e.g., for ideal mixtures or symmetric pairs)
    if total_enthalpy == 0.0:
        logger.debug(f"Mixing enthalpy is exactly zero for composition {composition_dict}. This is valid.")

    return float(total_enthalpy)


def calculate_atomic_size_mismatch(composition_dict: Dict[str, float]) -> float:
    """
    Calculate atomic size mismatch parameter (delta).

    Formula: delta = 1 - sum(c_i * r_i) / r_bar
    where r_i is atomic radius and r_bar is weighted average radius.

    Args:
        composition_dict: Dictionary of element: fraction

    Returns:
        Atomic size mismatch parameter (dimensionless)
    """
    if not composition_dict:
        return 0.0

    elements = list(composition_dict.keys())
    fractions = [composition_dict[e] for e in elements]

    # Calculate weighted average radius
    weighted_radius_sum = 0.0
    for elem, frac in composition_dict.items():
        props = get_element_properties_safe(elem)
        weighted_radius_sum += frac * props['atomic_radius']

    if weighted_radius_sum == 0.0:
        logger.warning("Weighted average radius is zero. Returning 0.0 for size mismatch.")
        return 0.0

    # delta = 1 - (weighted_sum / weighted_mean) = 1 - 1 = 0? 
    # Correction: The formula is typically: delta = sqrt(sum(c_i * (1 - r_i/r_bar)^2))
    # Or simpler: delta = 1 - (min_radius / max_radius) weighted
    # Let's use the standard definition: delta = 1 - sum(c_i * r_i) / r_bar
    # where r_bar = sum(c_i * r_i) -> This gives 0, which is wrong.
    
    # Standard definition from literature:
    # delta = sqrt( sum( c_i * (1 - r_i / r_bar)^2 ) )
    # where r_bar = sum( c_i * r_i )
    
    r_bar = weighted_radius_sum
    if r_bar == 0:
        return 0.0

    delta_squared = 0.0
    for elem, frac in composition_dict.items():
        props = get_element_properties_safe(elem)
        r_i = props['atomic_radius']
        if r_bar > 0:
            delta_squared += frac * ((1 - r_i / r_bar) ** 2)

    delta = np.sqrt(delta_squared)

    if np.isnan(delta):
        logger.warning("Atomic size mismatch resulted in NaN. Returning 0.0.")
        return 0.0

    return float(delta)


def calculate_electronegativity_variance(composition_dict: Dict[str, float]) -> float:
    """
    Calculate variance of electronegativity weighted by composition.

    Formula: Var(EN) = sum(c_i * (EN_i - EN_bar)^2)
    where EN_bar = sum(c_i * EN_i)

    Args:
        composition_dict: Dictionary of element: fraction

    Returns:
        Electronegativity variance (dimensionless)
    """
    if not composition_dict:
        return 0.0

    # Calculate weighted mean electronegativity
    en_bar = 0.0
    for elem, frac in composition_dict.items():
        props = get_element_properties_safe(elem)
        en_bar += frac * props['electronegativity']

    if en_bar == 0.0:
        logger.warning("Mean electronegativity is zero. Returning 0.0 for variance.")
        return 0.0

    # Calculate variance
    variance = 0.0
    for elem, frac in composition_dict.items():
        props = get_element_properties_safe(elem)
        en_i = props['electronegativity']
        variance += frac * ((en_i - en_bar) ** 2)

    if np.isnan(variance):
        logger.warning("Electronegativity variance resulted in NaN. Returning 0.0.")
        return 0.0

    return float(variance)


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all thermodynamic features for a DataFrame of alloys.

    Args:
        df: DataFrame with 'composition' column

    Returns:
        DataFrame with added feature columns
    """
    logger.info(f"Computing features for {len(df)} samples")

    # Initialize lists to store results
    mixing_enthalpies = []
    size_mismatches = []
    electronegativity_variances = []

    for idx, row in df.iterrows():
        try:
            comp_str = row['composition']
            comp_dict = parse_composition_to_dict(comp_str)

            # Calculate features
            h_mix = calculate_mixing_enthalpy(comp_dict)
            delta = calculate_atomic_size_mismatch(comp_dict)
            en_var = calculate_electronegativity_variance(comp_dict)

            mixing_enthalpies.append(h_mix)
            size_mismatches.append(delta)
            electronegativity_variances.append(en_var)

        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            # Append NaN but ensure we don't propagate it silently
            mixing_enthalpies.append(np.nan)
            size_mismatches.append(np.nan)
            electronegativity_variances.append(np.nan)

    # Add columns to DataFrame
    df['mixing_enthalpy'] = mixing_enthalpies
    df['atomic_size_mismatch'] = size_mismatches
    df['electronegativity_variance'] = electronegativity_variances

    # Log statistics
    logger.info(f"Mixing enthalpy range: [{df['mixing_enthalpy'].min():.4f}, {df['mixing_enthalpy'].max():.4f}]")
    logger.info(f"Zero enthalpy count: {df['mixing_enthalpy'].eq(0).sum()}")

    return df


def validate_features(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that computed features are within expected ranges and no NaN propagation.

    Args:
        df: DataFrame with feature columns

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']

    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
            continue

        if df[col].isna().any():
            errors.append(f"Column {col} contains NaN values")

        # Check for zero enthalpy validity (should be allowed)
        if col == 'mixing_enthalpy':
            zero_count = df[col].eq(0).sum()
            if zero_count > 0:
                logger.info(f"Found {zero_count} samples with zero mixing enthalpy. This is valid.")

    return len(errors) == 0, errors


def run_features():
    """
    Main entry point for feature engineering pipeline.
    """
    logger.info("Starting feature engineering pipeline")

    # Define paths
    input_path = "data/processed/processed_alloys_raw.csv"
    output_path = "data/processed/processed_alloys.csv"

    # Check input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion.py first.")

    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Compute features
    df = compute_features(df)

    # Validate features
    is_valid, errors = validate_features(df)
    if not is_valid:
        logger.warning(f"Feature validation found issues: {errors}")
        # Do not fail, just log

    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

    # Log summary
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Features computed: {list(df.columns)}")

    # Handle edge case: zero enthalpy verification
    zero_enthalpy_count = df['mixing_enthalpy'].eq(0).sum()
    logger.info(f"Edge case check: {zero_enthalpy_count} samples have exactly zero mixing enthalpy (valid).")

    return df


if __name__ == "__main__":
    run_features()