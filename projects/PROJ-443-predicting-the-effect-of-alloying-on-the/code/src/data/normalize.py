"""
Normalization utilities for High-Entropy Alloy composition data.

This module enforces the constraint that composition fractions sum to 1.0,
logs any adjustments made, and handles edge cases where normalization is
not possible (e.g., missing data or zero-sum compositions).
"""
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from utils.logging_config import get_logger
from utils.validators import normalize_compositions, ValidationError

# Initialize logger for this module
logger = get_logger(__name__)


def get_composition_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns in the DataFrame that represent elemental compositions.

    Heuristic: Columns containing 'element' or matching common element symbols
    (case-insensitive) are treated as composition columns.

    Args:
        df: Input DataFrame.

    Returns:
        List of column names representing compositions.
    """
    # Common element symbols (simplified list for heuristic)
    # In a real scenario, we might parse from a periodic table or metadata
    element_symbols = {
        'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
        'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
        'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
        'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
        'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
        'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
        'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
        'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
        'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
        'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm',
        'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',
        'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og'
    }

    composition_cols = []
    for col in df.columns:
        # Check if column name contains 'element' or matches an element symbol
        col_upper = col.upper()
        if 'ELEMENT' in col_upper:
            composition_cols.append(col)
        elif col in element_symbols:
            composition_cols.append(col)

    # Fallback: If no matches found, look for columns with numeric values
    # that might represent compositions (heuristic)
    if not composition_cols:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # Heuristic: assume it's a composition if it has non-negative values
                # and sum is close to 1 (within tolerance)
                if df[col].min() >= 0:
                    composition_cols.append(col)

    logger.info(f"Identified {len(composition_cols)} composition columns: {composition_cols}")
    return composition_cols


def normalize_composition_row(row: pd.Series, composition_cols: List[str]) -> Tuple[pd.Series, bool, str]:
    """
    Normalize a single row's composition values to sum to 1.0.

    Args:
        row: A single row from the DataFrame.
        composition_cols: List of column names representing compositions.

    Returns:
        Tuple of (normalized_row, was_adjusted, log_message)
    """
    row_copy = row.copy()
    values = row_copy[composition_cols].values

    # Check for NaN or invalid values
    if np.any(np.isnan(values)):
        return row_copy, False, "Skipped: Contains NaN values"

    current_sum = np.sum(values)

    # Check if sum is already close to 1.0 (within tolerance)
    tolerance = 1e-6
    if abs(current_sum - 1.0) < tolerance:
        return row_copy, False, "Already normalized"

    # Check for zero sum (invalid)
    if current_sum == 0:
        return row_copy, False, "Skipped: Sum is zero (invalid composition)"

    # Normalize
    normalized_values = values / current_sum
    row_copy[composition_cols] = normalized_values

    return row_copy, True, f"Normalized from sum={current_sum:.6f} to 1.0"


def normalize_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalize all composition values in a DataFrame to sum to 1.0 per row.

    Logs all adjustments and returns metadata about the normalization process.

    Args:
        df: Input DataFrame with composition columns.

    Returns:
        Tuple of (normalized_dataframe, normalization_metadata)
    """
    logger.info("Starting composition normalization")

    # Identify composition columns
    composition_cols = get_composition_columns(df)

    if not composition_cols:
        logger.warning("No composition columns found. Returning original DataFrame.")
        return df, {"normalized": False, "reason": "No composition columns"}

    # Track normalization statistics
    stats = {
        "total_rows": len(df),
        "rows_normalized": 0,
        "rows_skipped": 0,
        "skipped_reasons": {},
        "original_sums": [],
        "normalized_sums": []
    }

    # Apply normalization row by row
    normalized_rows = []
    for idx, row in df.iterrows():
        norm_row, was_adjusted, log_msg = normalize_composition_row(row, composition_cols)
        normalized_rows.append(norm_row)

        if was_adjusted:
            stats["rows_normalized"] += 1
            stats["original_sums"].append(row[composition_cols].sum())
            stats["normalized_sums"].append(1.0)
            logger.debug(f"Row {idx}: {log_msg}")
        else:
            stats["rows_skipped"] += 1
            # Track skip reasons
            reason = log_msg.split(": ")[-1] if ": " in log_msg else log_msg
            stats["skipped_reasons"][reason] = stats["skipped_reasons"].get(reason, 0) + 1

    normalized_df = pd.DataFrame(normalized_rows)

    # Verify final sums
    final_sums = normalized_df[composition_cols].sum(axis=1)
    invalid_sums = final_sums[~np.isclose(final_sums, 1.0, atol=1e-6)]

    if len(invalid_sums) > 0:
        logger.warning(f"{len(invalid_sums)} rows still have invalid sums after normalization")
        stats["rows_with_invalid_sums"] = len(invalid_sums)
    else:
        stats["rows_with_invalid_sums"] = 0

    stats["normalized"] = True
    logger.info(f"Normalization complete: {stats['rows_normalized']} rows normalized, "
                f"{stats['rows_skipped']} rows skipped")

    return normalized_df, stats


def main():
    """
    Main entry point for normalization script.

    Reads data from a CSV file, normalizes compositions, and writes the result.
    This is intended to be called by the pipeline orchestrator.
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Normalize HEA composition data")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info(f"Reading input file: {args.input}")

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        raise FileNotFoundError(f"Input file not found: {args.input}")

    # Read input data
    df = pd.read_csv(args.input)
    logger.info(f"Read {len(df)} rows with {len(df.columns)} columns")

    # Normalize
    normalized_df, stats = normalize_dataframe(df)

    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    normalized_df.to_csv(args.output, index=False)
    logger.info(f"Wrote normalized data to: {args.output}")

    # Log summary
    logger.info(f"Normalization summary: {stats}")

    return normalized_df, stats


if __name__ == "__main__":
    main()
