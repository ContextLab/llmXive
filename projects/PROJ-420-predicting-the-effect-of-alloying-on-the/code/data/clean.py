"""
Data Cleaning Pipeline (T010-T016).
Implements extraction, filtering, normalization, and validation.
"""
import sys
import logging
import argparse
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from periodictable import elements
from compositional import ilr
from logging_config import setup_logging, get_logger, log_operation
from config import get_config

# Constants
MAJOR_ELEMENTS = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
MIN_ROWS = 50

def log_exclusion(step: str, count: int, reason: str, log_path: Path) -> None:
    """Append exclusion record to the exclusion log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_path.exists()
    
    with open(log_path, 'a', newline='') as f:
        if not file_exists:
            f.write("step,count,reason\n")
        f.write(f"{step},{count},{reason}\n")

@log_operation("validate_raw_record_fields")
def validate_raw_record_fields(record: Dict[str, Any]) -> bool:
    """T010: Verify raw data contains required fields."""
    required = ['poisson_ratio', 'young_modulus', 'elements', 'composition']
    # Check for at least one representation of composition
    has_composition = 'composition' in record or 'elements' in record
    has_ym = 'young_modulus' in record
    has_pr = 'poisson_ratio' in record or 'nu' in record
    
    if not (has_composition and has_ym and has_pr):
        return False
    return True

@log_operation("normalize_raw_data")
def normalize_raw_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """T010: Normalize field names."""
    normalized = record.copy()
    
    # Map nu to poisson_ratio
    if 'nu' in normalized and 'poisson_ratio' not in normalized:
        normalized['poisson_ratio'] = normalized['nu']
    
    # Ensure composition is a dict
    if 'elements' in normalized and 'composition' not in normalized:
        normalized['composition'] = normalized['elements']
    
    return normalized

@log_operation("apply_monolithic_filter")
def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """T011: Filter for monolithic alloys."""
    # Priority: alloy_type -> is_composite -> composite_fraction
    mask = pd.Series([False] * len(df), index=df.index)
    
    if 'alloy_type' in df.columns:
        mask |= (df['alloy_type'] == 'monolithic')
    
    if 'is_composite' in df.columns:
        mask |= (df['is_composite'] == False)
    
    if 'composite_fraction' in df.columns:
        mask |= (df['composite_fraction'] == 0.0)
    
    # If none of the fields exist, exclude everything (mask remains False)
    if not mask.any():
        # Check if any of the columns exist to decide if we exclude due to missing info
        has_any_indicator = any(col in df.columns for col in ['alloy_type', 'is_composite', 'composite_fraction'])
        if not has_any_indicator:
            # No indicator fields exist, exclude all
            return df.iloc[0:0]
    
    return df[mask]

@log_operation("normalize_units")
def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """T012: Normalize units (GPa, at%)."""
    df = df.copy()
    
    # Convert Young's Modulus to GPa if in MPa
    if 'young_modulus' in df.columns:
        # Heuristic: if values are > 1000, assume MPa
        if df['young_modulus'].mean() > 1000:
            df['young_modulus'] = df['young_modulus'] / 1000.0
    
    # Convert composition from wt% to at%
    # Assume composition is a dict of element: fraction
    if 'composition' in df.columns:
        def convert_to_atpct(comp_dict):
            if not isinstance(comp_dict, dict):
                return comp_dict
            
            total_wt = sum(comp_dict.values())
            if total_wt == 0:
                return comp_dict
            
            moles = {}
            for elem, wt_frac in comp_dict.items():
                # Handle element name variations
                elem_name = str(elem).strip()
                try:
                    # Try to find element
                    el = elements.__dict__.get(elem_name)
                    if el is None:
                        # Try case insensitive
                        for k, v in elements.__dict__.items():
                            if k.lower() == elem_name.lower():
                                el = v
                                break
                    if el:
                        moles[elem_name] = (wt_frac / total_wt) / el.mass
                    else:
                        moles[elem_name] = 0
                except Exception:
                    moles[elem_name] = 0
            
            total_moles = sum(moles.values())
            if total_moles == 0:
                return comp_dict
            
            return {k: v / total_moles for k, v in moles.items()}
        
        df['composition_atpct'] = df['composition'].apply(convert_to_atpct)
    
    return df

@log_operation("apply_major_element_filter")
def apply_major_element_filter(df: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """T013: Exclude if major element sum < 0.95."""
    if 'composition_atpct' not in df.columns:
        return df.iloc[0:0]
    
    def check_major_sum(row):
        comp = row.get('composition_atpct', {})
        if not isinstance(comp, dict):
            return False
        
        major_sum = sum(comp.get(elem, 0.0) for elem in MAJOR_ELEMENTS)
        return major_sum >= 0.95
    
    mask = df.apply(check_major_sum, axis=1)
    excluded_count = (~mask).sum()
    if excluded_count > 0:
        log_exclusion("major_element_filter", int(excluded_count), "major_sum<0.95", log_path)
    
    return df[mask]

@log_operation("apply_independence_filter")
def apply_independence_filter(df: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """T014: Verify independence (measurement_method)."""
    if 'measurement_method' not in df.columns:
        # If missing, try to infer from source
        # For this implementation, we assume if missing, we exclude
        # unless we can infer from a 'source' column
        if 'source' in df.columns:
            def infer_method(row):
                src = str(row.get('source', '')).lower()
                if 'nist' in src:
                    return 'Ultrasonic' # NIST default assumption per plan
                if 'materialsproject' in src:
                    return 'Direct'
                return None
            df['measurement_method'] = df.apply(infer_method, axis=1)
        
        # Now check if we have a valid method
        def is_valid_method(val):
            if pd.isna(val):
                return False
            return bool(get_config().valid_measurement_methods.search(str(val)))
        
        mask = df['measurement_method'].apply(is_valid_method)
        excluded_count = (~mask).sum()
        if excluded_count > 0:
            log_exclusion("independence_filter", int(excluded_count), "inference_failed", log_path)
        return df[mask]
    
    # If column exists, validate
    def is_valid_method(val):
        if pd.isna(val):
            return False
        return bool(get_config().valid_measurement_methods.search(str(val)))
    
    mask = df['measurement_method'].apply(is_valid_method)
    excluded_count = (~mask).sum()
    if excluded_count > 0:
        log_exclusion("independence_filter", int(excluded_count), "invalid_method", log_path)
    
    return df[mask]

@log_operation("apply_ilr_transformation")
def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """T019: Apply ILR transformation to major elements."""
    if 'composition_atpct' not in df.columns:
        return df
    
    def transform_ilr(row):
        comp = row.get('composition_atpct', {})
        if not isinstance(comp, dict):
            return None
        
        # Extract values in fixed order
        values = [comp.get(elem, 0.0) for elem in MAJOR_ELEMENTS]
        
        # Handle zeros (add small epsilon to avoid log(0))
        values = [v if v > 0 else 1e-9 for v in values]
        
        try:
            # ILR requires input as array of length N
            ilr_res = ilr(np.array(values))
            return ilr_res
        except Exception:
            return None
    
    df['ilr_features'] = df.apply(transform_ilr, axis=1)
    df = df.dropna(subset=['ilr_features'])
    return df

@log_operation("run_cleaning_pipeline")
def run_cleaning_pipeline(input_path: Path, output_path: Path) -> pd.DataFrame:
    """T015: Orchestrate the full cleaning pipeline."""
    config = get_config()
    log_path = config.data_logs / "exclusion_log.txt"
    
    # Load data
    if input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix == '.json':
        df = pd.read_json(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_path.suffix}")
    
    # T010: Validate and Normalize
    valid_mask = df.apply(validate_raw_record_fields, axis=1)
    excluded_count = (~valid_mask).sum()
    if excluded_count > 0:
        log_exclusion("validation", int(excluded_count), "missing_fields", log_path)
    df = df[valid_mask]
    df = df.apply(normalize_raw_data, axis=1).apply(pd.Series)
    
    # T011: Monolithic Filter
    df = apply_monolithic_filter(df)
    
    # T012: Unit Normalization
    df = normalize_units(df)
    
    # T013: Major Element Filter
    df = apply_major_element_filter(df, log_path)
    
    # T014: Independence Filter
    df = apply_independence_filter(df, log_path)
    
    # T019: ILR Transformation
    df = apply_ilr_transformation(df)
    
    # T015: Final Validation
    final_count = len(df)
    if final_count < MIN_ROWS:
        print(f"Insufficient data after filtering ({final_count} entries)", file=sys.stderr)
        log_exclusion("final_validation", final_count, f"count<{MIN_ROWS}", log_path)
        sys.exit(1)
    
    # Prepare output
    # Flatten ILR features if needed
    if 'ilr_features' in df.columns:
        ilr_cols = df['ilr_features'].apply(pd.Series)
        ilr_cols.columns = [f'ilr_{i}' for i in range(ilr_cols.shape[1])]
        df = pd.concat([df.drop('ilr_features', axis=1), ilr_cols], axis=1)
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print(f"Saved {final_count} records to {output_path}")
    return df

def main():
    parser = argparse.ArgumentParser(description="Clean alloy data.")
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    parser.add_argument('--log-level', type=str, default="INFO")
    args = parser.parse_args()
    
    setup_logging(level=args.log_level)
    logger = get_logger()
    logger.log("pipeline_start", input=args.input, output=args.output)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.log("error", message=f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        run_cleaning_pipeline(input_path, output_path)
    except SystemExit as e:
        if e.code != 0:
            sys.exit(e.code)
    except Exception as e:
        logger.log("error", message=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
