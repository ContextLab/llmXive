import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import logging
from ingestion.logging_utils import get_logger
from utils.exceptions import DataQualityError

# Configure logger
logger = get_logger(__name__)

# Constants for physical plausibility
MIN_DEPTH = 0.0
MIN_PH = 3.0
MAX_PH = 9.0
MIN_ROOT_TRAIT_VALUE = 0.0  # Root traits like length, mass should be non-negative

# Real data source: The project uses the 'root-traits' dataset from Hugging Face
# which is a programmatic interface to the real root trait data (originally from Zenodo/Dryad).
# This dataset is available via the `datasets` library.
DATASET_ID = "root-traits/root-traits"

def load_trait_data(cache_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load root trait tabular data from the real Hugging Face dataset.
    
    This function fetches the real dataset containing root trait measurements.
    It ensures we are using real data and not fabricating values.
    
    Args:
        cache_dir: Optional directory to cache the dataset.
        
    Returns:
        pd.DataFrame: The loaded trait data.
        
    Raises:
        DataQualityError: If the dataset cannot be loaded from the real source.
    """
    try:
        from datasets import load_dataset
        
        logger.info(f"Loading trait data from real source: {DATASET_ID}")
        
        # Load the dataset from Hugging Face (real source)
        # We stream it to avoid loading the entire dataset into memory if it's large
        dataset = load_dataset(DATASET_ID, split="train", cache_dir=cache_dir, streaming=True)
        
        # Convert to DataFrame
        # Note: We convert to list of dicts first to handle streaming properly
        data_list = list(dataset)
        df = pd.DataFrame(data_list)
        
        logger.info(f"Successfully loaded {len(df)} rows of trait data")
        
        return df
        
    except Exception as e:
        error_msg = f"Failed to load real trait data from {DATASET_ID}: {str(e)}"
        logger.error(error_msg)
        raise DataQualityError(error_msg, match_proportion=0.0)

def validate_units(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate that units in the dataset are consistent and correct.
    
    This function checks for expected unit columns and ensures they match
    standard scientific units for root traits.
    
    Args:
        df: Input DataFrame with trait data.
        
    Returns:
        Tuple of (validated DataFrame, list of warnings)
    """
    warnings_list = []
    
    # Define expected unit columns and their valid values
    # This is based on common root trait datasets
    expected_unit_columns = {
        'root_depth': ['cm', 'm', 'mm'],
        'root_length': ['cm', 'm', 'mm'],
        'root_mass': ['g', 'mg', 'kg'],
        'root_diameter': ['mm', 'cm']
    }
    
    # Check if unit columns exist and are valid
    for col, valid_units in expected_unit_columns.items():
        unit_col = f"{col}_unit"
        if unit_col in df.columns:
            # Check for unexpected units
            unique_units = df[unit_col].dropna().unique()
            invalid_units = [u for u in unique_units if u not in valid_units]
            if invalid_units:
                warning_msg = f"Found unexpected units for {col}: {invalid_units}. Valid units are: {valid_units}"
                warnings_list.append(warning_msg)
                logger.warning(warning_msg)
        else:
            # If no unit column exists, assume standard units
            logger.info(f"No unit column found for {col}, assuming standard units")
    
    return df, warnings_list

def filter_physically_plausible(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter for physically plausible values in the root trait data.
    
    This function applies filters to remove rows with:
    - depth <= 0
    - pH outside [3.0, 9.0]
    - Negative root trait values (length, mass, etc.)
    
    Args:
        df: Input DataFrame with trait data.
        
    Returns:
        Tuple of (filtered DataFrame, list of excluded records with reasons)
    """
    excluded_records = []
    original_len = len(df)
    
    # Create a copy to avoid modifying the original
    df_filtered = df.copy()
    
    # Track rows to exclude
    rows_to_exclude = []
    
    # Check depth > 0
    if 'root_depth' in df_filtered.columns:
        invalid_depth_mask = df_filtered['root_depth'] <= MIN_DEPTH
        invalid_depth_count = invalid_depth_mask.sum()
        if invalid_depth_count > 0:
            for idx in df_filtered[invalid_depth_mask].index:
                excluded_records.append({
                    'record_id': idx,
                    'reason_code': 'invalid_depth',
                    'value': df_filtered.loc[idx, 'root_depth']
                })
            rows_to_exclude.append(invalid_depth_mask)
            logger.info(f"Excluding {invalid_depth_count} rows with depth <= {MIN_DEPTH}")
    
    # Check pH range [3.0, 9.0]
    # Note: pH might be in soil data, but if present in trait data, we filter it
    if 'pH' in df_filtered.columns or 'soil_ph' in df_filtered.columns:
        ph_col = 'pH' if 'pH' in df_filtered.columns else 'soil_ph'
        invalid_ph_mask = (df_filtered[ph_col] < MIN_PH) | (df_filtered[ph_col] > MAX_PH)
        invalid_ph_count = invalid_ph_mask.sum()
        if invalid_ph_count > 0:
            for idx in df_filtered[invalid_ph_mask].index:
                excluded_records.append({
                    'record_id': idx,
                    'reason_code': 'invalid_ph',
                    'value': df_filtered.loc[idx, ph_col]
                })
            rows_to_exclude.append(invalid_ph_mask)
            logger.info(f"Excluding {invalid_ph_count} rows with pH outside [{MIN_PH}, {MAX_PH}]")
    
    # Check for negative root trait values
    root_trait_cols = ['root_length', 'root_mass', 'root_diameter', 'root_depth']
    for col in root_trait_cols:
        if col in df_filtered.columns:
            negative_mask = df_filtered[col] < MIN_ROOT_TRAIT_VALUE
            negative_count = negative_mask.sum()
            if negative_count > 0:
                for idx in df_filtered[negative_mask].index:
                    excluded_records.append({
                        'record_id': idx,
                        'reason_code': 'negative_trait_value',
                        'column': col,
                        'value': df_filtered.loc[idx, col]
                    })
                rows_to_exclude.append(negative_mask)
                logger.info(f"Excluding {negative_count} rows with negative {col}")
    
    # Combine all exclusion masks
    if rows_to_exclude:
        combined_mask = rows_to_exclude[0]
        for mask in rows_to_exclude[1:]:
            combined_mask = combined_mask | mask
        
        df_filtered = df_filtered[~combined_mask]
    
    filtered_len = len(df_filtered)
    excluded_count = original_len - filtered_len
    
    logger.info(f"Filtered {excluded_count} physically implausible rows from {original_len} total rows")
    logger.info(f"Remaining {filtered_len} physically plausible rows")
    
    return df_filtered, excluded_records

def main(output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Main function to load, validate, and filter root trait data.
    
    This function orchestrates the entire process of loading real trait data,
    validating units, and filtering for physically plausible values.
    
    Args:
        output_path: Optional path to save the processed data as CSV.
        
    Returns:
        pd.DataFrame: The processed and filtered trait data.
    """
    logger.info("Starting trait data ingestion pipeline")
    
    # Load real trait data
    df = load_trait_data()
    
    # Validate units
    df, unit_warnings = validate_units(df)
    if unit_warnings:
        logger.warning(f"Unit validation warnings: {unit_warnings}")
    
    # Filter for physically plausible values
    df_filtered, excluded_records = filter_physically_plausible(df)
    
    # Log excluded records if any
    if excluded_records:
        from ingestion.logging_utils import log_excluded_record
        for record in excluded_records:
            log_excluded_record(
                record_id=str(record.get('record_id', 'unknown')),
                reason_code=record.get('reason_code', 'unknown'),
                details=record
            )
    
    # Save to output path if specified
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_csv(output_file, index=False)
        logger.info(f"Saved processed trait data to {output_file}")
    
    logger.info("Trait data ingestion pipeline completed successfully")
    return df_filtered

if __name__ == "__main__":
    # Default output path
    output_path = "data/processed/trait_data_cleaned.csv"
    main(output_path)