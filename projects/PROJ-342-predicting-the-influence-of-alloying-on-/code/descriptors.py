"""
code/descriptors.py

Computes atomic descriptors for metallic glass datasets.
Calculates radius mismatch, electronegativity difference, VEC,
and weighted mean radius. Saves results to CSV and diagnostic logs.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from mendeleev import element

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure output directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)


def get_element_properties(symbol: str) -> Tuple[float, float, int]:
    """
    Fetch atomic radius (pm), electronegativity (Pauling), and valence electron count for an element.

    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Zr')

    Returns:
        Tuple of (radius, electronegativity, valence_electrons)

    Raises:
        ValueError: If element is not found in mendeleev database.
    """
    try:
        el = element(symbol)
        radius = el.atomic_radius
        electronegativity = el.allen_electronegativity
        # Mendeleev 'valence_electrons' might be None for some, fallback to group or 0
        v_electrons = el.valence_electrons
        if v_electrons is None:
            # Fallback logic if valence_electrons is missing in specific version
            # Using group number for transition metals approximation if needed, but keeping simple
            v_electrons = 0
        return float(radius), float(electronegativity), int(v_electrons)
    except Exception as e:
        raise ValueError(f"Element {symbol} not found in mendeleev database: {e}")


def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Fe50Zr50' or 'Fe50.5Zr49.5' into a dict of {element: fraction}.

    Args:
        composition_str: String representation of composition.

    Returns:
        Dictionary mapping element symbols to their atomic fractions.
    """
    import re
    # Regex to match ElementSymbol followed by optional number
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, composition_str)

    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")

    composition_dict = {}
    total_at = 0.0

    for symbol, count in matches:
        count = float(count)
        composition_dict[symbol] = count
        total_at += count

    # Normalize to fractions if the sum is not 1.0 (handles cases like Fe50Zr50 -> 50, 50)
    if abs(total_at - 1.0) > 1e-5:
        for k in composition_dict:
            composition_dict[k] /= total_at

    return composition_dict


def calculate_weighted_mean_radius(composition: Dict[str, float]) -> float:
    """
    Calculate the weighted mean atomic radius (R_avg) for a composition.
    R_avg = sum(c_i * R_i)

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Weighted mean radius in pm.
    """
    r_avg = 0.0
    for symbol, fraction in composition.items():
        radius, _, _ = get_element_properties(symbol)
        r_avg += fraction * radius
    return r_avg


def calculate_radius_mismatch(composition: Dict[str, float]) -> float:
    """
    Calculate atomic radius mismatch (delta).
    delta = sqrt(sum(c_i * (1 - R_i/R_avg)^2))

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Radius mismatch value.
    """
    r_avg = calculate_weighted_mean_radius(composition)
    if r_avg == 0:
        return 0.0

    delta_sq = 0.0
    for symbol, fraction in composition.items():
        radius, _, _ = get_element_properties(symbol)
        delta_sq += fraction * ((1.0 - (radius / r_avg)) ** 2)

    return np.sqrt(delta_sq)


def calculate_electronegativity_difference(composition: Dict[str, float]) -> float:
    """
    Calculate electronegativity difference (delta_chi).
    delta_chi = sqrt(sum(c_i * (chi_i - chi_avg)^2))

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Electronegativity difference value.
    """
    chi_avg = 0.0
    chi_values = []

    for symbol, fraction in composition.items():
        _, electronegativity, _ = get_element_properties(symbol)
        chi_values.append((fraction, electronegativity))
        chi_avg += fraction * electronegativity

    delta_chi_sq = 0.0
    for fraction, chi in chi_values:
        delta_chi_sq += fraction * ((chi - chi_avg) ** 2)

    return np.sqrt(delta_chi_sq)


def calculate_vec(composition: Dict[str, float]) -> float:
    """
    Calculate average valence electron concentration (VEC).
    VEC = sum(c_i * VEC_i)

    Args:
        composition: Dict of {element: atomic_fraction}

    Returns:
        Average VEC.
    """
    vec = 0.0
    for symbol, fraction in composition.items():
        _, _, valence = get_element_properties(symbol)
        vec += fraction * valence
    return vec


def compute_descriptors(row: pd.Series) -> Tuple[float, float, float, float]:
    """
    Compute all descriptors for a single dataframe row.

    Args:
        row: DataFrame row containing 'composition' and optionally 'Tg'.

    Returns:
        Tuple of (radius_mismatch, electronegativity_diff, VEC, weighted_mean_radius)
    """
    try:
        comp_str = row['composition']
        composition = parse_composition(comp_str)
    except Exception as e:
        logger.warning(f"Failed to parse composition '{row.get('composition', 'N/A')}': {e}")
        # Return NaNs to indicate failure, filtering happens later
        return (np.nan, np.nan, np.nan, np.nan)

    r_mismatch = calculate_radius_mismatch(composition)
    chi_diff = calculate_electronegativity_difference(composition)
    vec_val = calculate_vec(composition)
    w_mean_r = calculate_weighted_mean_radius(composition)

    return r_mismatch, chi_diff, vec_val, w_mean_r


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a dataframe to compute descriptors for all rows.

    Args:
        df: DataFrame with 'composition' column.

    Returns:
        DataFrame with added descriptor columns.
    """
    logger.info(f"Processing {len(df)} rows for descriptor calculation...")

    # Apply function row-wise
    results = df.apply(compute_descriptors, axis=1)

    # Unpack results into separate columns
    df['radius_mismatch'] = [r[0] for r in results]
    df['electronegativity_diff'] = [r[1] for r in results]
    df['VEC'] = [r[2] for r in results]
    df['weighted_mean_radius'] = [r[3] for r in results]

    logger.info("Descriptor calculation complete.")
    return df


def save_diagnostic_log(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save diagnostic information (weighted mean radius stats) to JSON.

    Args:
        df: DataFrame with 'weighted_mean_radius' column.
        output_path: Path to save the JSON log.
    """
    if 'weighted_mean_radius' not in df.columns:
        logger.warning("No 'weighted_mean_radius' column found, skipping diagnostic log.")
        return

    valid_r = df['weighted_mean_radius'].dropna()
    if len(valid_r) > 0:
        w_mean_r_val = float(valid_r.mean())
    else:
        w_mean_r_val = 0.0

    log_data = {
        "weighted_mean_radius": w_mean_r_val,
        "record_count": len(df),
        "valid_radius_count": len(valid_r)
    }

    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Diagnostic log saved to {output_path}")


def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the computed descriptors to a CSV file.

    Args:
        df: DataFrame with descriptor columns.
        output_path: Path to save the CSV.
    """
    required_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns: {required_cols}. Available: {df.columns.tolist()}")

    # Drop rows where descriptors are NaN (failed calculation)
    clean_df = df.dropna(subset=required_cols)
    logger.info(f"Saving {len(clean_df)} valid records to {output_path}")

    clean_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved successfully to {output_path}")


def main():
    """
    Main entry point to run descriptor computation pipeline.
    1. Loads cleaned data from data/processed/cleaned_mg.csv
    2. Computes descriptors
    3. Saves descriptors to data/processed/descriptors.csv
    4. Saves diagnostic log to data/processed/diagnostic_log.json
    """
    input_path = DATA_PROCESSED_DIR / "cleaned_mg.csv"
    output_csv = DATA_PROCESSED_DIR / "descriptors.csv"
    output_diag = DATA_PROCESSED_DIR / "diagnostic_log.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T014 (cleaned_mg.csv) is completed first.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} rows. Columns: {df.columns.tolist()}")

    # Compute descriptors
    df = process_dataframe(df)

    # Save diagnostic log first (for T021 verification)
    save_diagnostic_log(df, output_diag)

    # Save descriptors for US3
    save_descriptors(df, output_csv)

    logger.info("T026 completed successfully.")


if __name__ == "__main__":
    main()
