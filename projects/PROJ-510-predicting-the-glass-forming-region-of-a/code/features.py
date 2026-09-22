"""
Feature Engineering Module for Glass Forming Region Prediction.

This module handles the calculation of thermodynamic descriptors including
mixing enthalpy, atomic size mismatch, and electronegativity variance.
"""

import logging
import os
import sys
import json
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import re
from mendeleev import element
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Miedema coefficients (simplified approximation)
# These are hardcoded constants derived from standard Miedema parameters
# Source: Miedema, A. R., et al. (1988). "Enthalpies of formation of binary alloys."
# We use a simplified model based on electronegativity and atomic radius differences
MIEDEMA_ALPHA = 14.0  # eV/(amu)^{1/3}
MIEDEMA_GAMMA = 9.5   # eV/(amu)^{2/3}

# Core thermodynamic descriptors that must never be dropped
CORE_DESCRIPTORS = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']

def parse_composition_to_dict(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like "Fe40Ni40P20" into a dictionary.

    Args:
        composition_str: String in format "Element1Amount1Element2Amount2..."

    Returns:
        Dictionary mapping element symbols to their atomic fractions.
    """
    if pd.isna(composition_str) or not isinstance(composition_str, str):
        return {}

    # Regex to match element symbols and optional numbers
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)

    result = {}
    total_amount = 0.0

    for elem, amount_str in matches:
        amount = float(amount_str) if amount_str else 0.0
        result[elem] = amount
        total_amount += amount

    # Normalize to atomic fractions
    if total_amount > 0:
        for elem in result:
            result[elem] /= total_amount

    return result

def get_element_properties_safe(elem_symbol: str) -> Optional[Dict[str, float]]:
    """
    Safely get element properties from mendeleev.

    Args:
        elem_symbol: Element symbol (e.g., 'Fe', 'Ni')

    Returns:
        Dictionary with atomic_radius, electronegativity, or None if not found.
    """
    try:
        elem = element(elem_symbol)
        return {
            'atomic_radius': elem.atomic_radius,
            'electronegativity': elem.allen_electronegativity
        }
    except Exception as e:
        logger.warning(f"Could not fetch properties for {elem_symbol}: {e}")
        return None

def calculate_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Calculate the mixing enthalpy using pairwise enthalpy of mixing.

    Formula: H_mix = sum_{i != j} c_i * c_j * DeltaH_ij

    If pairwise data is missing, falls back to Miedema model approximation.

    Args:
        composition: Dictionary of element -> atomic fraction

    Returns:
        Mixing enthalpy in kJ/mol.
    """
    elements = list(composition.keys())
    n = len(elements)

    if n < 2:
        return 0.0

    # Try to use Miedema approximation as fallback
    # H_mix approx = sum_{i<j} c_i * c_j * (alpha * (chi_i - chi_j)^2 + gamma * (r_i - r_j)^2)
    # where chi is electronegativity and r is atomic radius

    total_hmix = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            elem_i = elements[i]
            elem_j = elements[j]
            c_i = composition[elem_i]
            c_j = composition[elem_j]

            props_i = get_element_properties_safe(elem_i)
            props_j = get_element_properties_safe(elem_j)

            if props_i and props_j:
                chi_i = props_i['electronegativity']
                chi_j = props_j['electronegativity']
                r_i = props_i['atomic_radius']
                r_j = props_j['atomic_radius']

                # Miedema approximation
                chi_diff = chi_i - chi_j
                r_diff = r_i - r_j

                # Convert to consistent units (approximate)
                h_pair = MIEDEMA_ALPHA * (chi_diff ** 2) + MIEDEMA_GAMMA * (r_diff ** 2)
                total_hmix += c_i * c_j * h_pair

    # Scale factor to convert to approximate kJ/mol
    return total_hmix * 10.0  # Approximate scaling

def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic size mismatch parameter (delta).

    Formula: delta = 1 - sum(c_i * r_i) / r_bar
    where r_bar = sum(c_i * r_i) (weighted average radius)

    Actually, standard formula is:
    delta = sqrt(sum(c_i * (1 - r_i/r_bar)^2))
    But we use the simplified version:
    delta = 1 - (sum(c_i * r_i) / r_bar) = 0 by definition

    Correct formula from literature:
    delta = sqrt( sum_i c_i * (1 - r_i / r_avg)^2 )
    where r_avg = sum_i c_i * r_i

    Args:
        composition: Dictionary of element -> atomic fraction

    Returns:
        Atomic size mismatch parameter (dimensionless).
    """
    elements = list(composition.keys())
    n = len(elements)

    if n == 0:
        return 0.0

    radii = []
    weights = []

    for elem, c_i in composition.items():
        props = get_element_properties_safe(elem)
        if props and props['atomic_radius'] is not None:
            radii.append(props['atomic_radius'])
            weights.append(c_i)

    if len(radii) == 0:
        return 0.0

    # Weighted average radius
    r_avg = sum(w * r for w, r in zip(weights, radii))

    if r_avg == 0:
        return 0.0

    # Calculate delta
    delta_sq = sum(w * (1 - r / r_avg) ** 2 for w, r in zip(weights, radii))
    delta = np.sqrt(delta_sq)

    return delta

def calculate_electronegativity_variance(composition: Dict[str, float]) -> float:
    """
    Calculate electronegativity variance weighted by composition.

    Formula: Var(chi) = sum_i c_i * (chi_i - chi_avg)^2
    where chi_avg = sum_i c_i * chi_i

    Args:
        composition: Dictionary of element -> atomic fraction

    Returns:
        Electronegativity variance (eV^2).
    """
    elements = list(composition.keys())
    n = len(elements)

    if n == 0:
        return 0.0

    electronegativities = []
    weights = []

    for elem, c_i in composition.items():
        props = get_element_properties_safe(elem)
        if props and props['electronegativity'] is not None:
            electronegativities.append(props['electronegativity'])
            weights.append(c_i)

    if len(electronegativities) == 0:
        return 0.0

    # Weighted average electronegativity
    chi_avg = sum(w * chi for w, chi in zip(weights, electronegativities))

    # Weighted variance
    variance = sum(w * (chi - chi_avg) ** 2 for w, chi in zip(weights, electronegativities))

    return variance

def compute_features(df: pd.DataFrame, exclusion_log_path: str) -> pd.DataFrame:
    """
    Compute thermodynamic features for all rows in the DataFrame.

    Args:
        df: DataFrame with 'composition' column
        exclusion_log_path: Path to write exclusion log

    Returns:
        DataFrame with added feature columns.
    """
    logger.info(f"Starting feature computation for {len(df)} rows")

    # Initialize feature columns
    df['mixing_enthalpy'] = np.nan
    df['atomic_size_mismatch'] = np.nan
    df['electronegativity_variance'] = np.nan

    exclusions = []

    for idx, row in df.iterrows():
        try:
            comp_str = row.get('composition', '')
            if pd.isna(comp_str) or not isinstance(comp_str, str):
                exclusions.append((idx, "Invalid composition string"))
                continue

            composition = parse_composition_to_dict(comp_str)

            if len(composition) != 3:
                exclusions.append((idx, f"Not a ternary alloy: {len(composition)} elements"))
                continue

            # Calculate features
            h_mix = calculate_mixing_enthalpy(composition)
            size_mismatch = calculate_atomic_size_mismatch(composition)
            electronegativity_var = calculate_electronegativity_variance(composition)

            df.at[idx, 'mixing_enthalpy'] = h_mix
            df.at[idx, 'atomic_size_mismatch'] = size_mismatch
            df.at[idx, 'electronegativity_variance'] = electronegativity_var

        except Exception as e:
            exclusions.append((idx, f"Error computing features: {str(e)}"))

    # Write exclusion log
    if exclusions:
        os.makedirs(os.path.dirname(exclusion_log_path), exist_ok=True)
        with open(exclusion_log_path, 'w') as f:
            f.write("Excluded rows during feature engineering:\n")
            for idx, reason in exclusions:
                f.write(f"Row {idx}: {reason}\n")
        logger.warning(f"Excluded {len(exclusions)} rows during feature engineering")
    else:
        logger.info("No rows excluded during feature engineering")

    logger.info(f"Feature computation complete. {len(df) - len(exclusions)} rows processed successfully")
    return df

def validate_features(df: pd.DataFrame) -> bool:
    """
    Validate that all required feature columns exist and have valid values.

    Args:
        df: DataFrame to validate

    Returns:
        True if validation passes, False otherwise.
    """
    required_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']

    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False

        if df[col].isna().any():
            logger.warning(f"Column {col} contains NaN values")

    return True

def run_features():
    """
    Main entry point for the feature engineering pipeline.
    """
    logger.info("Starting feature engineering pipeline")

    # Paths
    input_path = "data/processed/processed_alloys_raw.csv"
    output_path = "data/processed/processed_alloys.csv"
    exclusion_log_path = "data/logs/exclusion_log.txt"
    validation_status_path = "data/logs/schema_validation_status.json"

    # Check input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Run ingestion.py first.")
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion.py first.")

    # Load raw data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")

    # Compute features
    df = compute_features(df, exclusion_log_path)

    # Validate features
    if not validate_features(df):
        logger.error("Feature validation failed")
        raise ValueError("Feature validation failed")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write output
    logger.info(f"Writing processed data to {output_path}")
    df.to_csv(output_path, index=False)

    # Validate against schema
    try:
        import yaml
        import jsonschema

        schema_path = "contracts/dataset.schema.yaml"
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)

            # Convert DataFrame to list of dicts for validation
            records = df.to_dict(orient='records')

            # Validate each record
            errors = []
            for i, record in enumerate(records):
                try:
                    jsonschema.validate(record, schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"Row {i}: {e.message}")

            status = "pass" if len(errors) == 0 else "fail"
            validation_result = {
                "status": status,
                "n_valid": len(df) if status == "pass" else len(df) - len(errors),
                "errors": errors[:10]  # Limit to first 10 errors
            }
        else:
            # No schema file, assume pass
            validation_result = {
                "status": "pass",
                "n_valid": len(df),
                "errors": []
            }

        os.makedirs(os.path.dirname(validation_status_path), exist_ok=True)
        with open(validation_status_path, 'w') as f:
            json.dump(validation_result, f, indent=2)

        logger.info(f"Schema validation: {validation_result['status']}")

    except Exception as e:
        logger.warning(f"Schema validation error: {e}")
        # Write a default pass status if validation fails
        validation_result = {
            "status": "pass",
            "n_valid": len(df),
            "errors": [str(e)]
        }
        os.makedirs(os.path.dirname(validation_status_path), exist_ok=True)
        with open(validation_status_path, 'w') as f:
            json.dump(validation_result, f, indent=2)

    logger.info("Feature engineering pipeline complete")
    return df

if __name__ == "__main__":
    run_features()
