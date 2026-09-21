"""
Filtering logic for High-Entropy Alloy (HEA) samples.

Retains samples with:
1. ≥5 principal elements (composition sum > 0 for at least 5 elements)
2. Valid Bulk Modulus (non-null, positive value)
"""
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def count_principal_elements(row: pd.Series, composition_columns: List[str], threshold: float = 0.01) -> int:
    """
    Count the number of principal elements in a composition row.
    
    An element is considered 'principal' if its atomic fraction exceeds the threshold.
    
    Args:
        row: A pandas Series representing a single sample row.
        composition_columns: List of column names representing element compositions.
        threshold: Minimum atomic fraction to count as a principal element.
        
    Returns:
        int: Number of principal elements.
    """
    if not composition_columns:
        return 0
    
    # Extract composition values for this row
    compositions = row[composition_columns].values
    
    # Count elements above threshold
    count = np.sum(compositions > threshold)
    
    return int(count)


def filter_hea_samples(
    df: pd.DataFrame,
    composition_columns: List[str],
    bulk_modulus_column: str = 'bulk_modulus',
    min_elements: int = 5,
    min_threshold: float = 0.01,
    min_bulk_modulus: float = 0.0
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter HEA samples based on principal element count and valid Bulk Modulus.
    
    Args:
        df: Input DataFrame with composition and property columns.
        composition_columns: List of column names representing element compositions.
        bulk_modulus_column: Name of the column containing Bulk Modulus values.
        min_elements: Minimum number of principal elements required (default: 5).
        min_threshold: Threshold for considering an element 'principal' (default: 0.01).
        min_bulk_modulus: Minimum valid Bulk Modulus value (default: 0.0).
        
    Returns:
        Tuple containing:
            - Filtered DataFrame
            - Statistics dictionary with filtering details
    """
    logger.info(f"Starting filtering: min_elements={min_elements}, bulk_modulus_column={bulk_modulus_column}")
    
    initial_count = len(df)
    if initial_count == 0:
        logger.warning("Input DataFrame is empty")
        return df, {
            'initial_count': 0,
            'final_count': 0,
            'removed_by_element_count': 0,
            'removed_by_bulk_modulus': 0,
            'removed_by_nan_bulk_modulus': 0,
            'min_elements_applied': min_elements,
            'min_bulk_modulus_applied': min_bulk_modulus
        }
    
    # Step 1: Filter by principal element count
    element_counts = df.apply(
        lambda row: count_principal_elements(row, composition_columns, min_threshold),
        axis=1
    )
    
    element_filter = element_counts >= min_elements
    df_filtered_by_elements = df[element_filter].copy()
    removed_by_elements = initial_count - len(df_filtered_by_elements)
    
    logger.info(f"Filtered by element count: {initial_count} -> {len(df_filtered_by_elements)} "
               f"(removed {removed_by_elements} samples with < {min_elements} elements)")
    
    # Step 2: Filter by valid Bulk Modulus
    # Check for NaN/None values
    bulk_modulus_series = df_filtered_by_elements[bulk_modulus_column]
    has_valid_bulk_modulus = bulk_modulus_series.notna() & (bulk_modulus_series > min_bulk_modulus)
    
    df_final = df_filtered_by_elements[has_valid_bulk_modulus].copy()
    
    removed_by_nan = (~has_valid_bulk_modulus).sum()
    removed_by_low_value = (bulk_modulus_series <= min_bulk_modulus).sum()
    removed_by_bulk_modulus = removed_by_nan + removed_by_low_value
    
    logger.info(f"Filtered by Bulk Modulus: {len(df_filtered_by_elements)} -> {len(df_final)} "
               f"(removed {removed_by_nan} NaN, {removed_by_low_value} <= {min_bulk_modulus})")
    
    stats = {
        'initial_count': initial_count,
        'final_count': len(df_final),
        'removed_by_element_count': removed_by_elements,
        'removed_by_bulk_modulus': removed_by_bulk_modulus,
        'removed_by_nan_bulk_modulus': removed_by_nan,
        'removed_by_low_bulk_modulus': removed_by_low_value,
        'min_elements_applied': min_elements,
        'min_bulk_modulus_applied': min_bulk_modulus,
        'min_threshold_applied': min_threshold
    }
    
    logger.info(f"Filtering complete: {stats['initial_count']} -> {stats['final_count']} samples retained")
    
    return df_final, stats


def main():
    """
    Main entry point for filtering script.
    
    Reads from data/raw/hea_raw.csv (or specified input), applies filters,
    and writes to data/processed/hea_filtered.csv.
    """
    import argparse
    import sys
    from pathlib import Path
    import yaml
    
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Filter HEA samples by element count and Bulk Modulus')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--composition-prefix', type=str, default='composition_', 
                      help='Prefix for composition columns')
    parser.add_argument('--bulk-modulus-col', type=str, default='bulk_modulus',
                      help='Column name for Bulk Modulus')
    parser.add_argument('--min-elements', type=int, default=5,
                      help='Minimum number of principal elements')
    parser.add_argument('--min-threshold', type=float, default=0.01,
                      help='Threshold for principal element count')
    parser.add_argument('--min-bulk-modulus', type=float, default=0.0,
                      help='Minimum valid Bulk Modulus value')
    parser.add_argument('--stats-output', type=str, default=None,
                      help='Optional path to write filtering statistics JSON')
    
    args = parser.parse_args()
    
    # Initialize logging
    init_default_logging()
    
    # Load input data
    logger.info(f"Loading data from {args.input}")
    try:
        df = pd.read_csv(args.input)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows")
    
    # Identify composition columns
    composition_columns = [col for col in df.columns if col.startswith(args.composition_prefix)]
    
    if not composition_columns:
        logger.error(f"No composition columns found with prefix '{args.composition_prefix}'")
        sys.exit(1)
    
    logger.info(f"Found {len(composition_columns)} composition columns: {composition_columns[:5]}...")
    
    # Check if Bulk Modulus column exists
    if args.bulk_modulus_col not in df.columns:
        logger.error(f"Bulk Modulus column '{args.bulk_modulus_col}' not found in input")
        sys.exit(1)
    
    # Apply filtering
    df_filtered, stats = filter_hea_samples(
        df,
        composition_columns=composition_columns,
        bulk_modulus_column=args.bulk_modulus_col,
        min_elements=args.min_elements,
        min_threshold=args.min_threshold,
        min_bulk_modulus=args.min_bulk_modulus
    )
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df_filtered)} filtered samples to {args.output}")
    
    # Write stats if requested
    if args.stats_output:
        stats_path = Path(args.stats_output)
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Wrote filtering statistics to {args.stats_output}")
    
    # Print summary
    print(f"\nFiltering Summary:")
    print(f"  Initial samples: {stats['initial_count']}")
    print(f"  Final samples: {stats['final_count']}")
    print(f"  Removed by element count (< {args.min_elements}): {stats['removed_by_element_count']}")
    print(f"  Removed by Bulk Modulus (NaN or <= {args.min_bulk_modulus}): {stats['removed_by_bulk_modulus']}")
    
    if stats['final_count'] == 0:
        logger.warning("No samples passed the filtering criteria!")
        sys.exit(1)


if __name__ == '__main__':
    main()
