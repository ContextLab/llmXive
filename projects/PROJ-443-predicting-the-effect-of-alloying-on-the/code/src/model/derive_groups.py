"""
Derive 'Alloy System' grouping keys from composition data.

This module implements the logic to group High-Entropy Alloy (HEA) samples
by their unique alloy system (the set of elements present), preventing
data leakage during train/test splits by ensuring all compositions of a
specific element set stay together.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Set

from src.utils.logging_config import get_logger

# Constants for composition column detection
COMPOSITION_PREFIX = "composition_"
ELEMENT_COL_PREFIX = "elem_"

def get_composition_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns in the DataFrame that represent elemental composition.

    Heuristic: Columns starting with 'elem_' or 'composition_' are treated
    as composition data.

    Args:
        df: Input DataFrame containing processed features.

    Returns:
        List of column names representing elemental compositions.
    """
    composition_cols = [
        col for col in df.columns
        if col.startswith(ELEMENT_COL_PREFIX) or col.startswith(COMPOSITION_PREFIX)
    ]
    return sorted(composition_cols)


def derive_alloy_system_key(composition_row: pd.Series, composition_cols: List[str]) -> Tuple[str, ...]:
    """
    Derive a unique grouping key for an alloy system from a single row.

    The key is a sorted tuple of element symbols present in the composition.
    This ensures that 'FeCrNi' and 'CrFeNi' map to the same group ('Cr', 'Fe', 'Ni').

    Args:
        composition_row: A pandas Series representing a single row of the DataFrame.
        composition_cols: List of column names containing elemental composition data.

    Returns:
        A sorted tuple of element symbols present in the composition.
    """
    elements_present = []
    for col in composition_cols:
        # Extract element symbol from column name (e.g., 'elem_Fe' -> 'Fe')
        # Handle both 'elem_X' and 'composition_X' prefixes
        if col.startswith(ELEMENT_COL_PREFIX):
            elem_symbol = col[len(ELEMENT_COL_PREFIX):]
        elif col.startswith(COMPOSITION_PREFIX):
            elem_symbol = col[len(COMPOSITION_PREFIX):]
        else:
            continue

        # Check if the element is present (value > 0 or value > threshold)
        value = composition_row.get(col, 0.0)
        if pd.notna(value) and value > 1e-9:  # Small threshold to avoid floating point noise
            elements_present.append(elem_symbol)

    # Return sorted tuple to ensure consistent grouping regardless of column order
    return tuple(sorted(elements_present))


def add_alloy_system_grouping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add an 'alloy_system' column to the DataFrame based on composition data.

    This function derives the grouping key for each sample, which can be used
    for grouped train/test splitting to prevent data leakage.

    Args:
        df: Input DataFrame with composition columns.

    Returns:
        DataFrame with an additional 'alloy_system' column containing the
        sorted tuple of elements as a string representation.
    """
    logger = get_logger(__name__)
    logger.info("Deriving alloy system grouping keys from composition data.")

    composition_cols = get_composition_columns(df)

    if not composition_cols:
        logger.warning("No composition columns found. Cannot derive alloy system groups.")
        # Create a default group to avoid breaking downstream code
        df['alloy_system'] = ['unknown'] * len(df)
        return df

    # Apply the derivation function row-wise
    # Using apply is efficient enough for typical HEA dataset sizes (< 100k rows)
    # If performance becomes an issue, a vectorized approach can be implemented
    df['alloy_system'] = df.apply(
        lambda row: derive_alloy_system_key(row, composition_cols),
        axis=1
    )

    logger.info(f"Derived {df['alloy_system'].nunique()} unique alloy system groups.")

    return df


def get_unique_alloy_systems(df: pd.DataFrame) -> List[Tuple[str, ...]]:
    """
    Get a list of all unique alloy systems in the dataset.

    Args:
        df: DataFrame containing the 'alloy_system' column.

    Returns:
        List of unique alloy system keys (sorted tuples of elements).
    """
    if 'alloy_system' not in df.columns:
        raise ValueError("DataFrame must contain 'alloy_system' column. Run add_alloy_system_grouping first.")

    return df['alloy_system'].unique().tolist()


def count_samples_per_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count the number of samples in each alloy system group.

    Args:
        df: DataFrame containing the 'alloy_system' column.

    Returns:
        DataFrame with columns 'alloy_system' and 'count'.
    """
    if 'alloy_system' not in df.columns:
        raise ValueError("DataFrame must contain 'alloy_system' column. Run add_alloy_system_grouping first.")

    return df.groupby('alloy_system').size().reset_index(name='count')


def main():
    """
    Main entry point for standalone execution.

    Reads processed features from data/processed/hea_features.csv,
    derives alloy system groups, and saves the result.
    """
    logger = get_logger(__name__)
    logger.info("Starting alloy system grouping derivation.")

    input_path = "data/processed/hea_features.csv"
    output_path = "data/processed/hea_features_grouped.csv"

    try:
        # Load the processed features
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} samples from {input_path}")

        # Derive groups
        df_grouped = add_alloy_system_grouping(df)

        # Save the result
        df_grouped.to_csv(output_path, index=False)
        logger.info(f"Saved grouped data to {output_path}")

        # Log summary statistics
        unique_groups = df_grouped['alloy_system'].nunique()
        logger.info(f"Total unique alloy systems: {unique_groups}")

        if unique_groups > 0:
            group_counts = count_samples_per_group(df_grouped)
            avg_samples = group_counts['count'].mean()
            min_samples = group_counts['count'].min()
            max_samples = group_counts['count'].max()
            logger.info(f"Average samples per group: {avg_samples:.2f}")
            logger.info(f"Min/Max samples per group: {min_samples} / {max_samples}")

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise
    except Exception as e:
        logger.error(f"Error during grouping derivation: {e}")
        raise


if __name__ == "__main__":
    main()
