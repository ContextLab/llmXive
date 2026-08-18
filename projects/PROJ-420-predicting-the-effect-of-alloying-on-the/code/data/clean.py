"""Data cleaning pipeline for aluminum alloy Poisson's ratio prediction."""
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
from compositional import ilr
from periodictable import elements
import joblib

from logging_config import setup_logging, get_logger
from config import get_config


def log_exclusion(step: str, count: int, reason: str, log_file: Optional[Path] = None) -> None:
    """Log exclusion records to a CSV file.
    
    Args:
        step: The filtering step name
        count: Number of records excluded
        reason: Reason for exclusion
        log_file: Path to the exclusion log file
    """
    if log_file is None:
        config = get_config()
        log_file = config.data_logs / "exclusion_log.txt"
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to log file
    file_exists = log_file.exists()
    with open(log_file, 'a') as f:
        if not file_exists:
            f.write("step,count,reason\n")
        f.write(f"{step},{count},{reason}\n")


def validate_raw_record_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that raw data contains required fields at schema level.
    
    Args:
        df: Raw DataFrame from data sources
        
    Returns:
        DataFrame with validated structure
        
    Raises:
        ValueError: If required fields are missing from schema
    """
    required_fields = ['poisson_ratio', 'young_modulus', 'composition', 'measurement_method']
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        raise ValueError(f"Missing required fields in raw data: {missing_fields}")
    
    return df


def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for monolithic alloys only.
    
    Definition: alloy_type == 'monolithic' OR is_composite == False OR composite_fraction == 0.0
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    initial_count = len(df)
    
    # Priority: Check alloy_type first, then is_composite, then composite_fraction
    mask = pd.Series([False] * len(df), index=df.index)
    
    if 'alloy_type' in df.columns:
        mask |= (df['alloy_type'] == 'monolithic')
    
    if 'is_composite' in df.columns:
        mask |= (df['is_composite'] == False)
    
    if 'composite_fraction' in df.columns:
        mask |= (df['composite_fraction'] == 0.0)
    
    # If none of the fields exist, exclude all records
    if not mask.any():
        # Check if any of the fields exist at all
        has_any_field = any(field in df.columns for field in ['alloy_type', 'is_composite', 'composite_fraction'])
        if has_any_field:
            filtered_df = df[mask]
            excluded_count = initial_count - len(filtered_df)
            if excluded_count > 0:
                log_exclusion("monolithic_filter", excluded_count, "Non-monolithic alloy")
            return filtered_df
        else:
            # No fields exist, exclude all
            log_exclusion("monolithic_filter", initial_count, "No monolithic/composite fields found")
            return pd.DataFrame(columns=df.columns)
    
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    if excluded_count > 0:
        log_exclusion("monolithic_filter", excluded_count, "Non-monolithic alloy")
    
    return filtered_df


def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units for composition and Young's modulus.
    
    - Composition: Convert wt% to at% if needed
    - Young's modulus: Convert to GPa if in MPa
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with normalized units
    """
    df = df.copy()
    
    # Handle Young's modulus unit conversion
    if 'young_modulus_unit' in df.columns:
        # Convert MPa to GPa
        mask_mp = df['young_modulus_unit'].str.upper().str.contains('MPA', na=False)
        df.loc[mask_mp, 'young_modulus'] = df.loc[mask_mp, 'young_modulus'] / 1000.0
        df.loc[mask_mp, 'young_modulus_unit'] = 'GPa'
    
    # Handle composition unit conversion
    if 'composition_unit' in df.columns:
        mask_wt = df['composition_unit'].str.upper().str.contains('WT', na=False)
        if mask_wt.any():
            # Convert wt% to at% using atomic weights
            for idx in df[mask_wt].index:
                composition = df.loc[idx, 'composition']
                if isinstance(composition, dict):
                    total_weight = sum(composition.values())
                    atomic_fractions = {}
                    for element, weight in composition.items():
                        try:
                            atomic_weight = getattr(elements, element.strip()).atomic
                            atomic_fractions[element] = (weight / atomic_weight)
                        except (AttributeError, KeyError):
                            atomic_fractions[element] = 0.0
                    
                    total_atoms = sum(atomic_fractions.values())
                    if total_atoms > 0:
                        atomic_fractions = {k: v / total_atoms for k, v in atomic_fractions.items()}
                    
                    df.loc[idx, 'composition'] = atomic_fractions
            df.loc[mask_wt, 'composition_unit'] = 'at%'
    
    return df


def apply_major_element_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Exclude entries where major element sum < 0.95.
    
    Major elements: Cu, Mg, Si, Zn, Mn
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    initial_count = len(df)
    major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    def check_major_sum(row):
        composition = row.get('composition', {})
        if isinstance(composition, dict):
            major_sum = sum(composition.get(elem, 0.0) for elem in major_elements)
            return major_sum >= 0.95
        return False
    
    mask = df.apply(check_major_sum, axis=1)
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        log_exclusion("major_element_filter", excluded_count, "Major element sum < 0.95")
    
    return filtered_df


def apply_independence_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter records based on measurement_method availability.
    
    If measurement_method is missing/null, attempt inference from metadata.
    If inference fails, exclude the record.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    initial_count = len(df)
    inference_keywords = ['Ultrasonic', 'Direct', 'Resonant', 'Impulse']
    
    def process_measurement_method(row):
        method = row.get('measurement_method')
        
        # If method exists and is not null, return as-is
        if pd.notna(method) and method:
            return method, False
        
        # Attempt inference from metadata
        metadata = row.get('metadata', {})
        source = row.get('source', '')
        
        # Check various metadata fields for keywords
        for field in ['method', 'technique', 'measurement_type', 'source_method']:
            if field in metadata:
                value = str(metadata[field])
                for keyword in inference_keywords:
                    if keyword.lower() in value.lower():
                        return keyword, True
        
        # Check source field for keywords
        if source:
            for keyword in inference_keywords:
                if keyword.lower() in str(source).lower():
                    return keyword, True
        
        # Inference failed
        return None, False
    
    # Process each row
    new_methods = []
    excluded_rows = []
    
    for idx, row in df.iterrows():
        method, inferred = process_measurement_method(row)
        if method is None:
            excluded_rows.append(idx)
        else:
            new_methods.append(method)
            if inferred:
                df.at[idx, 'measurement_method'] = method
                df.at[idx, 'measurement_method_inferred'] = True
    
    if excluded_rows:
        df = df.drop(index=excluded_rows)
        log_exclusion("independence_filter", len(excluded_rows), "missing_measurement_method")
    
    return df


def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Apply isometric log-ratio transformation to composition data.
    
    Args:
        df: Input DataFrame with composition column
        
    Returns:
        DataFrame with ILR-transformed features
    """
    df = df.copy()
    element_order = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    def transform_composition(row):
        composition = row.get('composition', {})
        if not isinstance(composition, dict):
            return None
        
        # Extract values for ILR transformation
        values = [composition.get(elem, 0.0) for elem in element_order]
        
        # Check for zeros (ILR requires positive values)
        if any(v <= 0 for v in values):
            # Add small pseudocount
            values = [max(v, 1e-10) for v in values]
        
        return ilr(np.array(values))
    
    # Apply ILR transformation
    ilr_results = df.apply(transform_composition, axis=1)
    ilr_valid = ilr_results.notna()
    
    if not ilr_valid.all():
        excluded_count = (~ilr_valid).sum()
        log_exclusion("ilr_transformation", excluded_count, "Invalid composition for ILR")
        df = df[ilr_valid]
        ilr_results = ilr_results[ilr_valid]
    
    # Convert ILR results to columns
    ilr_df = pd.DataFrame(ilr_results.tolist(), index=df.index, columns=[f'ilr_{i}' for i in range(len(element_order) - 1)])
    df = pd.concat([df, ilr_df], axis=1)
    
    return df


def run_cleaning_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> pd.DataFrame:
    """Run the complete data cleaning pipeline.
    
    Steps:
    1. Validate raw record fields (T010)
    2. Apply monolithic filter (T011)
    3. Normalize units (T012)
    4. Apply major element filter (T013)
    5. Apply independence filter with inference (T014)
    6. Log all exclusions (T016)
    7. Final validation and output (T015)
    
    Args:
        input_path: Path to raw data file
        output_path: Path for cleaned output file
        
    Returns:
        Cleaned DataFrame
    """
    config = get_config()
    logger = get_logger()
    
    # Set default paths
    if input_path is None:
        input_path = config.data_raw / "alloys_raw.parquet"
    if output_path is None:
        output_path = config.data_processed / "alloys_clean.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    config.data_logs.mkdir(parents=True, exist_ok=True)
    
    # Load raw data
    logger.log("load_raw_data", path=str(input_path))
    df = pd.read_parquet(input_path)
    
    initial_count = len(df)
    
    # Step 1: Validate raw record fields
    logger.log("validate_raw_fields")
    df = validate_raw_record_fields(df)
    
    # Step 2: Apply monolithic filter
    logger.log("apply_monolithic_filter")
    df = apply_monolithic_filter(df)
    
    # Step 3: Normalize units
    logger.log("normalize_units")
    df = normalize_units(df)
    
    # Step 4: Apply major element filter
    logger.log("apply_major_element_filter")
    df = apply_major_element_filter(df)
    
    # Step 5: Apply independence filter with inference
    logger.log("apply_independence_filter")
    df = apply_independence_filter(df)
    
    # Step 6: Log all exclusions (T016 is invoked automatically by log_exclusion calls above)
    
    # Step 7: Final validation and output (T015)
    final_count = len(df)
    
    # Read exclusion log and count
    exclusion_log_path = config.data_logs / "exclusion_log.txt"
    if exclusion_log_path.exists():
        exclusion_df = pd.read_csv(exclusion_log_path)
        total_excluded = exclusion_df['count'].sum()
        logger.log("exclusion_summary", total_excluded=total_excluded, final_count=final_count)
    
    # Check minimum row count
    if final_count < 50:
        error_msg = f"Insufficient data after filtering (<50 entries): {final_count}"
        logger.log("pipeline_halt", error=error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # Save cleaned dataset
    logger.log("save_cleaned_data", path=str(output_path), count=final_count)
    df.to_parquet(output_path, index=False)
    
    print(f"Cleaning complete: {final_count} records saved to {output_path}")
    return df


def main():
    """Main entry point for data cleaning."""
    parser = argparse.ArgumentParser(description="Clean aluminum alloy data")
    parser.add_argument("--input", type=str, help="Input data file path")
    parser.add_argument("--output", type=str, help="Output data file path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Run pipeline
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    run_cleaning_pipeline(input_path, output_path)


if __name__ == "__main__":
    main()
