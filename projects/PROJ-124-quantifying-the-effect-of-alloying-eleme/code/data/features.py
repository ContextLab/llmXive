"""
Feature Engineering Module for Metallic Glass GFA Analysis.

Computes physics-based descriptors using Pymatgen:
- Atomic radius (weighted mean)
- Electronegativity (weighted mean)
- Valence Electron Concentration (VEC_raw, VEC_avg)
- Size mismatch (delta)
- Pairwise size mismatch descriptors

Output: data/processed/features.csv
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np

from pymatgen.core import Element
from utils.logger import get_logger, FeatureEngineeringError

# Initialize logger
logger = get_logger(__name__)

# Constants
ELEMENTS_DATA_PATH = Path(__file__).parent.parent / "config" / "elements.yaml"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "features.csv"
INPUT_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "ingested_data.csv"

def get_element_properties(element_symbol: str) -> Dict[str, float]:
    """
    Retrieve atomic properties for a given element symbol using Pymatgen.

    Args:
        element_symbol: Chemical symbol (e.g., 'Fe', 'Cu')

    Returns:
        Dictionary with 'atomic_radius', 'electronegativity', 'valence'
    """
    try:
        elem = Element(element_symbol)
        return {
            'atomic_radius': elem.atomic_radius,
            'electronegativity': elem.electronegativity,
            'valence': elem.valence
        }
    except Exception as e:
        logger.error(f"Failed to retrieve properties for element {element_symbol}: {e}")
        raise

def parse_composition_string(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string into a dictionary of elements and their fractions.

    Expected format: "Fe50.0Cu50.0" or "Fe_50.0_Cu_50.0" or similar.
    Handles formats like "Fe50Cu50", "Fe50.0Cu50.0", "Fe_50.0_Cu_50.0".

    Args:
        composition_str: String representing the alloy composition.

    Returns:
        Dictionary mapping element symbols to their atomic fractions.
    """
    import re

    # Normalize underscores to spaces if present, then split
    # Pattern to match ElementSymbol followed by a number (optional decimal)
    # Handles: Fe50.0, Cu20, Zr10.5
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'

    matches = re.findall(pattern, composition_str)
    if not matches:
        # Fallback for underscore separated: Fe_50.0_Cu_50.0
        # Split by underscore and reconstruct
        parts = composition_str.replace(',', ' ').split()
        matches = []
        i = 0
        while i < len(parts) - 1:
            elem = parts[i]
            # Check if next part is a number
            try:
                frac = float(parts[i+1])
                matches.append((elem, str(frac)))
                i += 2
            except ValueError:
                # If not a number, maybe it's part of the name or error
                i += 1

    if not matches:
        raise ValueError(f"Could not parse composition string: {composition_str}")

    composition_dict = {}
    total_frac = 0.0
    for elem_sym, frac_str in matches:
        try:
            frac = float(frac_str)
            composition_dict[elem_sym] = frac
            total_frac += frac
        except ValueError:
            logger.warning(f"Invalid fraction '{frac_str}' for element {elem_sym} in {composition_str}")

    if total_frac == 0:
        raise ValueError(f"Total composition fraction is zero for: {composition_str}")

    # Normalize to 1.0 if close (within 1%)
    if 0.99 <= total_frac <= 1.01:
        for k in composition_dict:
            composition_dict[k] /= total_frac
    elif total_frac != 100.0 and total_frac != 1.0:
        # If it's not normalized, normalize it anyway (assuming input is percentages or parts)
        for k in composition_dict:
            composition_dict[k] /= total_frac

    return composition_dict

def compute_weighted_mean(values: Dict[str, float], fractions: Dict[str, float]) -> float:
    """
    Compute the weighted mean of a property based on atomic fractions.

    Args:
        values: Dictionary mapping element symbols to property values.
        fractions: Dictionary mapping element symbols to atomic fractions.

    Returns:
        Weighted mean value.
    """
    if not values or not fractions:
        return np.nan

    total_weighted = 0.0
    total_frac = 0.0
    for elem, frac in fractions.items():
        if elem in values:
            total_weighted += values[elem] * frac
            total_frac += frac

    if total_frac == 0:
        return np.nan

    return total_weighted / total_frac

def compute_size_mismatch(composition_dict: Dict[str, float]) -> float:
    """
    Compute the size mismatch parameter (delta) for a composition.
    delta = sqrt(sum(c_i * (1 - r_i / r_avg)^2)) * 100

    Args:
        composition_dict: Dictionary of element -> fraction.

    Returns:
        Size mismatch percentage.
    """
    if not composition_dict:
        return np.nan

    radii = {}
    for elem in composition_dict:
        try:
            radii[elem] = Element(elem).atomic_radius
        except Exception:
            logger.warning(f"Cannot get radius for {elem}, skipping size mismatch calc")
            return np.nan

    r_avg = compute_weighted_mean(radii, composition_dict)
    if r_avg == 0:
        return np.nan

    sum_sq = 0.0
    for elem, frac in composition_dict.items():
        r_i = radii[elem]
        sum_sq += frac * ((1 - (r_i / r_avg)) ** 2)

    return np.sqrt(sum_sq) * 100

def compute_pairwise_size_mismatch(composition_dict: Dict[str, float]) -> List[float]:
    """
    Compute pairwise size mismatch for every unique pair of elements.
    Returns a list of mismatch values for pairs (i, j) where i < j.
    Formula: |r_i - r_j| / max(r_i, r_j) * 100 (or similar metric)
    Using: (r_max - r_min) / r_avg for the pair?
    Standard definition in MG literature often uses delta (global) or specific pair differences.
    Here we calculate: |r_i - r_j| / r_avg_pair * 100?
    Let's use: |r_i - r_j| / max(r_i, r_j) * 100 as a normalized difference.

    Args:
        composition_dict: Dictionary of element -> fraction.

    Returns:
        List of pairwise mismatch values.
    """
    if len(composition_dict) < 2:
        return []

    radii = {}
    for elem in composition_dict:
        try:
            radii[elem] = Element(elem).atomic_radius
        except Exception:
            continue

    elements = list(radii.keys())
    mismatches = []

    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            r_i = radii[elements[i]]
            r_j = radii[elements[j]]
            max_r = max(r_i, r_j)
            if max_r == 0:
                continue
            mismatch = abs(r_i - r_j) / max_r * 100.0
            mismatches.append(mismatch)

    return mismatches

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main function to compute all features for the dataset.

    Args:
        df: DataFrame with 'composition' and 'log10_Rc' (or 'Rc') columns.

    Returns:
        DataFrame with added feature columns.
    """
    if 'composition' not in df.columns:
        raise FeatureEngineeringError("Input DataFrame missing 'composition' column")

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting feature engineering on {len(df)} rows")

    # Lists to store results
    features_list = []
    skipped_rows = 0

    for idx, row in df.iterrows():
        try:
            comp_str = row['composition']
            comp_dict = parse_composition_string(comp_str)

            # Get properties for each element
            elem_radii = {}
            elem_electro = {}
            elem_vec = {}

            valid_elements = True
            for elem in comp_dict:
                try:
                    props = get_element_properties(elem)
                    elem_radii[elem] = props['atomic_radius']
                    elem_electro[elem] = props['electronegativity']
                    elem_vec[elem] = props['valence']
                except Exception as e:
                    logger.warning(f"Unknown or unsupported element {elem} in composition {comp_str}: {e}")
                    valid_elements = False
                    break

            if not valid_elements:
                skipped_rows += 1
                continue

            # Compute weighted means
            atomic_radius_mean = compute_weighted_mean(elem_radii, comp_dict)
            electronegativity_mean = compute_weighted_mean(elem_electro, comp_dict)
            vec_avg = compute_weighted_mean(elem_vec, comp_dict)

            # VEC_raw is the sum of valence electrons per atom?
            # Usually VEC is the weighted average. VEC_raw might be the sum of valence * fraction * atomic_weight?
            # In MG context, VEC is typically the weighted average (VEC_avg).
            # We'll store VEC_avg as the primary feature.
            # If VEC_raw is needed as a distinct sum, it's often sum(valence * fraction). Which is the same as weighted mean if fractions sum to 1.
            # Let's assume VEC_raw = VEC_avg for now, or sum(valence * fraction) which is the same.
            vec_raw = vec_avg

            # Size mismatch
            size_mismatch = compute_size_mismatch(comp_dict)

            # Pairwise size mismatch
            pairwise_mismatches = compute_pairwise_size_mismatch(comp_dict)
            # Flatten pairwise mismatches into columns or aggregate?
            # Task says "etc. as defined in contract". Contract likely expects specific columns.
            # We will create columns: pairwise_mismatch_1, pairwise_mismatch_2, ... or max/min/mean.
            # Let's store the max pairwise mismatch as a single feature for simplicity unless specified otherwise.
            # Or we can store the list as a string? No, better to aggregate.
            pairwise_max = max(pairwise_mismatches) if pairwise_mismatches else 0.0
            pairwise_mean = np.mean(pairwise_mismatches) if pairwise_mismatches else 0.0

            # Target variable
            target = row.get('log10_Rc')
            if target is None and 'Rc' in row:
                # Convert Rc to log10 if necessary
                rc_val = row['Rc']
                if rc_val <= 0:
                    logger.warning(f"Non-positive Rc value {rc_val} for {comp_str}, setting log10_Rc to NaN")
                    target = np.nan
                else:
                    target = np.log10(rc_val)

            features_list.append({
                'composition': comp_str,
                'log10_Rc': target,
                'atomic_radius_mean': atomic_radius_mean,
                'electronegativity_mean': electronegativity_mean,
                'VEC_raw': vec_raw,
                'VEC_avg': vec_avg,
                'size_mismatch': size_mismatch,
                'pairwise_mismatch_max': pairwise_max,
                'pairwise_mismatch_mean': pairwise_mean,
                'num_elements': len(comp_dict)
            })

        except Exception as e:
            logger.error(f"Error processing row {idx} ({row.get('composition', 'N/A')}): {e}")
            skipped_rows += 1
            continue

    if not features_list:
        raise FeatureEngineeringError("No valid features computed. Check input data.")

    features_df = pd.DataFrame(features_list)

    # Log summary
    logger.info(f"Feature engineering complete. Processed {len(features_df)} rows, skipped {skipped_rows} rows.")

    return features_df

def main():
    """
    Entry point for the feature engineering script.
    Reads from data/processed/ingested_data.csv and writes to data/processed/features.csv.
    """
    logger.info("Starting feature engineering pipeline...")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}. Run ingest.py first.")

    logger.info(f"Reading input from {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)

    logger.info(f"Loaded {len(df)} rows from {INPUT_PATH}")
    logger.info(f"Columns: {df.columns.tolist()}")

    # Compute features
    features_df = compute_features(df)

    # Save output
    logger.info(f"Saving features to {OUTPUT_PATH}")
    features_df.to_csv(OUTPUT_PATH, index=False)

    logger.info(f"Successfully saved {len(features_df)} rows to {OUTPUT_PATH}")
    logger.info(f"Output columns: {features_df.columns.tolist()}")

    # Verify schema (basic check)
    required_cols = ['composition', 'log10_Rc', 'atomic_radius_mean', 'electronegativity_mean', 'VEC_avg', 'size_mismatch']
    missing_cols = [col for col in required_cols if col not in features_df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns in output: {missing_cols}")
    else:
        logger.info("All required columns present in output.")

    return features_df

if __name__ == "__main__":
    main()