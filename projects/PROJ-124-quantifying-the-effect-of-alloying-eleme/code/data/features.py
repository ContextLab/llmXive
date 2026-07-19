"""
Feature engineering module for Metallic Glass GFA prediction.

Computes physics-based descriptors including atomic properties,
weighted means, and pairwise size mismatch descriptors.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from pymatgen.core import Element, Composition

# Import shared utilities
from utils.logger import get_logger, FeatureEngineeringError
from config.elements import get_abundant_elements_set

logger = get_logger(__name__)

# Cache for element properties to avoid repeated lookups
_element_cache: Dict[str, Dict[str, float]] = {}

def get_element_properties(element_symbol: str) -> Dict[str, float]:
    """
    Retrieve physical properties for a given element symbol.

    Args:
        element_symbol: Chemical symbol (e.g., 'Fe', 'Cu')

    Returns:
        Dictionary with properties: atomic_radius, electronegativity, VEC, atomic_mass

    Raises:
        FeatureEngineeringError: If element is not found in Pymatgen
    """
    if element_symbol in _element_cache:
        return _element_cache[element_symbol]

    try:
        elem = Element(element_symbol)
        props = {
            'atomic_radius': elem.atomic_radius,  # Å
            'electronegativity': elem.electronegativity,  # Pauling
            'VEC': elem.oxi_state_guesses(max_oxi_states=10)[0] if hasattr(elem, 'oxi_state_guesses') else 0,
            'atomic_mass': elem.atomic_mass,
        }
        # Fallback for VEC if oxi_state_guesses fails or returns empty
        if props['VEC'] == 0 and hasattr(elem, 'group'):
            # Estimate VEC from group number for main group elements
            # Transition metals: use valence electron count from group
            group = elem.group
            if group <= 12 and group >= 3:
                props['VEC'] = group - 2  # Simplified: Sc=3, Ti=4, ... Zn=12 -> 10
            elif group == 1:
                props['VEC'] = 1
            elif group == 2:
                props['VEC'] = 2
            elif group == 13:
                props['VEC'] = 3
            elif group == 14:
                props['VEC'] = 4
            elif group == 15:
                props['VEC'] = 5
            elif group == 16:
                props['VEC'] = 6
            elif group == 17:
                props['VEC'] = 7
            elif group == 18:
                props['VEC'] = 8
            else:
                props['VEC'] = 0.0

        _element_cache[element_symbol] = props
        return props
    except Exception as e:
        logger.error(f"Failed to get properties for element {element_symbol}: {e}")
        raise FeatureEngineeringError(f"Unknown element: {element_symbol}") from e

def compute_weighted_mean(composition_dict: Dict[str, float], property_name: str) -> float:
    """
    Compute the weighted mean of a property based on atomic fractions.

    Args:
        composition_dict: Dict mapping element symbols to atomic fractions
        property_name: Property to compute mean for ('atomic_radius', 'electronegativity', 'VEC')

    Returns:
        Weighted mean value
    """
    total_weight = 0.0
    total_fraction = 0.0

    for elem, fraction in composition_dict.items():
        props = get_element_properties(elem)
        if property_name in props:
            total_weight += props[property_name] * fraction
            total_fraction += fraction

    if total_fraction == 0:
        return 0.0
    return total_weight / total_fraction

def compute_size_mismatch(composition_dict: Dict[str, float]) -> float:
    """
    Compute the atomic size mismatch parameter (delta) as defined in
    Inoue's criteria for metallic glass formation.

    Formula: delta = sqrt(sum(c_i * (1 - r_i / r_avg)^2)) * 100

    Args:
        composition_dict: Dict mapping element symbols to atomic fractions

    Returns:
        Size mismatch parameter in percent
    """
    radii = {}
    total_fraction = 0.0

    for elem, fraction in composition_dict.items():
        props = get_element_properties(elem)
        radii[elem] = props['atomic_radius']
        total_fraction += fraction

    if total_fraction == 0:
        return 0.0

    # Compute weighted mean radius
    r_avg = sum(radii[elem] * fraction for elem, fraction in composition_dict.items()) / total_fraction

    if r_avg == 0:
        return 0.0

    # Compute delta
    delta_squared = 0.0
    for elem, fraction in composition_dict.items():
        r_i = radii[elem]
        delta_squared += fraction * ((1 - r_i / r_avg) ** 2)

    return np.sqrt(delta_squared) * 100

def compute_pairwise_size_mismatch(composition_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Compute pairwise size mismatch descriptors for all unique element pairs.

    For each unique pair (A, B) in the composition, calculates:
    - delta_AB: |r_A - r_B| / max(r_A, r_B)
    - This captures local size mismatch between specific element pairs.

    Args:
        composition_dict: Dict mapping element symbols to atomic fractions

    Returns:
        Dictionary with keys like "delta_A_B" and values as the pairwise mismatch
    """
    elements = list(composition_dict.keys())
    if len(elements) < 2:
        return {}

    # Get radii for all elements
    radii = {}
    for elem in elements:
        props = get_element_properties(elem)
        radii[elem] = props['atomic_radius']

    pairwise_mismatches = {}

    # Iterate over unique pairs
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            elem_a = elements[i]
            elem_b = elements[j]

            r_a = radii[elem_a]
            r_b = radii[elem_b]

            max_r = max(r_a, r_b)
            if max_r == 0:
                delta_ab = 0.0
            else:
                delta_ab = abs(r_a - r_b) / max_r

            # Create a sorted key to ensure consistency (A_B vs B_A)
            pair_key = f"delta_{elem_a}_{elem_b}" if elem_a < elem_b else f"delta_{elem_b}_{elem_a}"
            pairwise_mismatches[pair_key] = delta_ab

    return pairwise_mismatches

def parse_composition_string(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like "Fe40Cu40Zr20" into a dictionary.

    Args:
        composition_str: String in format "ElementFraction..." (e.g., "Fe40Cu40Zr20")

    Returns:
        Dictionary mapping element symbols to atomic fractions (0.0 to 1.0)
    """
    composition_str = composition_str.strip()
    if not composition_str:
        return {}

    # Regex to match element symbols and their fractions
    # Matches: Element (1-2 chars) followed by number (integer or float)
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, composition_str)

    if not matches:
        logger.warning(f"Could not parse composition string: {composition_str}")
        return {}

    composition_dict = {}
    total = 0.0

    for elem, frac_str in matches:
        try:
            fraction = float(frac_str)
            composition_dict[elem] = fraction
            total += fraction
        except ValueError:
            logger.warning(f"Invalid fraction for element {elem} in {composition_str}")
            continue

    if total == 0:
        return {}

    # Normalize to sum to 1.0
    for elem in composition_dict:
        composition_dict[elem] /= total

    return composition_dict

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all feature engineering descriptors for the dataset.

    Adds the following columns:
    - atomic_radius_mean
    - electronegativity_mean
    - VEC_avg
    - size_mismatch (delta)
    - pairwise_size_mismatch_* (for each unique pair)

    Args:
        df: DataFrame with 'composition' column and optionally 'log10_Rc'

    Returns:
        DataFrame with added feature columns
    """
    logger.info(f"Computing features for {len(df)} samples")

    # Initialize new columns
    df = df.copy()
    df['atomic_radius_mean'] = np.nan
    df['electronegativity_mean'] = np.nan
    df['VEC_avg'] = np.nan
    df['size_mismatch'] = np.nan

    # Track which pairwise columns we'll add
    all_pairwise_columns: Set[str] = set()

    # First pass: compute scalar features and collect all pairwise keys
    pairwise_data: List[Dict[str, float]] = []

    for idx, row in df.iterrows():
        comp_str = row['composition']
        composition_dict = parse_composition_string(comp_str)

        if not composition_dict:
            logger.warning(f"Skipping invalid composition at index {idx}: {comp_str}")
            pairwise_data.append({})
            continue

        # Scalar features
        df.at[idx, 'atomic_radius_mean'] = compute_weighted_mean(composition_dict, 'atomic_radius')
        df.at[idx, 'electronegativity_mean'] = compute_weighted_mean(composition_dict, 'electronegativity')
        df.at[idx, 'VEC_avg'] = compute_weighted_mean(composition_dict, 'VEC')
        df.at[idx, 'size_mismatch'] = compute_size_mismatch(composition_dict)

        # Pairwise features
        pairwise = compute_pairwise_size_mismatch(composition_dict)
        pairwise_data.append(pairwise)
        all_pairwise_columns.update(pairwise.keys())

    # Add pairwise columns dynamically
    for col in sorted(all_pairwise_columns):
        df[col] = np.nan
        for idx, pairwise in enumerate(pairwise_data):
            if idx < len(df) and col in pairwise:
                df.at[idx, col] = pairwise[col]

    # Log summary
    logger.info(f"Computed {len(all_pairwise_columns)} pairwise size mismatch descriptors")
    logger.info(f"Total feature columns added: {4 + len(all_pairwise_columns)}")

    return df

def main():
    """Main entry point for feature engineering pipeline."""
    logger.info("Starting feature engineering pipeline (T015: Pairwise size mismatch)")

    # Determine paths
    base_dir = Path(__file__).resolve().parents[2]
    input_path = base_dir / "data" / "processed" / "ingested_data.csv"
    output_path = base_dir / "data" / "processed" / "features.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T013 (ingest.py) first to generate ingested_data.csv")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load ingested data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    if 'composition' not in df.columns:
        logger.error("Input CSV must contain 'composition' column")
        raise ValueError("Missing 'composition' column in input data")

    # Compute features
    df_features = compute_features(df)

    # Save output
    logger.info(f"Saving features to {output_path}")
    df_features.to_csv(output_path, index=False)

    # Verify output
    if output_path.exists():
        logger.info(f"Successfully saved {len(df_features)} rows to {output_path}")
        logger.info(f"Feature columns: {list(df_features.columns)}")
    else:
        raise FeatureEngineeringError("Failed to write output file")

    logger.info("Feature engineering pipeline completed successfully")

if __name__ == "__main__":
    main()