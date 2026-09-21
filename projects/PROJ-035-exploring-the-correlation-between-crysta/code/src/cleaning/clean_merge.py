import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np

from src.ingest.fetch_structures import fetch_perovskite_structures
from src.ingest.fetch_thermal import fetch_perovskite_thermal_data
from src.cleaning.provenance_validator import validate_provenance, save_validation_report, filter_valid_provenance
from src.cleaning.temperature_normalize import apply_temperature_normalization
from src.utils.validation import validate_dataframe_columns, validate_no_nulls, setup_logger
from src.config.env import validate_environment

logger = setup_logger('clean_merge', logging.INFO)

# Required columns per schema (T005)
REQUIRED_COLUMNS = [
    'structure_id', 'thermal_conductivity', 'source_reference', 
    'chemistry_class', 'temperature', 'tilting_angle', 
    'bond_length_variance', 'tolerance_factor', 'unit_cell_volume'
]

def merge_datasets(structures_df: pd.DataFrame, thermal_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge structures and thermal data on a common key.
    Assumes 'structure_id' exists in both or can be derived.
    For this pipeline, we assume thermal_df has 'structure_id' or a matching key.
    If thermal data lacks structure_id, we attempt to match on composition or ID.
    Here we perform an inner join on 'structure_id'.
    """
    logger.info(f"Structures shape: {structures_df.shape}")
    logger.info(f"Thermal shape: {thermal_df.shape}")
    
    # Ensure structure_id is present and string
    if 'structure_id' not in structures_df.columns:
        raise ValueError("Structures dataframe missing 'structure_id' column.")
    if 'structure_id' not in thermal_df.columns:
        # Attempt to create or find a match key if not present
        # For now, strict requirement: thermal must have structure_id or we fail
        raise ValueError("Thermal dataframe missing 'structure_id' column.")

    structures_df = structures_df.copy()
    thermal_df = thermal_df.copy()
    
    structures_df['structure_id'] = structures_df['structure_id'].astype(str)
    thermal_df['structure_id'] = thermal_df['structure_id'].astype(str)

    merged = pd.merge(
        structures_df, 
        thermal_df, 
        on='structure_id', 
        how='inner', 
        suffixes=('_struct', '_thermal')
    )
    
    logger.info(f"Merged shape (before cleaning): {merged.shape}")
    return merged

def validate_geometry(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Validate geometric constraints (e.g., tolerance factor range, non-negative volumes).
    Returns cleaned dataframe and count of dropped rows.
    """
    initial_len = len(df)
    dropped = 0
    
    # Basic geometric sanity checks
    # Tolerance factor (Goldschmidt) typically 0.8 - 1.05 for stable perovskites
    if 'tolerance_factor' in df.columns:
        valid_tf = df['tolerance_factor'].between(0.7, 1.1)
        df = df[valid_tf]
    
    # Unit cell volume must be positive
    if 'unit_cell_volume' in df.columns:
        valid_vol = df['unit_cell_volume'] > 0
        df = df[valid_vol]

    dropped = initial_len - len(df)
    if dropped > 0:
        logger.warning(f"Removed {dropped} entries due to geometric validation failures.")
    
    return df, dropped

def enforce_minimum_compositions(df: pd.DataFrame, min_count: int = 50) -> pd.DataFrame:
    """
    Count unique compositions (or structure_ids) and halt if below threshold.
    SC-001: >= 50 rows required.
    """
    unique_count = df['structure_id'].nunique()
    logger.info(f"Unique compositions found: {unique_count}")
    
    if unique_count < min_count:
        error_msg = f"Insufficient samples: N < {min_count}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return df

def add_provenance(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    Add provenance metadata to the dataframe.
    """
    df['processing_run_id'] = run_id
    df['processing_timestamp'] = pd.Timestamp.now()
    return df

def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for the clean_merge pipeline.
    1. Fetch structures (T013)
    2. Fetch thermal (T014b)
    3. Validate provenance (T014)
    4. Normalize temperature (T016)
    5. Merge
    6. Validate geometry
    7. Check minimum count
    8. Save output
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Clean and merge perovskite data")
        parser.add_argument("--output", type=str, default="data/cleaned/merged_perovskite.csv",
                            help="Path to output CSV")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
        parser.add_argument("--min-samples", type=int, default=50, help="Minimum unique samples required")
        args = parser.parse_args()

    # Validate environment
    validate_environment()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting data ingestion and merge pipeline...")

    # 1. Fetch Structures
    logger.info("Fetching structures from Materials Project...")
    try:
        structures_df = fetch_perovskite_structures()
    except Exception as e:
        logger.error(f"Failed to fetch structures: {e}")
        sys.exit(1)

    # 2. Fetch Thermal Data
    logger.info("Fetching thermal data from NIST/Literature...")
    try:
        thermal_df = fetch_perovskite_thermal_data()
    except Exception as e:
        logger.error(f"Failed to fetch thermal data: {e}")
        sys.exit(1)

    # 3. Validate Provenance (T014)
    logger.info("Validating provenance of thermal data...")
    # We expect thermal_df to have 'source_reference'
    valid_thermal_df, report = validate_provenance(thermal_df)
    save_validation_report(report, "data/cleaned/provenance_report.json")
    
    if len(valid_thermal_df) == 0:
        logger.error("No valid provenance records found in thermal data. Aborting.")
        sys.exit(1)
    
    thermal_df = valid_thermal_df

    # 4. Apply Temperature Normalization (T016)
    logger.info("Applying temperature normalization...")
    try:
        thermal_df = apply_temperature_normalization(thermal_df)
    except Exception as e:
        logger.error(f"Temperature normalization failed: {e}")
        sys.exit(1)

    # 5. Merge Datasets
    logger.info("Merging datasets...")
    try:
        merged_df = merge_datasets(structures_df, thermal_df)
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        sys.exit(1)

    if merged_df.empty:
        logger.error("Merge resulted in empty dataframe. Aborting.")
        sys.exit(1)

    # 6. Validate Geometry
    logger.info("Validating geometry...")
    merged_df, geo_dropped = validate_geometry(merged_df)

    # 7. Remove Nulls
    logger.info("Removing rows with null values in critical columns...")
    critical_cols = ['structure_id', 'thermal_conductivity']
    # Ensure these exist before checking nulls
    for col in critical_cols:
        if col not in merged_df.columns:
            logger.error(f"Critical column {col} missing after merge.")
            sys.exit(1)
    
    merged_df = merged_df.dropna(subset=critical_cols)

    # 8. Enforce Minimum Samples (SC-001)
    logger.info(f"Checking for minimum {args.min_samples} unique compositions...")
    try:
        merged_df = enforce_minimum_compositions(merged_df, min_count=args.min_samples)
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)

    # 9. Add Provenance Metadata
    merged_df = add_provenance(merged_df, "T015-run")

    # 10. Validate Schema Columns
    logger.info("Validating final schema...")
    # Check if all required columns exist (some might be added by descriptors later, 
    # but we ensure the base ones are there)
    for col in REQUIRED_COLUMNS:
        if col not in merged_df.columns:
            logger.warning(f"Optional/Deferred column {col} not found in merged output.")
    
    # Ensure specific columns from schema are present if they were part of input
    # We assume the merge brings them in. If not, we might need to fill or fail.
    # For this task, we ensure the critical ones exist.

    # 11. Save Output
    logger.info(f"Saving merged data to {output_path}...")
    merged_df.to_csv(output_path, index=False)
    logger.info("Pipeline completed successfully.")
    logger.info(f"Final output shape: {merged_df.shape}")

if __name__ == "__main__":
    main()
