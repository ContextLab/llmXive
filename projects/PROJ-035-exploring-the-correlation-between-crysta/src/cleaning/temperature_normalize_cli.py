"""
CLI script to normalize thermal conductivity data to 300K using the Slack (1979) formula.

This script:
1. Loads thermal data from data/raw/thermal_raw.csv (produced by T014b).
2. Validates provenance using the logic from T014 (provenance_validator).
3. Identifies unknown temperatures and discards those entries.
4. Applies Slack normalization for temperatures outside 300K ± 10K.
5. Keeps temperatures within 300K ± 10K as-is.
6. Writes the normalized data to data/cleaned/normalized_thermal.csv.

Dependencies:
- T014b: src/ingest/fetch_thermal.py (produces thermal_raw.csv)
- T014: src/cleaning/provenance_validator.py (validates source references)
- T016b: src/cleaning/temperature_normalize.py (Slack formula implementation)
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Import from existing project modules
from src.cleaning.temperature_normalize import (
    slack_normalization_factor,
    is_within_reference_window,
    normalize_thermal_conductivity,
    normalize_dataframe,
    apply_temperature_normalization
)
from src.cleaning.provenance_validator import (
    is_valid_source_reference,
    validate_provenance,
    filter_valid_provenance,
    save_validation_report
)
from src.utils.validation import setup_logger

def load_thermal_data(input_path: Path) -> pd.DataFrame:
    """Load thermal data from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['structure_id', 'thermal_conductivity', 'source_reference', 'temperature']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def discard_unknown_temperatures(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Identify and discard entries with unknown temperatures.
    
    Unknown temperature indicators:
    - Null or NaN
    - 'N/A', 'unknown', 'None' (case-insensitive)
    - -1
    - Empty string
    """
    logger.info(f"Initial dataset size: {len(df)} rows")
    
    # Create a mask for valid temperatures
    valid_mask = pd.Series([True] * len(df), index=df.index)
    
    for idx, row in df.iterrows():
        temp_val = row['temperature']
        
        # Check for null/NaN
        if pd.isna(temp_val):
            valid_mask[idx] = False
            continue
        
        # Check for string representations of unknown
        if isinstance(temp_val, str):
            if temp_val.strip().lower() in ['n/a', 'unknown', 'none', '']:
                valid_mask[idx] = False
                continue
        
        # Check for numeric sentinel values
        if isinstance(temp_val, (int, float)):
            if temp_val == -1:
                valid_mask[idx] = False
                continue
    
    df_valid = df[valid_mask].copy()
    discarded_count = len(df) - len(df_valid)
    logger.info(f"Discarded {discarded_count} entries with unknown temperatures")
    logger.info(f"Remaining dataset size: {len(df_valid)} rows")
    
    return df_valid

def main():
    parser = argparse.ArgumentParser(
        description="Normalize thermal conductivity data to 300K using Slack (1979) formula."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/thermal_raw.csv"),
        help="Path to input thermal data CSV (default: data/raw/thermal_raw.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/cleaned/normalized_thermal.csv"),
        help="Path to output normalized data CSV (default: data/cleaned/normalized_thermal.csv)"
    )
    parser.add_argument(
        "--provenance-report",
        type=Path,
        default=Path("data/cleaned/provenance_report.json"),
        help="Path to provenance validation report (default: data/cleaned/provenance_report.json)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger("temperature_normalize_cli", args.log_level)
    logger.info("Starting thermal conductivity normalization pipeline")
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load thermal data
    try:
        logger.info(f"Loading thermal data from {args.input}")
        df = load_thermal_data(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Step 2: Validate provenance
    logger.info("Validating provenance of thermal data entries")
    valid_mask, report = validate_provenance(df, logger)
    
    if not valid_mask.any():
        logger.error("No entries passed provenance validation")
        sys.exit(1)
    
    df_valid_provenance = df[valid_mask].copy()
    logger.info(f"Provenance validation: {sum(valid_mask)} passed, {len(df) - sum(valid_mask)} failed")
    
    # Save provenance report
    save_validation_report(report, args.provenance_report, logger)
    
    # Step 3: Discard unknown temperatures
    df_clean_temp = discard_unknown_temperatures(df_valid_provenance, logger)
    
    if len(df_clean_temp) == 0:
        logger.error("No entries with valid temperatures remaining after filtering")
        sys.exit(1)
    
    # Step 4: Apply temperature normalization
    logger.info("Applying Slack (1979) temperature normalization to 300K")
    
    # Create a copy to avoid modifying the original
    df_normalized = df_clean_temp.copy()
    
    # Apply normalization to thermal conductivity based on temperature
    # The Slack formula: k(T) = k_ref * (T_ref / T)^n
    # We want to normalize TO 300K, so T_ref = 300K
    T_ref = 300.0
    
    def normalize_row(row):
        temp = row['temperature']
        k = row['thermal_conductivity']
        
        # Check if within reference window (300K ± 10K)
        if is_within_reference_window(temp, T_ref, tolerance=10.0):
            # Keep as-is
            return k
        else:
            # Apply Slack normalization
            # We need the exponent n, which is typically around 1-2 for perovskites
            # For now, we'll use a default value of 1.5 (common for many materials)
            # In a more sophisticated implementation, n could be material-specific
            n = 1.5
            k_normalized = normalize_thermal_conductivity(k, temp, T_ref, n)
            return k_normalized
    
    df_normalized['thermal_conductivity_normalized'] = df_normalized.apply(normalize_row, axis=1)
    
    # Rename the normalized column to thermal_conductivity for consistency
    df_normalized['thermal_conductivity'] = df_normalized['thermal_conductivity_normalized']
    df_normalized = df_normalized.drop(columns=['thermal_conductivity_normalized'])
    
    # Add a column indicating the original temperature
    df_normalized['original_temperature'] = df_normalized['temperature']
    
    # Log normalization statistics
    within_window = df_normalized[df_normalized.apply(
        lambda row: is_within_reference_window(row['original_temperature'], T_ref, tolerance=10.0), axis=1
    )]
    outside_window = df_normalized[~df_normalized.apply(
        lambda row: is_within_reference_window(row['original_temperature'], T_ref, tolerance=10.0), axis=1
    )]
    
    logger.info(f"Entries within 300K ± 10K (no normalization): {len(within_window)}")
    logger.info(f"Entries outside 300K ± 10K (normalized): {len(outside_window)}")
    
    # Step 5: Write normalized data to output file
    try:
        df_normalized.to_csv(args.output, index=False)
        logger.info(f"Normalized data written to {args.output}")
        logger.info(f"Final dataset size: {len(df_normalized)} rows")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)
    
    logger.info("Thermal conductivity normalization pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())