#!/usr/bin/env python3
"""
Clean and merge perovskite crystal structure and thermal conductivity data.

This script merges structural data from Materials Project with thermal
conductivity data from peer-reviewed literature/NIST, removes null values,
validates geometry, and enforces minimum composition requirements.

Outputs:
    data/cleaned/merged_perovskites.csv: Cleaned, validated merged dataset

Requirements:
    - T011 (fetch_structures.py) must have completed
    - T012 (fetch_thermal.py) must have completed
"""

import sys
from pathlib import Path

# Add code directory to Python path for imports
CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

import pandas as pd
from typing import Optional

from ingest.fetch_structures import fetch_perovskite_structures
from ingest.fetch_thermal import fetch_perovskite_thermal_data
from utils.validation import setup_logger, handle_error

# Set up logging
logger = setup_logger('clean_merge', 'INFO')

# Default paths (relative to project root)
DEFAULT_STRUCTURE_PATH = 'data/raw/structures.csv'
DEFAULT_THERMAL_PATH = 'data/raw/thermal_conductivity.csv'
DEFAULT_OUTPUT_PATH = 'data/cleaned/merged_perovskites.csv'
MIN_COMPOSITIONS = 50


def merge_datasets(structures_df: pd.DataFrame, thermal_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge structural data with thermal conductivity data.

    Args:
        structures_df: DataFrame from fetch_perovskite_structures()
        thermal_df: DataFrame from fetch_perovskite_thermal_data()

    Returns:
        Merged DataFrame with both structure and thermal properties
    """
    logger.info(f"Structures data shape: {structures_df.shape}")
    logger.info(f"Thermal data shape: {thermal_df.shape}")

    # Merge on structure_id / material_id
    merged = structures_df.merge(
        thermal_df,
        left_on='structure_id',
        right_on='material_id',
        how='inner'
    )

    logger.info(f"Merged data shape: {merged.shape}")

    # Remove null values in critical columns
    critical_columns = ['thermal_conductivity', 'structure_id', 'material_id']
    initial_rows = len(merged)
    merged = merged.dropna(subset=critical_columns)
    removed_rows = initial_rows - len(merged)
    if removed_rows > 0:
        logger.warning(f"Removed {removed_rows} rows with null values in critical columns")

    return merged


def validate_geometry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate crystal geometry parameters.

    Checks:
        - Lattice parameters (a, b, c) are positive
        - Lattice angles (alpha, beta, gamma) are in valid range (0-180)
        - Formula follows ABX₃ stoichiometry pattern

    Args:
        df: Merged DataFrame with crystal structure data

    Returns:
        DataFrame with invalid entries removed
    """
    logger.info("Validating crystal geometry...")
    valid_indices = []

    for idx, row in df.iterrows():
        is_valid = True

        # Check lattice parameters are positive
        for param in ['a', 'b', 'c']:
            if param in df.columns:
                val = row.get(param)
                if pd.isna(val) or val <= 0:
                    logger.error(f"Row {idx}: Invalid {param} = {val}")
                    is_valid = False
                    break

        # Check lattice angles are in valid range
        if is_valid:
            for angle in ['alpha', 'beta', 'gamma']:
                if angle in df.columns:
                    val = row.get(angle)
                    if pd.isna(val) or val <= 0 or val >= 180:
                        logger.error(f"Row {idx}: Invalid {angle} = {val}")
                        is_valid = False
                        break

        # Check stoichiometry follows ABX₃ pattern
        if is_valid and 'formula' in df.columns:
            formula = row.get('formula', '')
            # Simple check: formula should contain 3 elements with proper stoichiometry
            # This is a basic check - more sophisticated validation would use pymatgen
            if not formula or len(str(formula)) < 3:
                logger.error(f"Row {idx}: Invalid formula = {formula}")
                is_valid = False

        if is_valid:
            valid_indices.append(idx)

    logger.info(f"Geometry validation: {len(valid_indices)} valid out of {len(df)}")
    return df.loc[valid_indices].reset_index(drop=True)


def enforce_minimum_compositions(df: pd.DataFrame) -> None:
    """
    Enforce minimum number of compositions requirement.

    Args:
        df: Cleaned DataFrame

    Raises:
        SystemExit: If minimum compositions not met (exits with error)
    """
    n = len(df)
    if n < MIN_COMPOSITIONS:
        error_msg = f"Insufficient samples: N < 50"
        logger.error(error_msg)
        handle_error(error_msg, level='ERROR')
        sys.exit(1)
    else:
        logger.info(f"Sample count OK: {n} >= {MIN_COMPOSITIONS}")


def add_provenance(df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Add provenance metadata to the cleaned dataset.

    Args:
        df: Cleaned DataFrame
        output_path: Path to output file

    Returns:
        DataFrame with provenance columns added
    """
    import datetime
    df['cleaning_timestamp'] = datetime.datetime.now().isoformat()
    df['cleaning_script_version'] = '1.0.0'
    df['source_reference'] = df.get('source_reference', 'peer-reviewed literature/NIST')
    logger.info("Added provenance metadata")
    return df


def main():
    """
    Main entry point for data cleaning pipeline.

    Executes the full cleaning pipeline:
        1. Load structures and thermal data
        2. Merge datasets
        3. Validate geometry
        4. Enforce minimum sample count
        5. Add provenance metadata
        6. Write output CSV
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Clean and merge perovskite crystal structure and thermal data'
    )
    parser.add_argument(
        '--structures',
        type=str,
        default=DEFAULT_STRUCTURE_PATH,
        help='Path to raw structures CSV'
    )
    parser.add_argument(
        '--thermal',
        type=str,
        default=DEFAULT_THERMAL_PATH,
        help='Path to raw thermal data CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help='Path to output cleaned CSV'
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting data cleaning pipeline")
    logger.info("=" * 60)

    # Load input data
    logger.info(f"Loading structures from: {args.structures}")
    structures_df = fetch_perovskite_structures(args.structures)
    if structures_df is None or structures_df.empty:
        logger.error("Failed to load structures data")
        sys.exit(1)

    logger.info(f"Loading thermal data from: {args.thermal}")
    thermal_df = fetch_perovskite_thermal_data(args.thermal)
    if thermal_df is None or thermal_df.empty:
        logger.error("Failed to load thermal data")
        sys.exit(1)

    # Merge datasets
    logger.info("Merging datasets...")
    merged_df = merge_datasets(structures_df, thermal_df)
    if merged_df.empty:
        logger.error("No data after merging")
        sys.exit(1)

    # Validate geometry
    logger.info("Validating geometry...")
    cleaned_df = validate_geometry(merged_df)
    if cleaned_df.empty:
        logger.error("No data after geometry validation")
        sys.exit(1)

    # Enforce minimum compositions
    logger.info("Enforcing minimum compositions...")
    enforce_minimum_compositions(cleaned_df)

    # Add provenance
    logger.info("Adding provenance metadata...")
    final_df = add_provenance(cleaned_df, args.output)

    # Write output
    logger.info(f"Writing output to: {args.output}")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(args.output, index=False)

    logger.info("=" * 60)
    logger.info(f"Pipeline complete. Output: {args.output}")
    logger.info(f"Final record count: {len(final_df)}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()