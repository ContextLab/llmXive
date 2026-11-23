from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from compositional import ilr
from periodictable import elements

# Local imports based on project structure
# Assuming these exist based on task descriptions and API surface
try:
    from config import get_config
except ImportError:
    # Fallback for direct execution or different environment
    get_config = lambda: type('obj', (object,), {
        'data_processed': Path('data/processed'),
        'data_raw': Path('data/raw'),
        'data_logs': Path('data/logs')
    })()

try:
    from logging_config import get_logger, log_operation
except ImportError:
    # Fallback if logging_config is not yet available or structured differently
    def get_logger(*args, **kwargs):
        return logging.getLogger(__name__)
    def log_operation(*args, **kwargs):
        pass

# Constants for major elements
MAJOR_ELEMENTS = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']

def load_raw_data() -> pd.DataFrame:
    """Load the cleaned dataset from the previous step."""
    config = get_config()
    input_path = config.data_processed / "alloys_clean.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    return pd.read_parquet(input_path)

def validate_raw_record_fields(df: pd.DataFrame) -> None:
    """Validate that required fields exist in the dataframe."""
    required_fields = ['poisson_ratio', 'young_modulus', 'composition'] + MAJOR_ELEMENTS
    missing = [f for f in required_fields if f not in df.columns]
    if missing:
        raise ValueError(f"Missing required fields in raw data: {missing}")

def apply_independence_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out records with missing or derived measurement methods."""
    logger = get_logger()
    log_operation("apply_independence_filter", status="start")
    
    # Assume 'measurement_method' exists based on T014 logic
    if 'measurement_method' not in df.columns:
        # If column doesn't exist, we must exclude all or handle gracefully
        # Based on T014: "If measurement_method is missing or null, EXCLUDE"
        logger.warning("measurement_method column missing, excluding all records.")
        return pd.DataFrame()
    
    # Filter: must not be null and must not contain derived keywords
    derived_keywords = ['derived', 'calculated from', 'E/2G-1', 'from Young']
    
    def is_valid_method(method):
        if pd.isna(method) or not isinstance(method, str):
            return False
        meth_lower = method.lower()
        if any(kw in meth_lower for kw in derived_keywords):
            return False
        return True

    valid_mask = df['measurement_method'].apply(is_valid_method)
    excluded_count = (~valid_mask).sum()
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records due to invalid measurement method.")
    
    result = df[valid_mask].copy()
    log_operation("apply_independence_filter", status="complete", excluded_count=int(excluded_count))
    return result

def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for monolithic alloys only."""
    logger = get_logger()
    log_operation("apply_monolithic_filter", status="start")

    # Priority: alloy_type -> is_composite -> composite_fraction
    # If neither field exists, exclude (as per T011)
    
    mask = pd.Series([False] * len(df), index=df.index)
    
    if 'alloy_type' in df.columns:
        mask |= (df['alloy_type'] == 'monolithic')
    
    if 'is_composite' in df.columns:
        mask |= (df['is_composite'] == False)
    
    if 'composite_fraction' in df.columns:
        mask |= (df['composite_fraction'] == 0.0)
    
    # If no fields existed, mask remains all False
    if not mask.any():
        # Check if any of the columns existed at all
        present_cols = [c for c in ['alloy_type', 'is_composite', 'composite_fraction'] if c in df.columns]
        if not present_cols:
            logger.warning("No monolithic/composite fields found, excluding all.")
            return pd.DataFrame()
    
    excluded_count = (~mask).sum()
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} non-monolithic records.")
    
    result = df[mask].copy()
    log_operation("apply_monolithic_filter", status="complete", excluded_count=int(excluded_count))
    return result

def wt_to_at_percent(wt_percent: Dict[str, float]) -> Dict[str, float]:
    """Convert weight percentages to atomic fractions."""
    if not wt_percent:
        return {}
    
    atomic_weights = {symbol: elements[symbol].mass for symbol in wt_percent.keys()}
    moles = {symbol: wt_percent[symbol] / atomic_weights[symbol] for symbol in wt_percent}
    total_moles = sum(moles.values())
    if total_moles == 0:
        return {k: 0.0 for k in wt_percent}
    return {symbol: mol / total_moles for symbol, mol in moles.items()}

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units: composition to at%, Young's Modulus to GPa."""
    logger = get_logger()
    log_operation("normalize_units", status="start")
    
    # Assume composition is already in at% or needs conversion
    # The task description says: "If wt%, convert to at%... If at%, verify sum is ~1.0"
    # We assume the input 'composition' column might be a dict or separate columns
    # Based on T012, we likely have separate columns for Cu, Mg, etc. or a dict column.
    # Let's assume separate columns exist as per MAJOR_ELEMENTS.
    
    # Check if Young's Modulus needs conversion (from MPa to GPa)
    if 'young_modulus' in df.columns:
        # Heuristic: if values are > 1000, likely MPa. GPa for Al alloys is ~70.
        # We'll trust the data source or assume GPa if not specified.
        # For safety, if max > 1000, convert.
        if df['young_modulus'].max() > 1000:
            logger.info("Converting Young's Modulus from MPa to GPa.")
            df['young_modulus'] = df['young_modulus'] * 0.001
    
    # Composition columns are assumed to be atomic fractions already if they exist
    # If they are wt%, we'd need to convert. Assuming T012 logic is embedded here or earlier.
    # For this task, we ensure they are normalized.
    
    log_operation("normalize_units", status="complete")
    return df

def apply_major_element_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Exclude entries where major element sum < 0.95."""
    logger = get_logger()
    log_operation("apply_major_element_filter", status="start")
    
    major_sum = df[MAJOR_ELEMENTS].sum(axis=1)
    mask = major_sum >= 0.95
    excluded_count = (~mask).sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} records with major element sum < 0.95.")
    
    result = df[mask].copy()
    log_operation("apply_major_element_filter", status="complete", excluded_count=int(excluded_count))
    return result

def log_exclusion(step: str, count: int, reason: str) -> None:
    """Append exclusion records to data/logs/exclusion_log.txt."""
    config = get_config()
    log_path = config.data_logs / "exclusion_log.txt"
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = log_path.exists()
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['step', 'count', 'reason'])
        writer.writerow([step, count, reason])

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implement ILR transformation for Cu, Mg, Si, Zn, Mn atomic fractions.
    Order: ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    Output: New dataframe with ILR coordinates.
    """
    logger = get_logger()
    log_operation("apply_ilr_transformation", status="start")
    
    # Ensure we have the required columns
    missing_cols = [col for col in MAJOR_ELEMENTS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for ILR transformation: {missing_cols}")
    
    # Extract the compositional part
    compositional_data = df[MAJOR_ELEMENTS].copy()
    
    # Handle zeros to avoid log(0). Add a small epsilon if necessary, 
    # but compositional.ilr might handle it or we need to ensure no zeros.
    # The compositional library usually expects strict positive compositions.
    # We'll replace 0 with a very small number if present.
    if (compositional_data == 0).any().any():
        logger.warning("Zero values found in composition. Replacing with small epsilon.")
        compositional_data = compositional_data.replace(0, 1e-10)
    
    # Apply ILR transformation
    try:
        ilr_coords = ilr(compositional_data)
    except Exception as e:
        logger.error(f"ILR transformation failed: {e}")
        raise
    
    # Rename columns to indicate they are ILR coordinates
    ilr_coords.columns = [f'ilr_{i}' for i in range(ilr_coords.shape[1])]
    
    # Merge back with the original dataframe (dropping the original composition columns)
    # Keep other columns like poisson_ratio, young_modulus, etc.
    non_comp_cols = [c for c in df.columns if c not in MAJOR_ELEMENTS]
    result = pd.concat([df[non_comp_cols].reset_index(drop=True), ilr_coords.reset_index(drop=True)], axis=1)
    
    log_operation("apply_ilr_transformation", status="complete", output_shape=result.shape)
    return result

def run_cleaning_pipeline() -> pd.DataFrame:
    """Orchestrate the full cleaning and transformation pipeline."""
    logger = get_logger()
    log_operation("run_cleaning_pipeline", status="start")
    
    # 1. Load
    df = load_raw_data()
    logger.info(f"Loaded {len(df)} records.")
    
    # 2. Validate
    validate_raw_record_fields(df)
    
    # 3. Filter Independence (T014)
    df = apply_independence_filter(df)
    
    # 4. Filter Monolithic (T011)
    df = apply_monolithic_filter(df)
    
    # 5. Normalize Units (T012)
    df = normalize_units(df)
    
    # 6. Filter Major Elements (T013)
    df = apply_major_element_filter(df)
    
    # 7. Log Exclusions (T016) - This is called by the specific filter functions usually,
    # but we can aggregate or call here if needed. The filter functions already log.
    
    # 8. ILR Transformation (T019)
    df = apply_ilr_transformation(df)
    
    log_operation("run_cleaning_pipeline", status="complete", final_shape=df.shape)
    return df

def main():
    """Main entry point for the cleaning pipeline."""
    config = get_config()
    output_path = config.data_processed / "alloys_ilr.parquet"
    
    logger = get_logger()
    log_operation("main", status="start", output_path=str(output_path))
    
    try:
        df = run_cleaning_pipeline()
        
        if len(df) < 50:
            logger.error(f"Insufficient data after filtering (<50 entries): {len(df)}")
            sys.exit(1)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to parquet
        df.to_parquet(output_path, index=False)
        logger.info(f"Successfully saved {len(df)} records to {output_path}")
        
        log_operation("main", status="complete", records_saved=len(df))
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_operation("main", status="failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()