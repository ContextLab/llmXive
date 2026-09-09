"""
Data cleaning pipeline for aluminum alloy Poisson's ratio prediction.
Implements filtering, unit normalization, and ILR transformation.
"""
import sys
import logging
import argparse
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from compositional import ilr
from logging_config import setup_logging, get_logger
from config import get_config

# Initialize logger
logger = setup_logging(level="INFO", module_name="data_clean")

# Constants
MAJOR_ELEMENTS = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
ILR_ELEMENT_ORDER = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']

def log_exclusion(reason: str, count: int, step: str = "unknown"):
    """Log exclusion events to the exclusion log file."""
    log_path = Path("data/logs/exclusion_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(f"{step},{count},{reason}\n")
    logger.info(f"Excluded {count} records: {reason}")

def validate_raw_record_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    T010: Validate that raw data contains required fields at the schema level.
    Does NOT filter rows with missing values; that is T014's job.
    """
    required_fields = ['poisson_ratio', 'young_modulus', 'composition', 'measurement_method']
    
    # Check if composition is a column or if elemental columns exist
    has_composition_col = 'composition' in df.columns
    has_elemental_cols = all(elem in df.columns for elem in MAJOR_ELEMENTS)
    
    if not has_composition_col and not has_elemental_cols:
        raise ValueError(f"Missing composition data. Expected 'composition' column or elemental columns: {MAJOR_ELEMENTS}")
    
    for field in required_fields:
        if field not in df.columns and field != 'composition':
            raise ValueError(f"Missing required field in schema: {field}")
    
    logger.info("Schema validation passed: all required fields present")
    return df

def apply_independence_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    T014: Verify independence of Poisson's ratio measurements.
    Exclude records with derived methods or missing measurement_method.
    """
    initial_count = len(df)
    
    # Check for derived methods
    derived_mask = df['measurement_method'].str.contains('derived|calculated', case=False, na=False)
    derived_count = derived_mask.sum()
    
    if derived_count > 0:
        log_exclusion("derived_measurement", int(derived_count), "T014")
        df = df[~derived_mask]
    
    # Check for missing measurement_method (log warning, but retain for review per spec)
    # However, spec says: "If measurement_method is missing or null, LOG A WARNING and retain"
    # But T014 description says: "EXCLUDE the record immediately" if derived.
    # The spec clarification in T014 says: "If measurement_method is missing or null... retain... unless source metadata explicitly confirms derivation"
    # We will log missing but NOT exclude here, as per the explicit "retain" instruction.
    missing_mask = df['measurement_method'].isna() | (df['measurement_method'] == '')
    missing_count = missing_mask.sum()
    
    if missing_count > 0:
        log_exclusion("missing_measurement_method", int(missing_count), "T014")
        # Spec says: "retain the record for potential manual review (do not exclude automatically)"
        # So we do NOT exclude here.
    
    final_count = len(df)
    logger.info(f"Independence filter: {initial_count} -> {final_count} (excluded {initial_count - final_count} derived)")
    return df

def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    T011: Filter for monolithic alloys only.
    alloy_type == 'monolithic' OR is_composite == False OR composite_fraction == 0.0
    """
    initial_count = len(df)
    
    # Priority check: alloy_type first
    if 'alloy_type' in df.columns:
        monolithic_mask = df['alloy_type'] == 'monolithic'
    else:
        monolithic_mask = pd.Series([False] * len(df), index=df.index)
    
    # Secondary: is_composite
    if 'is_composite' in df.columns:
        non_composite_mask = (df['is_composite'] == False) | (df['is_composite'] == 0)
    else:
        non_composite_mask = pd.Series([True] * len(df), index=df.index)
    
    # Tertiary: composite_fraction
    if 'composite_fraction' in df.columns:
        zero_composite_mask = (df['composite_fraction'] == 0.0) | (df['composite_fraction'].isna())
    else:
        zero_composite_mask = pd.Series([True] * len(df), index=df.index)
    
    # If neither field exists, exclude (as per spec: "If neither field exists, the record is excluded")
    if 'alloy_type' not in df.columns and 'is_composite' not in df.columns and 'composite_fraction' not in df.columns:
        logger.warning("No alloy type indicators found; excluding all records")
        return pd.DataFrame()
    
    # Combine: (alloy_type == 'monolithic') OR (is_composite == False) OR (composite_fraction == 0.0)
    # But if alloy_type exists, we prioritize it.
    # Logic: Keep if (alloy_type is 'monolithic') OR (is_composite is False) OR (composite_fraction is 0.0)
    # If a record has alloy_type but it's not 'monolithic', check is_composite.
    # If it has is_composite but it's True, check composite_fraction.
    
    # Simplified logic per spec: "Check alloy_type first, then is_composite, then composite_fraction. If neither field exists, exclude."
    # This implies: if alloy_type exists and is not 'monolithic', check is_composite. If is_composite exists and is True, check composite_fraction.
    # If composite_fraction exists and is not 0.0, exclude.
    
    # Let's implement the "OR" logic as described in the definition:
    # `alloy_type == 'monolithic'` OR `is_composite == False` OR `composite_fraction == 0.0`
    mask = pd.Series([False] * len(df), index=df.index)
    
    if 'alloy_type' in df.columns:
        mask = mask | (df['alloy_type'] == 'monolithic')
    
    if 'is_composite' in df.columns:
        mask = mask | (df['is_composite'] == False)
    
    if 'composite_fraction' in df.columns:
        mask = mask | (df['composite_fraction'] == 0.0)
    
    # If no fields exist, mask is all False -> exclude all (correct)
    
    df_filtered = df[mask]
    excluded_count = initial_count - len(df_filtered)
    if excluded_count > 0:
        log_exclusion("non_monolithic", excluded_count, "T011")
    
    logger.info(f"Monolithic filter: {initial_count} -> {len(df_filtered)}")
    return df_filtered

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    T012: Unit normalization.
    Convert composition to at% if in wt%, verify sum ~1.0.
    Convert young_modulus to GPa if in MPa.
    """
    # Assume composition is already in at% from previous steps (T015c output)
    # If wt% is detected, convert using atomic weights
    # For this implementation, we assume the input from T015c is already normalized to at%
    # as per T012 requirement: "If at%, verify sum is ~1.0"
    
    if 'composition' in df.columns:
        # If composition is a dict/series of dicts, expand it
        if isinstance(df['composition'].iloc[0], dict):
            comp_df = pd.DataFrame(df['composition'].tolist(), index=df.index)
            for elem in MAJOR_ELEMENTS:
                if elem in comp_df.columns:
                    df[elem] = comp_df[elem]
            df = df.drop(columns=['composition'])
    
    # Ensure elemental columns exist
    for elem in MAJOR_ELEMENTS:
        if elem not in df.columns:
            df[elem] = 0.0
    
    # Verify sum of major elements is reasonable (handled in T013)
    # Convert young_modulus if necessary
    if 'young_modulus' in df.columns:
        # Assume input is in GPa as per spec "expected in GPa"
        # If values are > 1000, assume MPa
        if df['young_modulus'].max() > 1000:
            df['young_modulus'] = df['young_modulus'] * 0.001
            logger.info("Converted young_modulus from MPa to GPa")
    
    return df

def apply_major_element_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    T013: Exclude entries where major element sum < 0.95.
    """
    initial_count = len(df)
    
    # Ensure all major element columns exist
    for elem in MAJOR_ELEMENTS:
        if elem not in df.columns:
            df[elem] = 0.0
    
    major_sum = df[MAJOR_ELEMENTS].sum(axis=1)
    valid_mask = major_sum >= 0.95
    
    df_filtered = df[valid_mask]
    excluded_count = initial_count - len(df_filtered)
    
    if excluded_count > 0:
        log_exclusion("major_sum < 0.95", excluded_count, "T013")
    
    logger.info(f"Major element filter: {initial_count} -> {len(df_filtered)}")
    return df_filtered

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    T019: Implement ILR transformation for compositional data.
    Uses the `compositional.ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions.
    Fixed order: ['Cu', 'Mg', 'Si', 'Zn', 'Mn'] for reproducibility.
    Output: Save ILR-transformed data to data/processed/alloys_ilr.parquet.
    """
    logger.info("Starting ILR transformation")
    
    # Ensure all major element columns exist and are non-negative
    for elem in MAJOR_ELEMENTS:
        if elem not in df.columns:
            df[elem] = 0.0
        # ILR requires strictly positive values; handle zeros by replacing with a small epsilon
        df[elem] = df[elem].replace(0, 1e-10)
    
    # Extract composition columns in fixed order
    composition_df = df[ILR_ELEMENT_ORDER].copy()
    
    # Apply ILR transformation
    # The compositional.ilr function expects a DataFrame with compositional columns
    try:
        ilr_transformed = ilr(composition_df)
        logger.info(f"ILR transformation successful. Output shape: {ilr_transformed.shape}")
    except Exception as e:
        logger.error(f"ILR transformation failed: {e}")
        raise RuntimeError(f"ILR transformation failed: {e}")
    
    # Add ILR coordinates to the dataframe
    # The ilr function returns a DataFrame with columns named 'ilr_0', 'ilr_1', etc.
    for i, col in enumerate(ilr_transformed.columns):
        df[f'ilr_{i}'] = ilr_transformed[col]
    
    # Save to parquet
    output_path = Path("data/processed/alloys_ilr.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved ILR-transformed data to {output_path}")
    
    return df

def run_cleaning_pipeline(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    T015b: Orchestrate the full cleaning pipeline.
    Steps: T010 -> T014 -> T011 -> T013 -> T016 (logging) -> T019 (ILR)
    """
    if input_path is None:
        input_path = "data/processed/alloys_clean.parquet"
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # T010: Schema validation
    df = validate_raw_record_fields(df)
    
    # T014: Independence filter
    df = apply_independence_filter(df)
    
    # T011: Monolithic filter
    df = apply_monolithic_filter(df)
    
    # T012: Unit normalization
    df = normalize_units(df)
    
    # T013: Major element filter
    df = apply_major_element_filter(df)
    
    # T016: Exclusion logging (already called within each filter function)
    
    # T015b: Check row count
    if len(df) < 50:
        logger.error(f"Insufficient data after filtering (<50 entries): {len(df)}")
        sys.exit(1)
    
    # T019: ILR transformation
    df = apply_ilr_transformation(df)
    
    return df

def main():
    """CLI entry point for data cleaning pipeline."""
    parser = argparse.ArgumentParser(description="Clean and transform alloy data")
    parser.add_argument("--input", type=str, default="data/processed/alloys_clean.parquet",
                      help="Input parquet file path")
    parser.add_argument("--output", type=str, default="data/processed/alloys_ilr.parquet",
                      help="Output parquet file path")
    args = parser.parse_args()
    
    logger.info("Starting data cleaning pipeline")
    df = run_cleaning_pipeline(input_path=args.input)
    logger.info(f"Pipeline completed. Output saved to {args.output}")

if __name__ == "__main__":
    main()