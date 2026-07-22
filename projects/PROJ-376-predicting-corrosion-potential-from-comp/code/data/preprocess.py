import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Local imports matching API surface
from utils.logging import get_logger, log_message
from utils.config import get_log_path, get_processed_data_path, get_path
from utils.exceptions import DataInsufficientError
from utils.validation import validate_non_nulls, validate_schema_structure, filter_null_records
from data.models import AlloyRecord, EnvironmentRecord, CorrosionMeasurement

logger = get_logger(__name__)

# Constants for pH filtering
MIN_PH = 0.0
MAX_PH = 14.0
EXTREME_PH_THRESHOLD = 1.0  # pH < 1.0 or pH > 13.0 considered extreme

def load_raw_dataset(raw_data_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the raw dataset from the downloaded NIST archive."""
    if raw_data_path is None:
        raw_data_path = get_path("data", "raw", "nist_corrosion_database.csv")
    
    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"Raw dataset not found at {raw_data_path}. "
                              "Please run download_nist.py first.")
    
    logger.info(f"Loading raw dataset from {raw_data_path}")
    df = pd.read_csv(raw_data_path)
    logger.info(f"Loaded {len(df)} records from raw dataset")
    return df

def filter_missing_critical_fields(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Filter out records missing critical fields (pH, temperature, corrosion_potential).
    
    Returns:
        Tuple of (filtered dataframe, count of missing pH, count of missing temp)
    """
    logger.info("Filtering records with missing critical fields...")
    
    original_count = len(df)
    
    # Track missing counts before filtering
    missing_ph = df['pH'].isna().sum()
    missing_temp = df['temperature'].isna().sum()
    missing_corr = df['corrosion_potential'].isna().sum()
    
    logger.info(f"Missing pH: {missing_ph}, Missing temperature: {missing_temp}, "
               f"Missing corrosion_potential: {missing_corr}")
    
    # Log diagnostic information for excluded records
    log_path = get_log_path("pipeline.log")
    with open(log_path, 'a') as log_file:
        log_file.write(f"\n[DIAGNOSTIC] Missing critical fields analysis:\n")
        log_file.write(f"  Total records: {original_count}\n")
        log_file.write(f"  Missing pH: {missing_ph}\n")
        log_file.write(f"  Missing temperature: {missing_temp}\n")
        log_file.write(f"  Missing corrosion_potential: {missing_corr}\n")
        
        # Log specific records with missing pH
        if missing_ph > 0:
            missing_ph_indices = df[df['pH'].isna()].index.tolist()
            log_file.write(f"  Indices with missing pH: {missing_ph_indices[:10]}{'...' if len(missing_ph_indices) > 10 else ''}\n")
    
    # Filter out records with missing critical fields
    df_filtered = df.dropna(subset=['pH', 'temperature', 'corrosion_potential'])
    
    filtered_count = len(df_filtered)
    removed_count = original_count - filtered_count
    
    logger.info(f"Filtered {removed_count} records with missing critical fields. "
               f"Remaining: {filtered_count}")
    
    return df_filtered, int(missing_ph), int(missing_temp)

def encode_weight_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode weight fractions for alloy composition columns.
    
    Assumes composition columns are named with element symbols (e.g., 'Fe', 'Cr', 'Ni').
    """
    logger.info("Encoding weight fractions...")
    
    # Identify composition columns (typically element symbols)
    composition_cols = [col for col in df.columns if col in ['Fe', 'Cr', 'Ni', 'Mn', 'C', 'Si', 'Mo', 'Cu', 'Ti', 'Al', 'V', 'Nb', 'W', 'Co']]
    
    if not composition_cols:
        logger.warning("No composition columns found. Skipping weight fraction encoding.")
        return df
    
    # Ensure all weight fractions are non-negative and sum to <= 100 (or 1.0)
    for col in composition_cols:
        df[col] = df[col].clip(lower=0)
    
    logger.info(f"Encoded {len(composition_cols)} composition columns")
    return df

def detect_and_remove_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Detect and remove outliers using IQR method for pH and temperature.
    
    Returns:
        Tuple of (filtered dataframe, dict of outlier counts by field)
    """
    logger.info("Detecting and removing outliers...")
    
    original_count = len(df)
    outlier_counts = {}
    
    # Log diagnostic information for extreme pH values
    log_path = get_log_path("pipeline.log")
    
    # Check for extreme pH values (outside 0-14 or extremely acidic/basic)
    extreme_ph_mask = (df['pH'] < MIN_PH) | (df['pH'] > MAX_PH) | \
                    (df['pH'] < EXTREME_PH_THRESHOLD) | (df['pH'] > (MAX_PH - EXTREME_PH_THRESHOLD))
    
    extreme_ph_count = extreme_ph_mask.sum()
    outlier_counts['extreme_ph'] = int(extreme_ph_count)
    
    if extreme_ph_count > 0:
        extreme_ph_indices = df[extreme_ph_mask].index.tolist()
        extreme_ph_values = df.loc[extreme_ph_mask, 'pH'].tolist()
        
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n[DIAGNOSTIC] Extreme pH values detected:\n")
            log_file.write(f"  Total extreme pH records: {extreme_ph_count}\n")
            log_file.write(f"  pH values: {extreme_ph_values[:20]}{'...' if len(extreme_ph_values) > 20 else ''}\n")
            log_file.write(f"  Indices: {extreme_ph_indices[:20]}{'...' if len(extreme_ph_indices) > 20 else ''}\n")
        
        logger.warning(f"Found {extreme_ph_count} records with extreme pH values")
    
    # Check for missing pH values (should already be filtered, but double-check)
    missing_ph_mask = df['pH'].isna()
    missing_ph_count = missing_ph_mask.sum()
    outlier_counts['missing_ph'] = int(missing_ph_count)
    
    if missing_ph_count > 0:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n[DIAGNOSTIC] Records with missing pH (post-filtering check):\n")
            log_file.write(f"  Count: {missing_ph_count}\n")
        logger.warning(f"Found {missing_ph_count} records with missing pH after filtering")
    
    # Remove extreme pH records
    df_filtered = df[~extreme_ph_mask]
    
    # Apply IQR-based outlier detection for temperature
    temp_q1 = df_filtered['temperature'].quantile(0.25)
    temp_q3 = df_filtered['temperature'].quantile(0.75)
    temp_iqr = temp_q3 - temp_q1
    temp_lower = temp_q1 - 1.5 * temp_iqr
    temp_upper = temp_q3 + 1.5 * temp_iqr
    
    temp_outlier_mask = (df_filtered['temperature'] < temp_lower) | \
                       (df_filtered['temperature'] > temp_upper)
    temp_outlier_count = temp_outlier_mask.sum()
    outlier_counts['temperature_outliers'] = int(temp_outlier_count)
    
    if temp_outlier_count > 0:
        with open(log_path, 'a') as log_file:
            log_file.write(f"\n[DIAGNOSTIC] Temperature outliers (IQR method):\n")
            log_file.write(f"  Count: {temp_outlier_count}\n")
            log_file.write(f"  Range: [{temp_lower:.2f}, {temp_upper:.2f}]\n")
        logger.warning(f"Found {temp_outlier_count} temperature outliers")
    
    df_filtered = df_filtered[~temp_outlier_mask]
    
    final_count = len(df_filtered)
    removed_count = original_count - final_count
    
    logger.info(f"Removed {removed_count} outliers. Remaining: {final_count}")
    
    return df_filtered, outlier_counts

def validate_processed_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the processed dataset meets quality requirements.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Validating processed dataset...")
    
    validation_results = {
        'total_records': len(df),
        'has_nulls': {},
        'pH_range': {},
        'temperature_range': {},
        'is_valid': True
    }
    
    # Check for nulls in critical fields
    critical_fields = ['pH', 'temperature', 'corrosion_potential', 'specific_alloy_designation_id']
    for field in critical_fields:
        null_count = df[field].isna().sum()
        validation_results['has_nulls'][field] = int(null_count)
        if null_count > 0:
            validation_results['is_valid'] = False
            logger.error(f"Found {null_count} null values in critical field: {field}")
    
    # Check pH range
    validation_results['pH_range'] = {
        'min': float(df['pH'].min()),
        'max': float(df['pH'].max())
    }
    
    # Check temperature range
    validation_results['temperature_range'] = {
        'min': float(df['temperature'].min()),
        'max': float(df['temperature'].max())
    }
    
    # Log validation results
    log_path = get_log_path("pipeline.log")
    with open(log_path, 'a') as log_file:
        log_file.write(f"\n[VALIDATION] Processed dataset validation results:\n")
        for key, value in validation_results.items():
            if key != 'is_valid':
                log_file.write(f"  {key}: {value}\n")
        log_file.write(f"  Overall valid: {validation_results['is_valid']}\n")
    
    if not validation_results['is_valid']:
        raise DataInsufficientError("Processed dataset contains null values in critical fields")
    
    logger.info("Dataset validation passed")
    return validation_results

def save_processed_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Save the processed dataset to parquet format."""
    if output_path is None:
        output_path = get_processed_data_path("corrosion_dataset.parquet")
    
    logger.info(f"Saving processed dataset to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved {len(df)} records to {output_path}")
    return output_path

def main():
    """Main pipeline execution function."""
    logger.info("Starting data preprocessing pipeline...")
    
    # Load raw dataset
    df_raw = load_raw_dataset()
    
    # Filter missing critical fields
    df_filtered, missing_ph_count, missing_temp_count = filter_missing_critical_fields(df_raw)
    
    # Encode weight fractions
    df_encoded = encode_weight_fractions(df_filtered)
    
    # Detect and remove outliers
    df_clean, outlier_counts = detect_and_remove_outliers(df_encoded)
    
    # Validate processed data
    validation_results = validate_processed_data(df_clean)
    
    # Save processed dataset
    output_path = save_processed_dataset(df_clean)
    
    # Final summary
    logger.info("Preprocessing pipeline completed successfully")
    logger.info(f"Final dataset: {len(df_clean)} records")
    logger.info(f"Output saved to: {output_path}")
    
    # Log final diagnostic summary
    log_path = get_log_path("pipeline.log")
    with open(log_path, 'a') as log_file:
        log_file.write(f"\n[SUMMARY] Preprocessing pipeline completed:\n")
        log_file.write(f"  Initial records: {len(df_raw)}\n")
        log_file.write(f"  Records with missing pH: {missing_ph_count}\n")
        log_file.write(f"  Records with missing temperature: {missing_temp_count}\n")
        log_file.write(f"  Extreme pH records removed: {outlier_counts.get('extreme_ph', 0)}\n")
        log_file.write(f"  Temperature outliers removed: {outlier_counts.get('temperature_outliers', 0)}\n")
        log_file.write(f"  Final records: {len(df_clean)}\n")
        log_file.write(f"  Output file: {output_path}\n")
    
    return df_clean, output_path

if __name__ == "__main__":
    main()