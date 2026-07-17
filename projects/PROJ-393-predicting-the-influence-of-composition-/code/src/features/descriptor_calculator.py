"""
Descriptor Calculator for Heusler Alloy Composition Analysis.

Computes elemental and compositional descriptors based on FR-003:
1. Average Electronegativity
2. Valence Electron Concentration (VEC)
3. Atomic Radii Variance
4. Average d-electrons
5. Atomic Size Mismatch
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from src.utils.periodic_table_loader import load_elemental_properties, get_element_property
from src.utils.logging_config import setup_logging

logger = setup_logging(__name__)


def calculate_average_electronegativity(composition: Dict[str, float], properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate the weighted average electronegativity of the alloy.

    Args:
        composition: Dict mapping element symbol to atomic fraction.
        properties: Dict of elemental properties loaded from periodic_table_loader.

    Returns:
        Weighted average electronegativity.
    """
    if not composition:
        return 0.0

    total_en = 0.0
    total_frac = 0.0

    for element, fraction in composition.items():
        if element in properties and 'electronegativity' in properties[element]:
            en = properties[element]['electronegativity']
            if en is not None and not np.isnan(en):
                total_en += en * fraction
                total_frac += fraction
            else:
                logger.warning(f"Missing or invalid electronegativity for {element}, skipping.")
        else:
            logger.warning(f"Element {element} not found in periodic table properties, skipping.")

    if total_frac == 0:
        logger.error("No valid electronegativity data found for composition.")
        return np.nan

    return total_en / total_frac


def calculate_valence_electron_concentration(composition: Dict[str, float], properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate the Valence Electron Concentration (VEC).
    VEC = sum(valence_electrons * atomic_fraction)

    Args:
        composition: Dict mapping element symbol to atomic fraction.
        properties: Dict of elemental properties.

    Returns:
        Weighted average VEC.
    """
    if not composition:
        return 0.0

    total_vec = 0.0
    total_frac = 0.0

    for element, fraction in composition.items():
        if element in properties and 'valence_electrons' in properties[element]:
            vec = properties[element]['valence_electrons']
            if vec is not None and not np.isnan(vec):
                total_vec += vec * fraction
                total_frac += fraction
            else:
                logger.warning(f"Missing or invalid valence_electrons for {element}, skipping.")
        else:
            logger.warning(f"Element {element} not found in periodic table properties, skipping.")

    if total_frac == 0:
        logger.error("No valid valence electron data found for composition.")
        return np.nan

    return total_vec / total_frac


def calculate_atomic_radii_variance(composition: Dict[str, float], properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate the variance of atomic radii weighted by composition.
    Variance = sum(frac * (radius - mean_radius)^2)

    Args:
        composition: Dict mapping element symbol to atomic fraction.
        properties: Dict of elemental properties.

    Returns:
        Weighted variance of atomic radii.
    """
    if not composition:
        return 0.0

    radii = []
    fractions = []

    for element, fraction in composition.items():
        if element in properties and 'atomic_radii' in properties[element]:
            radius = properties[element]['atomic_radii']
            if radius is not None and not np.isnan(radius):
                radii.append(radius)
                fractions.append(fraction)
            else:
                logger.warning(f"Missing or invalid atomic_radii for {element}, skipping.")
        else:
            logger.warning(f"Element {element} not found in periodic table properties, skipping.")

    if len(radii) == 0:
        logger.error("No valid atomic radii data found for composition.")
        return np.nan

    radii = np.array(radii)
    fractions = np.array(fractions)

    mean_radius = np.average(radii, weights=fractions)
    variance = np.average((radii - mean_radius) ** 2, weights=fractions)

    return variance


def calculate_average_d_electrons(composition: Dict[str, float], properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate the average number of d-electrons.
    Note: Uses 'valence_electrons' as a proxy if specific d-electron count is not available,
    or assumes a standard transition metal approximation if data is missing.
    For this implementation, we assume 'valence_electrons' is the best proxy available
    in the provided elemental_properties.csv. If a specific 'd_electrons' column existed,
    it would be used here.

    Args:
        composition: Dict mapping element symbol to atomic fraction.
        properties: Dict of elemental properties.

    Returns:
        Weighted average d-electrons (proxy: valence electrons for transition metals).
    """
    # Since the provided elemental_properties.csv typically has 'valence_electrons',
    # and specific d-electron counts are often not in simple periodic tables,
    # we use valence_electrons as the descriptor here as per standard Heusler literature
    # when specific d-counts aren't provided.
    # If the properties dict has a 'd_electrons' key, we prefer that.
    if not composition:
        return 0.0

    total_de = 0.0
    total_frac = 0.0
    has_d_data = False

    for element, fraction in composition.items():
        if element in properties:
            # Check for specific d-electron column if it exists
            if 'd_electrons' in properties[element]:
                de = properties[element]['d_electrons']
            else:
                # Fallback to valence electrons for transition metals (Mn, Co, Fe, Ni, Cu, etc.)
                # This is a standard approximation in Heusler alloy studies when specific d-counts are missing.
                if 'valence_electrons' in properties[element]:
                    de = properties[element]['valence_electrons']
                else:
                    de = None

            if de is not None and not np.isnan(de):
                total_de += de * fraction
                total_frac += fraction
                has_d_data = True
            else:
                logger.warning(f"Missing or invalid d-electron data for {element}, skipping.")
        else:
            logger.warning(f"Element {element} not found in periodic table properties, skipping.")

    if not has_d_data or total_frac == 0:
        logger.error("No valid d-electron data found for composition.")
        return np.nan

    return total_de / total_frac


def calculate_atomic_size_mismatch(composition: Dict[str, float], properties: Dict[str, Dict[str, Any]]) -> float:
    """
    Calculate the atomic size mismatch (delta).
    delta = sqrt( sum(frac * (1 - radius_i / mean_radius)^2) )

    This is a common descriptor for lattice distortion in high-entropy and Heusler alloys.

    Args:
        composition: Dict mapping element symbol to atomic fraction.
        properties: Dict of elemental properties.

    Returns:
        Atomic size mismatch (delta).
    """
    if not composition:
        return 0.0

    radii = []
    fractions = []

    for element, fraction in composition.items():
        if element in properties and 'atomic_radii' in properties[element]:
            radius = properties[element]['atomic_radii']
            if radius is not None and not np.isnan(radius):
                radii.append(radius)
                fractions.append(fraction)
            else:
                logger.warning(f"Missing or invalid atomic_radii for {element}, skipping.")
        else:
            logger.warning(f"Element {element} not found in periodic table properties, skipping.")

    if len(radii) == 0:
        logger.error("No valid atomic radii data found for composition.")
        return np.nan

    radii = np.array(radii)
    fractions = np.array(fractions)

    mean_radius = np.average(radii, weights=fractions)

    if mean_radius == 0:
        logger.error("Mean atomic radius is zero, cannot calculate mismatch.")
        return np.nan

    terms = fractions * (1 - (radii / mean_radius)) ** 2
    delta = np.sqrt(np.sum(terms))

    return delta


def compute_descriptors_row(row: pd.Series, properties: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute all descriptors for a single alloy row.

    Args:
        row: A pandas Series representing a single alloy entry.
        properties: Dict of elemental properties.

    Returns:
        Dict of descriptor names and their calculated values.
    """
    # The composition column is expected to be a string like "Co2MnGa" or a dict string.
    # We rely on the composition_parser to have converted this to a format we can parse,
    # or we parse the string here if it wasn't fully expanded to fractions in the dataframe yet.
    # Assuming the 'composition' column in the processed CSV might still be the formula string
    # or a JSON string of fractions.
    # However, T019 (composition_parser) should have created atomic fractions.
    # Let's assume the row has a column 'composition_fractions' which is a dict or string representation of a dict.
    # If the column is just the formula string, we need to parse it.
    # Given T019 exists, we assume the dataframe has a column with the parsed fractions.
    # If not, we try to parse the 'composition' string.

    comp_data = None
    if 'composition_fractions' in row.index:
        val = row['composition_fractions']
        if isinstance(val, dict):
            comp_data = val
        elif isinstance(val, str):
            try:
                import ast
                comp_data = ast.literal_eval(val)
            except:
                logger.error(f"Could not parse composition_fractions: {val}")
                return {k: np.nan for k in DESCRIPTOR_NAMES}
    elif 'composition' in row.index:
        # Fallback: try to parse the formula string if fractions column is missing
        # This implies T019 might not have populated a separate column or we need to re-parse.
        # For robustness, we assume the formula is in 'composition' and we need to parse it again.
        # But T019 should have done this. Let's assume the input to this function expects a dict.
        # If we reach here, it's a data integrity issue.
        logger.error(f"Row missing 'composition_fractions' and 'composition' is not parsed: {row.get('composition')}")
        return {k: np.nan for k in DESCRIPTOR_NAMES}

    if not isinstance(comp_data, dict):
        logger.error(f"Composition data is not a dict: {type(comp_data)}")
        return {k: np.nan for k in DESCRIPTOR_NAMES}

    descriptors = {}
    descriptors['avg_electronegativity'] = calculate_average_electronegativity(comp_data, properties)
    descriptors['vec'] = calculate_valence_electron_concentration(comp_data, properties)
    descriptors['atomic_radii_variance'] = calculate_atomic_radii_variance(comp_data, properties)
    descriptors['avg_d_electrons'] = calculate_average_d_electrons(comp_data, properties)
    descriptors['atomic_size_mismatch'] = calculate_atomic_size_mismatch(comp_data, properties)

    return descriptors


def calculate_all_descriptors(df: pd.DataFrame, properties: Optional[Dict[str, Dict[str, Any]]] = None) -> pd.DataFrame:
    """
    Calculate descriptors for the entire dataframe.

    Args:
        df: The processed alloys dataframe.
        properties: Pre-loaded properties. If None, loads them.

    Returns:
        DataFrame with new descriptor columns appended.
    """
    if properties is None:
        properties = load_elemental_properties()

    descriptors_list = []
    for idx, row in df.iterrows():
        desc = compute_descriptors_row(row, properties)
        descriptors_list.append(desc)

    desc_df = pd.DataFrame(descriptors_list)

    # Concatenate original df with descriptors
    # Reset index to ensure alignment
    df_reset = df.reset_index(drop=True)
    desc_df_reset = desc_df.reset_index(drop=True)

    result = pd.concat([df_reset, desc_df_reset], axis=1)

    return result


DESCRIPTOR_NAMES = [
    'avg_electronegativity',
    'vec',
    'atomic_radii_variance',
    'avg_d_electrons',
    'atomic_size_mismatch'
]


def main():
    """Main entry point for the descriptor calculator."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting descriptor calculation pipeline.")

    input_path = Path("data/processed/alloys_raw.csv")
    output_path = Path("data/processed/alloys_features.csv")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    properties = load_elemental_properties()
    logger.info(f"Loaded properties for {len(properties)} elements.")

    result_df = calculate_all_descriptors(df, properties)

    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved feature-enriched data to {output_path}")


if __name__ == "__main__":
    import sys
    main()
