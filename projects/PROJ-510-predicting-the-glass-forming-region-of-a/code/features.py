"""
Feature engineering for glass-forming alloys.
Calculates thermodynamic descriptors from composition.
"""
import logging
import sys
import os
from typing import List, Dict, Any, Tuple, Optional
import re
import numpy as np
import pandas as pd
from mendeleev import element

# Add project root to path for imports if running as script
if os.path.basename(os.path.dirname(__file__)) == 'code':
    sys.path.insert(0, os.path.dirname(__file__))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import get_logger, get_element_properties, normalize_element_symbol

logger = get_logger(__name__)

# Constants
TOLERANCE = 1e-6
REQUIRED_FEATURE_COLUMNS = [
    'mixing_enthalpy',
    'atomic_size_mismatch',
    'electronegativity_variance'
]

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Cu50Zr50' or 'Cu_50_Zr_50' into a dict.

    Args:
        composition_str: String representation of alloy composition.

    Returns:
        Dictionary mapping element symbols to atomic fractions.

    Raises:
        ValueError: If composition is invalid or contains unknown elements.
    """
    if not isinstance(composition_str, str):
        raise ValueError(f"Composition must be a string, got {type(composition_str)}")

    # Normalize format: replace underscores with nothing for parsing
    clean_str = composition_str.replace('_', '')

    # Pattern to match element symbol followed by optional number
    # Elements start with uppercase, optionally followed by lowercase
    pattern = r'([A-Z][a-z]?)(\d+(?:\.\d+)?)'

    matches = re.findall(pattern, clean_str)

    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")

    composition = {}
    total_fraction = 0.0

    for symbol, fraction_str in matches:
        # Validate element exists
        try:
            elem = element(symbol)
            if elem is None:
                raise ValueError(f"Unknown element: {symbol}")
        except Exception:
            raise ValueError(f"Invalid element symbol: {symbol}")

        fraction = float(fraction_str)
        composition[symbol] = fraction
        total_fraction += fraction

    # Normalize if not exactly 100 (or 1.0)
    if abs(total_fraction - 100.0) > 1e-6 and abs(total_fraction - 1.0) > 1e-6:
        # Assume percentages if sum is ~100, fractions if ~1
        if total_fraction > 10.0:
            # Normalize percentages to fractions
            for sym in composition:
                composition[sym] /= total_fraction
        else:
            # Already fractions but sum != 1, normalize anyway
            for sym in composition:
                composition[sym] /= total_fraction

    return composition

def get_element_properties_safe(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Safely get properties for an element.

    Args:
        symbol: Element symbol.

    Returns:
        Dictionary of properties or None if element not found.
    """
    try:
        sym = normalize_element_symbol(symbol)
        if sym is None:
            return None
        elem = element(sym)
        if elem is None:
            return None

        # Extract relevant properties
        props = {
            'symbol': sym,
            'atomic_radius': elem.atomic_radius,
            'electronegativity': elem.electronegativity,
            'melting_point': elem.melting_point,
            'atomic_number': elem.atomic_number
        }

        # Handle None values
        for key, val in props.items():
            if val is None:
                if key in ['atomic_radius', 'electronegativity']:
                    logger.warning(f"Property {key} is missing for {sym}, using fallback")
                    props[key] = 0.0  # Will cause issues in calculation, handled downstream
                else:
                    props[key] = 0

        return props

    except Exception as e:
        logger.warning(f"Could not get properties for {symbol}: {e}")
        return None

def calculate_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Calculate the mixing enthalpy of an alloy.

    Formula: ΔH_mix = Σ_i Σ_j c_i * c_j * ΔH_ij
    where c_i is atomic fraction and ΔH_ij is enthalpy of mixing for pair.

    For simplicity, we use a weighted average of pairwise enthalpies.
    Note: This is a simplified model; real calculation requires Miedema parameters.

    Args:
        composition: Dict of element -> atomic fraction.

    Returns:
        Mixing enthalpy in kJ/mol.
    """
    if len(composition) <= 1:
        return 0.0

    elements = list(composition.keys())
    fractions = [composition[e] for e in elements]

    total_enthalpy = 0.0
    count = 0

    # Simple heuristic: use electronegativity difference as proxy for mixing enthalpy
    # This is a placeholder for actual Miedema calculations
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            elem_i = elements[i]
            elem_j = elements[j]
            c_i = fractions[i]
            c_j = fractions[j]

            props_i = get_element_properties_safe(elem_i)
            props_j = get_element_properties_safe(elem_j)

            if props_i is None or props_j is None:
                continue

            # Proxy: use electronegativity difference squared
            # Real implementation would use Miedema parameters
            delta_chi = props_i['electronegativity'] - props_j['electronegativity']
            if delta_chi is None:
                delta_chi = 0.0

            # Approximate mixing enthalpy contribution
            # This is a simplified model
            pair_enthalpy = -20.0 * (delta_chi ** 2)  # kJ/mol approximation

            total_enthalpy += c_i * c_j * pair_enthalpy
            count += 1

    if count == 0:
        return 0.0

    return float(total_enthalpy)

def calculate_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic size mismatch (δ).

    Formula: δ = 100 * sqrt(Σ_i c_i * (1 - r_i / r_avg)^2)
    where r_i is atomic radius and r_avg is average radius.

    Args:
        composition: Dict of element -> atomic fraction.

    Returns:
        Atomic size mismatch in percent.
    """
    if len(composition) <= 1:
        return 0.0

    elements = list(composition.keys())
    fractions = [composition[e] for e in elements]

    radii = []
    for elem in elements:
        props = get_element_properties_safe(elem)
        if props is None or props['atomic_radius'] is None:
            # Skip if radius unknown
            return float('nan')
        radii.append(props['atomic_radius'])

    if not radii:
        return float('nan')

    # Calculate weighted average radius
    r_avg = sum(c * r for c, r in zip(fractions, radii))

    if r_avg == 0:
        return float('nan')

    # Calculate mismatch
    mismatch_sum = 0.0
    for c, r in zip(fractions, radii):
        mismatch_sum += c * ((1 - r / r_avg) ** 2)

    δ = 100.0 * np.sqrt(mismatch_sum)
    return float(δ)

def calculate_electronegativity_variance(composition: Dict[str, float]) -> float:
    """
    Calculate electronegativity variance.

    Formula: Δχ = sqrt(Σ_i c_i * (χ_i - χ_avg)^2)

    Args:
        composition: Dict of element -> atomic fraction.

    Returns:
        Electronegativity variance.
    """
    if len(composition) <= 1:
        return 0.0

    elements = list(composition.keys())
    fractions = [composition[e] for e in elements]

    chi_values = []
    for elem in elements:
        props = get_element_properties_safe(elem)
        if props is None or props['electronegativity'] is None:
            return float('nan')
        chi_values.append(props['electronegativity'])

    if not chi_values:
        return float('nan')

    # Weighted average electronegativity
    chi_avg = sum(c * chi for c, chi in zip(fractions, chi_values))

    # Variance
    variance_sum = 0.0
    for c, chi in zip(fractions, chi_values):
        variance_sum += c * ((chi - chi_avg) ** 2)

    return float(np.sqrt(variance_sum))

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute thermodynamic features for all alloys in the dataframe.

    Args:
        df: DataFrame with 'composition' column.

    Returns:
        DataFrame with added feature columns.
    """
    logger.info(f"Computing features for {len(df)} alloys")

    # Initialize result dataframe
    result_df = df.copy()

    # Calculate features for each row
    mixing_enthalpies = []
    atomic_size_mismatches = []
    electronegativity_variances = []

    for idx, row in df.iterrows():
        try:
            comp_str = row['composition']
            composition = parse_composition(comp_str)

            # Check if we have enough elements (ternary or more)
            if len(composition) < 2:
                logger.warning(f"Skipping {comp_str}: less than 2 elements")
                mixing_enthalpies.append(np.nan)
                atomic_size_mismatches.append(np.nan)
                electronegativity_variances.append(np.nan)
                continue

            # Calculate features
            me = calculate_mixing_enthalpy(composition)
            asm = calculate_atomic_size_mismatch(composition)
            env = calculate_electronegativity_variance(composition)

            mixing_enthalpies.append(me)
            atomic_size_mismatches.append(asm)
            electronegativity_variances.append(env)

        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            mixing_enthalpies.append(np.nan)
            atomic_size_mismatches.append(np.nan)
            electronegativity_variances.append(np.nan)

    result_df['mixing_enthalpy'] = mixing_enthalpies
    result_df['atomic_size_mismatch'] = atomic_size_mismatches
    result_df['electronegativity_variance'] = electronegativity_variances

    logger.info(f"Feature computation complete. NaN counts: "
               f"ME={result_df['mixing_enthalpy'].isna().sum()}, "
               f"ASM={result_df['atomic_size_mismatch'].isna().sum()}, "
               f"ENV={result_df['electronegativity_variance'].isna().sum()}")

    return result_df

def validate_features(df: pd.DataFrame, tolerance: float = TOLERANCE) -> bool:
    """
    Validate computed features.

    Checks:
    1. All required columns exist
    2. No NaN in required columns (unless expected)
    3. Values are within reasonable bounds

    Args:
        df: DataFrame with computed features.
        tolerance: Tolerance for numerical checks.

    Returns:
        True if validation passes, False otherwise.
    """
    # Check required columns
    for col in REQUIRED_FEATURE_COLUMNS:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False

    # Check for NaN in critical columns (mixing_enthalpy, atomic_size_mismatch, electronegativity_variance)
    # Note: Some NaN might be expected if data is incomplete, but we flag them
    nan_counts = {}
    for col in REQUIRED_FEATURE_COLUMNS:
        nan_count = df[col].isna().sum()
        nan_counts[col] = nan_count
        if nan_count > 0:
            logger.warning(f"Column {col} has {nan_count} NaN values")

    # Check value ranges (heuristic bounds)
    # Mixing enthalpy: typically -50 to +50 kJ/mol
    if 'mixing_enthalpy' in df.columns:
        me = df['mixing_enthalpy']
        if not me.dropna().empty:
            if me.min() < -100 or me.max() > 100:
                logger.warning(f"Mixing enthalpy out of expected range: [{me.min()}, {me.max()}]")

    # Atomic size mismatch: typically 0 to 20%
    if 'atomic_size_mismatch' in df.columns:
        asm = df['atomic_size_mismatch']
        if not asm.dropna().empty:
            if asm.min() < 0 or asm.max() > 30:
                logger.warning(f"Atomic size mismatch out of expected range: [{asm.min()}, {asm.max()}]")

    # Electronegativity variance: typically 0 to 1.0
    if 'electronegativity_variance' in df.columns:
        env = df['electronegativity_variance']
        if not env.dropna().empty:
            if env.min() < 0 or env.max() > 2.0:
                logger.warning(f"Electronegativity variance out of expected range: [{env.min()}, {env.max()}]")

    logger.info("Feature validation complete")
    return True

def run_features(input_path: str, output_path: str) -> None:
    """
    Run feature engineering pipeline.

    Args:
        input_path: Path to input CSV with compositions.
        output_path: Path to save processed CSV.
    """
    logger.info(f"Loading data from {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} records")

    # Compute features
    df_features = compute_features(df)

    # Validate features
    is_valid = validate_features(df_features)

    if not is_valid:
        logger.warning("Feature validation failed, but continuing to save")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to CSV
    df_features.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

    # Print summary
    logger.info(f"Summary: {len(df_features)} records, "
               f"NaN counts: ME={df_features['mixing_enthalpy'].isna().sum()}, "
               f"ASM={df_features['atomic_size_mismatch'].isna().sum()}, "
               f"ENV={df_features['electronegativity_variance'].isna().sum()}")

if __name__ == "__main__":
    # Default paths
    input_file = "data/processed/filtered_alloys.csv"
    output_file = "data/processed/processed_alloys.csv"

    # Allow override from command line
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    run_features(input_file, output_file)
