"""
Data cleaning and validation pipeline for alloy data.
Implements T010-T016 logic.
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
from compositional import ilr, ilr_inv
from periodictable import elements
from logging_config import setup_logging, get_logger
from config import get_config

logger = get_logger()
config = get_config()

def log_exclusion(step: str, count: int, reason: str) -> None:
    """Append exclusion records to data/logs/exclusion_log.txt."""
    log_path = config.data_logs_dir / "exclusion_log.txt"
    file_exists = log_path.exists()
    
    with open(log_path, "a") as f:
        if not file_exists:
            f.write("step,count,reason\n")
        f.write(f"{step},{count},{reason}\n")

def validate_raw_record_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Verify the raw data contains all required fields at schema level."""
    required_fields = ["poisson_ratio", "young_modulus", "composition", "measurement_method"]
    
    # Check if columns exist in the dataframe
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        raise ValueError(f"Missing required fields in raw data: {missing_fields}")
    
    return df

def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for monolithic alloys only."""
    initial_count = len(df)
    
    # Priority: alloy_type -> is_composite -> composite_fraction
    if "alloy_type" in df.columns:
        df = df[df["alloy_type"] == "monolithic"]
    
    if "is_composite" in df.columns:
        df = df[df["is_composite"] == False]
    
    if "composite_fraction" in df.columns:
        df = df[df["composite_fraction"] == 0.0]
    
    # If neither field exists, exclude all (but we assume at least one exists from T007)
    if len(df) == 0 and initial_count > 0:
        logger.log("monolithic_filter", reason="No monolithic records found")
    
    log_exclusion("monolithic_filter", initial_count - len(df), "non-monolithic")
    return df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert units: young_modulus to GPa, composition to at%."""
    # Convert young_modulus from MPa to GPa if needed
    if "young_modulus" in df.columns:
        # Assume values > 1000 are in MPa
        df["young_modulus"] = df["young_modulus"].apply(lambda x: x / 1000.0 if x > 1000 else x)
    
    # Convert composition from wt% to at%
    if "composition" in df.columns:
        def wt_to_at(comp_dict):
            if not isinstance(comp_dict, dict):
                return comp_dict
            
            total_wt = sum(comp_dict.values())
            if total_wt == 0:
                return comp_dict
            
            at_dict = {}
            for elem, wt in comp_dict.items():
                try:
                    atomic_weight = getattr(elements, elem.lower(), None)
                    if atomic_weight:
                        at_dict[elem] = (wt / atomic_weight)
                    else:
                        at_dict[elem] = wt  # Keep as is if unknown
                except:
                    at_dict[elem] = wt
            
            total_at = sum(at_dict.values())
            if total_at > 0:
                for elem in at_dict:
                    at_dict[elem] = at_dict[elem] / total_at
            
            return at_dict
        
        df["composition"] = df["composition"].apply(wt_to_at)
    
    return df

def apply_major_element_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Exclude entries where major element sum < 0.95."""
    initial_count = len(df)
    major_elements = ["Cu", "Mg", "Si", "Zn", "Mn"]
    
    def check_major_sum(comp_dict):
        if not isinstance(comp_dict, dict):
            return False
        major_sum = sum(comp_dict.get(elem, 0.0) for elem in major_elements)
        return major_sum >= config.MIN_MAJOR_ELEMENT_SUM
    
    df = df[df["composition"].apply(check_major_sum)]
    
    log_exclusion("major_element_filter", initial_count - len(df), "major_sum < 0.95")
    return df

def apply_independence_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Exclude records with missing or invalid measurement_method."""
    initial_count = len(df)
    
    if "measurement_method" not in df.columns:
        # If column doesn't exist, exclude all
        log_exclusion("independence_filter", initial_count, "missing_measurement_method")
        return pd.DataFrame(columns=df.columns)
    
    # Check for null/missing values
    mask = df["measurement_method"].notna() & (df["measurement_method"] != "")
    df_filtered = df[mask]
    
    excluded_count = initial_count - len(df_filtered)
    if excluded_count > 0:
        log_exclusion("independence_filter", excluded_count, "missing_measurement_method")
    
    # Validate values against regex
    valid_mask = df_filtered["measurement_method"].apply(
        lambda x: bool(config.VALID_MEASUREMENT_METHODS.search(str(x)))
    )
    df_filtered = df_filtered[valid_mask]
    
    invalid_count = len(df) - len(df_filtered) - excluded_count
    if invalid_count > 0:
        log_exclusion("independence_filter", invalid_count, "invalid_measurement_method")
    
    return df_filtered

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ILR transformation to composition."""
    elements_order = ["Cu", "Mg", "Si", "Zn", "Mn"]
    
    def transform_composition(comp_dict):
        if not isinstance(comp_dict, dict):
            return {f"ilr_{i}": 0.0 for i in range(len(elements_order))}
        
        # Extract values in order, filling missing with 0
        values = [comp_dict.get(elem, 0.0) for elem in elements_order]
        
        # Avoid zero values for ILR
        values = [max(v, 1e-10) for v in values]
        
        try:
            ilr_result = ilr(values)
            return {f"ilr_{i}": float(val) for i, val in enumerate(ilr_result)}
        except Exception as e:
            logger.log("ilr_error", message=str(e))
            return {f"ilr_{i}": 0.0 for i in range(len(elements_order))}
    
    ilr_columns = {f"ilr_{i}": [] for i in range(len(elements_order))}
    
    for _, row in df.iterrows():
        result = transform_composition(row.get("composition", {}))
        for key, val in result.items():
            ilr_columns[key].append(val)
    
    for key, vals in ilr_columns.items():
        df[key] = vals
    
    return df

def run_cleaning_pipeline(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Run the full cleaning pipeline."""
    logger.log("cleaning_pipeline_start", input=str(input_path), output=str(output_path))
    
    # Load raw data
    if input_path.suffix == ".json":
        df = pd.read_json(input_path)
    elif input_path.suffix == ".csv":
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    # Step 1: Schema validation (T010)
    df = validate_raw_record_fields(df)
    
    # Step 2: Monolithic filter (T011)
    df = apply_monolithic_filter(df)
    
    # Step 3: Unit normalization (T012)
    df = normalize_units(df)
    
    # Step 4: Major element filter (T013)
    df = apply_major_element_filter(df)
    
    # Step 5: Independence filter (T014)
    df = apply_independence_filter(df)
    
    # Step 6: ILR transformation (T019)
    df = apply_ilr_transformation(df)
    
    # Step 7: Final validation and logging (T015, T016)
    final_count = len(df)
    
    # Read exclusion log to verify
    log_path = config.data_logs_dir / "exclusion_log.txt"
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    logger.log("exclusion_record", step=parts[0], count=parts[1], reason=parts[2])
    
    # Check minimum row count
    if final_count < config.MIN_ROWS_AFTER_FILTERING:
        logger.log("insufficient_data", count=final_count, threshold=config.MIN_ROWS_AFTER_FILTERING)
        raise SystemExit(f"Insufficient data after filtering ({final_count} entries, need >= {config.MIN_ROWS_AFTER_FILTERING})")
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.log("cleaning_pipeline_complete", rows=final_count, output=str(output_path))
    return df

def main():
    parser = argparse.ArgumentParser(description="Clean and validate alloy data.")
    parser.add_argument('--input', type=str, required=True, help="Path to raw data file")
    parser.add_argument('--output', type=str, required=True, help="Path to output parquet file")
    parser.add_argument('--log-level', type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.log("input_not_found", path=str(input_path))
        sys.exit(1)
    
    try:
        run_cleaning_pipeline(input_path, output_path)
        logger.log("pipeline_success")
    except SystemExit as e:
        if e.code != 0:
            sys.exit(e.code)
    except Exception as e:
        logger.log("pipeline_error", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
