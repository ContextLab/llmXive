"""
Module to output connectivity results to CSV.

This module handles the loading of processed connectivity data,
computation of group statistics, and writing of results to disk.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger
from analysis.stats import (
    welch_t_test,
    fdr_correction_benjamini_hochberg,
    calculate_cohens_d,
    calculate_confidence_interval,
    process_connectivity_statistics
)

logger = get_logger(__name__)

def load_processed_connectivity_data(
    input_path: str,
    group_labels: str = "group"
) -> pd.DataFrame:
    """
    Load processed connectivity data from CSV.

    Args:
        input_path: Path to the input CSV file containing connectivity matrices
                   and subject labels.
        group_labels: Column name containing group labels (default: "group").

    Returns:
        DataFrame with connectivity data and group labels.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(path)

    required_cols = ['subject_id', 'group', 'connection_id', 'r_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def compute_group_statistics(
    df: pd.DataFrame,
    group_col: str = "group",
    value_col: str = "r_value"
) -> pd.DataFrame:
    """
    Compute group statistics for each connection.

    Performs Welch's t-test, FDR correction, and effect size calculation
    for each connection between groups.

    Args:
        df: DataFrame with connectivity data and group labels.
        group_col: Column name containing group labels.
        value_col: Column name containing connectivity values.

    Returns:
        DataFrame with statistics for each connection.
    """
    logger.info("Computing group statistics...")

    # Get unique connections
    connections = df['connection_id'].unique()
    results = []

    for conn_id in connections:
        conn_data = df[df['connection_id'] == conn_id]

        # Split by group
        group1 = conn_data[conn_data[group_col] == 'musician'][value_col]
        group2 = conn_data[conn_data[group_col] == 'non_musician'][value_col]

        if len(group1) == 0 or len(group2) == 0:
            logger.warning(f"Skipping {conn_id}: insufficient data in one group")
            continue

        # Welch's t-test
        t_stat, p_value = welch_t_test(group1.values, group2.values)

        # Effect size (Cohen's d)
        effect_size = calculate_cohens_d(group1.values, group2.values)

        # Confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(
            group1.values, group2.values, confidence_level=0.95
        )

        results.append({
            'connection_id': conn_id,
            't_stat': t_stat,
            'p_value': p_value,
            'effect_size': effect_size,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })

    results_df = pd.DataFrame(results)

    # FDR correction
    if len(results_df) > 0:
        results_df['q_value'] = fdr_correction_benjamini_hochberg(
            results_df['p_value'].values
        )
    else:
        results_df['q_value'] = []

    logger.info(f"Computed statistics for {len(results_df)} connections")
    return results_df

def write_connectivity_results(
    results_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Write connectivity results to CSV.

    Args:
        results_df: DataFrame with computed statistics.
        output_path: Path for the output CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure required columns exist
    required_cols = [
        'connection_id', 't_stat', 'p_value', 'q_value',
        'effect_size', 'ci_lower', 'ci_upper'
    ]
    missing_cols = [col for col in required_cols if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required output columns: {missing_cols}")

    # Select only required columns in correct order
    output_df = results_df[required_cols]

    output_df.to_csv(output_file, index=False)
    logger.info(f"Wrote {len(output_df)} results to {output_path}")

def main() -> None:
    """
    Main entry point for generating connectivity results.

    Reads processed connectivity data, computes group statistics,
    and writes results to CSV.
    """
    logger.info("Starting connectivity results generation...")

    # Configuration
    input_path = str(PROJECT_ROOT / "data" / "processed" / "connectivity_matrices.csv")
    output_path = str(PROJECT_ROOT / "data" / "processed" / "connectivity_results.csv")

    try:
        # Load data
        df = load_processed_connectivity_data(input_path)

        # Compute statistics
        results_df = compute_group_statistics(df)

        # Write results
        write_connectivity_results(results_df, output_path)

        logger.info("Connectivity results generation completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()