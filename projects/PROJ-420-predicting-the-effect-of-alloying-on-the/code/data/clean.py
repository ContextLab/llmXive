"""
Data cleaning and transformation pipeline for Aluminum Alloy Poisson's Ratio prediction.
Implements US1 (Data Cleaning) and US2 (ILR Transformation) tasks.
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
from periodictable import elements

# Import local utilities
# Note: We assume logging_config and config are available in the path
try:
    from logging_config import get_logger, setup_logging, log_operation
    from config import get_config
except ImportError:
    # Fallback for standalone execution if imports fail (should not happen in pipeline)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Constants
MAJOR_ELEMENTS = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
ILR_ELEMENT_ORDER = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
MAJOR_SUM_THRESHOLD = 0.95
MIN_ROWS_FOR_CLEAN = 50

# Configure logging
# Attempt to use project logging, fallback to basic if not available
try:
    _logger = get_logger(module="data.clean")
except Exception:
    _logger = logging.getLogger("data.clean")
    _logger.setLevel(logging.INFO)
    if not _logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

def load_raw_data(input_path: str) -> pd.DataFrame:
    """Load the merged raw data from parquet file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    _logger.info(f"Loading raw data from {input_path}")
    return pd.read_parquet(path)

def validate_raw_record_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    T010: Validate that the raw data contains all required fields.
    Required: poisson_ratio, young_modulus, composition (Cu, Mg, Si, Zn, Mn), measurement_method.
    """
    required_fields = ['poisson_ratio', 'young_modulus', 'measurement_method']
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    # Check composition columns
    # Composition might be a dict column or expanded columns
    if 'composition' in df.columns:
        # If it's a dict, we need to expand it later, but check if keys exist in sample
        sample = df['composition'].dropna().iloc[0] if not df['composition'].dropna().empty else {}
        if isinstance(sample, dict):
            missing_comp = [e for e in MAJOR_ELEMENTS if e not in sample]
            if missing_comp:
                _logger.warning(f"Missing composition elements in schema: {missing_comp}")
    else:
        # Check for expanded columns directly
        missing_comp = [e for e in MAJOR_ELEMENTS if e not in df.columns]
        if missing_comp:
            _logger.warning(f"Missing composition columns in schema: {missing_comp}")
            # If columns are missing, we might need to expand the 'composition' dict first
            if 'composition' in df.columns:
                comp_df = pd.DataFrame(df['composition'].tolist(), index=df.index)
                df = pd.concat([df.drop('composition', axis=1), comp_df], axis=1)

    if missing_fields:
        raise ValueError(f"Missing required schema fields: {missing_fields}")
    
    _logger.info("Schema validation passed.")
    return df

def apply_independence_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    T014: Filter out records with missing or derived measurement methods.
    """
    exclusion_log = []
    initial_count = len(df)
    
    # Check for measurement_method
    if 'measurement_method' not in df.columns:
        _logger.warning("Column 'measurement_method' not found. Excluding all rows.")
        exclusion_log.append({'step': 'T014', 'count': initial_count, 'reason': 'missing_measurement_method_column'})
        return pd.DataFrame(), exclusion_log

    # Filter out null/missing measurement_method
    mask_valid_method = df['measurement_method'].notna() & (df['measurement_method'] != '')
    df_valid_method = df[mask_valid_method]
    excluded_count = initial_count - len(df_valid_method)
    if excluded_count > 0:
        exclusion_log.append({'step': 'T014', 'count': excluded_count, 'reason': 'missing_measurement_method'})
        _logger.info(f"Excluded {excluded_count} rows with missing measurement_method.")

    # Check for derived keywords
    derived_keywords = ['calculated from', 'derived', 'E/2G-1', "from Young's Modulus", 'derived from']
    derived_mask = pd.Series([False] * len(df_valid_method), index=df_valid_method.index)
    
    for idx, row in df_valid_method.iterrows():
        method_str = str(row['measurement_method']).lower()
        if any(kw in method_str for kw in derived_keywords):
            derived_mask[idx] = True
    
    df_independent = df_valid_method[~derived_mask]
    excluded_derived = len(df_valid_method) - len(df_independent)
    if excluded_derived > 0:
        exclusion_log.append({'step': 'T014', 'count': excluded_derived, 'reason': 'derived_measurement'})
        _logger.info(f"Excluded {excluded_derived} rows with derived measurement methods.")

    return df_independent, exclusion_log

def apply_monolithic_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    T011: Filter for monolithic alloys.
    Logic: alloy_type == 'monolithic' OR is_composite == False OR composite_fraction == 0.0
    """
    exclusion_log = []
    initial_count = len(df)
    mask = pd.Series([False] * len(df), index=df.index)

    if 'alloy_type' in df.columns:
        mask |= (df['alloy_type'] == 'monolithic')
    if 'is_composite' in df.columns:
        mask |= (df['is_composite'] == False)
    if 'composite_fraction' in df.columns:
        mask |= (df['composite_fraction'] == 0.0)

    # If none of these columns exist, exclude all (as per spec: "If neither field exists, the record is excluded")
    if not mask.any():
        if 'alloy_type' not in df.columns and 'is_composite' not in df.columns and 'composite_fraction' not in df.columns:
            exclusion_log.append({'step': 'T011', 'count': initial_count, 'reason': 'no_monolithic_indicator_fields'})
            return pd.DataFrame(), exclusion_log
        # If fields exist but no match, exclude all
        exclusion_log.append({'step': 'T011', 'count': initial_count, 'reason': 'non_monolithic'})
        return pd.DataFrame(), exclusion_log

    df_monolithic = df[mask]
    excluded_count = initial_count - len(df_monolithic)
    if excluded_count > 0:
        exclusion_log.append({'step': 'T011', 'count': excluded_count, 'reason': 'non_monolithic'})
        _logger.info(f"Excluded {excluded_count} non-monolithic rows.")

    return df_monolithic, exclusion_log

def wt_to_at_percent(wt_percent: float, element: str) -> float:
    """Convert weight percent to atomic percent for a single element."""
    # Simplified: This function is usually part of a vectorized operation
    # We assume the caller handles the vectorization or we use a helper
    raise NotImplementedError("Use normalize_units for vectorized conversion")

def normalize_units(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    T012: Normalize units.
    - Composition: Convert wt% to at% if needed.
    - Young's Modulus: Ensure GPa.
    """
    exclusion_log = []
    # Check if composition is in wt% or at%
    # Heuristic: if sum of major elements > 1.0, likely wt% (though at% can also sum to 1.0)
    # We assume the data comes with a unit indicator or we infer from context.
    # For this task, we assume 'composition' columns are already atomic fractions or we check a 'unit' column.
    # If 'composition_unit' column exists:
    if 'composition_unit' in df.columns:
        if (df['composition_unit'] == 'wt%').any():
            _logger.info("Converting wt% to at% for composition.")
            # Vectorized conversion
            # at% = (wt% / atomic_weight) / sum(wt% / atomic_weight)
            def convert_row(row):
                total = 0.0
                converted = {}
                for elem in MAJOR_ELEMENTS:
                    if elem in row and pd.notna(row[elem]):
                        wt = row[elem]
                        at_wt = wt / elements.__getattr__(elem).mass
                        converted[elem] = at_wt
                        total += at_wt
                    else:
                        converted[elem] = 0.0
                # Normalize
                if total > 0:
                    for elem in MAJOR_ELEMENTS:
                        converted[elem] /= total
                return pd.Series(converted)
            
            comp_converted = df.apply(convert_row, axis=1)
            for elem in MAJOR_ELEMENTS:
                df[elem] = comp_converted[elem]
    
    # Young's Modulus
    if 'young_modulus_unit' in df.columns:
        if (df['young_modulus_unit'] == 'MPa').any():
            _logger.info("Converting Young's Modulus from MPa to GPa.")
            df['young_modulus'] = df['young_modulus'] * 0.001

    return df, exclusion_log

def apply_major_element_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    T013: Exclude entries where sum of major elements < 0.95.
    """
    exclusion_log = []
    initial_count = len(df)
    
    # Ensure we have the columns
    for elem in MAJOR_ELEMENTS:
        if elem not in df.columns:
            df[elem] = 0.0

    major_sum = df[MAJOR_ELEMENTS].sum(axis=1)
    mask = major_sum >= MAJOR_SUM_THRESHOLD
    
    df_filtered = df[mask]
    excluded_count = initial_count - len(df_filtered)
    if excluded_count > 0:
        exclusion_log.append({'step': 'T013', 'count': excluded_count, 'reason': f'major_sum<{MAJOR_SUM_THRESHOLD}'})
        _logger.info(f"Excluded {excluded_count} rows with major element sum < {MAJOR_SUM_THRESHOLD}.")

    return df_filtered, exclusion_log

def log_exclusion(exclusion_log: List[Dict], output_path: str):
    """
    T016: Log exclusions to CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = path.exists()
    with open(path, 'a') as f:
        if not file_exists:
            f.write("step,count,reason\n")
        for entry in exclusion_log:
            f.write(f"{entry['step']},{entry['count']},{entry['reason']}\n")
    _logger.info(f"Exclusion log written to {output_path}")

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    T019: Apply ILR transformation to compositional data.
    Uses the `compositional.ilr` function.
    Order: ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    """
    _logger.info("Applying ILR transformation...")
    
    # Ensure columns exist and are numeric
    for elem in ILR_ELEMENT_ORDER:
        if elem not in df.columns:
            raise ValueError(f"Required element column '{elem}' missing for ILR transformation.")
        df[elem] = pd.to_numeric(df[elem], errors='coerce').fillna(0)
    
    # Select composition columns
    comp_cols = df[ILR_ELEMENT_ORDER].copy()
    
    # Handle zeros: ILR requires strictly positive values.
    # Add a small pseudocount if zeros exist.
    if (comp_cols == 0).any().any():
        _logger.warning("Zeros detected in composition. Applying pseudocount (1e-6).")
        comp_cols = comp_cols.replace(0, 1e-6)
    
    # Ensure sum is 1 (closure)
    sums = comp_cols.sum(axis=1)
    comp_cols = comp_cols.div(sums, axis=0)
    
    # Apply ILR
    try:
        ilr_data = ilr(comp_cols)
    except Exception as e:
        _logger.error(f"ILR transformation failed: {e}")
        raise
    
    # Rename columns to indicate ILR coordinates (e.g., ilr_0, ilr_1, ...)
    ilr_data.columns = [f'ilr_{i}' for i in range(ilr_data.shape[1])]
    
    # Concatenate with original non-compositional data
    # Drop the original composition columns to avoid redundancy
    df_out = df.drop(columns=ILR_ELEMENT_ORDER)
    df_out = pd.concat([df_out, ilr_data], axis=1)
    
    _logger.info(f"ILR transformation complete. Shape: {df_out.shape}")
    return df_out

def run_cleaning_pipeline(input_path: str, output_path: str, exclusion_log_path: str):
    """
    T015b: Orchestrate the full cleaning pipeline.
    T015c: Save the cleaned dataset.
    """
    # 1. Load
    df = load_raw_data(input_path)
    
    # 2. Validate Schema (T010)
    df = validate_raw_record_fields(df)
    
    # 3. Independence Filter (T014)
    df, log = apply_independence_filter(df)
    log_exclusion(log, exclusion_log_path)
    
    if len(df) == 0:
        _logger.error("No data remaining after independence filter.")
        sys.exit(1)
    
    # 4. Monolithic Filter (T011)
    df, log = apply_monolithic_filter(df)
    log_exclusion(log, exclusion_log_path)
    
    if len(df) == 0:
        _logger.error("No data remaining after monolithic filter.")
        sys.exit(1)
    
    # 5. Normalize Units (T012)
    df, log = normalize_units(df)
    log_exclusion(log, exclusion_log_path)
    
    # 6. Major Element Filter (T013)
    df, log = apply_major_element_filter(df)
    log_exclusion(log, exclusion_log_path)
    
    # 7. Check Row Count (T015b)
    if len(df) < MIN_ROWS_FOR_CLEAN:
        _logger.error(f"Insufficient data after filtering ({len(df)} entries < {MIN_ROWS_FOR_CLEAN}).")
        sys.exit(1)
    
    # 8. ILR Transformation (T019)
    df = apply_ilr_transformation(df)
    
    # 9. Save (T015c)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    _logger.info(f"Cleaned and ILR-transformed data saved to {output_path}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Clean and transform alloy data.")
    parser.add_argument("--input", type=str, default="data/processed/merged_raw.parquet", help="Input parquet file")
    parser.add_argument("--output", type=str, default="data/processed/alloys_ilr.parquet", help="Output parquet file")
    parser.add_argument("--exclusion-log", type=str, default="data/logs/exclusion_log.txt", help="Exclusion log file")
    args = parser.parse_args()
    
    run_cleaning_pipeline(args.input, args.output, args.exclusion_log)

if __name__ == "__main__":
    main()
