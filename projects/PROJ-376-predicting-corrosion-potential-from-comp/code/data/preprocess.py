import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from utils.config import get_config, get_path, get_log_path
from utils.exceptions import DataInsufficientError
from utils.logging import get_logger, log_message
from utils.validation import validate_non_nulls, filter_null_records
from data.models import AlloyRecord, EnvironmentRecord, CorrosionMeasurement

# Constants for pH filtering
MIN_PH = 0.0
MAX_PH = 14.0
MIN_RECORDS = 500

def load_raw_dataset(raw_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the raw NIST-IR-8200 dataset from disk.
    Expects a CSV or Parquet file at the configured raw data path.
    """
    config = get_config()
    if raw_path is None:
        raw_path = Path(config.get('paths', {}).get('raw_data', 'data/raw/corrosion_raw.csv'))
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}. Run download_nist.py first.")
    
    logger = get_logger("preprocess")
    logger.info(f"Loading raw dataset from {raw_path}")
    
    if str(raw_path).endswith('.parquet'):
        return pd.read_parquet(raw_path)
    else:
        return pd.read_csv(raw_path)

def filter_missing_critical_fields(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Filter out records with missing critical fields (pH, Temperature, Corrosion Rate).
    Logs details of excluded records to pipeline.log.
    
    Returns:
        Tuple of (filtered_df, count_excluded, list_of_exclusion_reasons)
    """
    if logger is None:
        logger = get_logger("preprocess")
    
    critical_fields = ['pH', 'temperature_celsius', 'corrosion_rate_mpy']
    missing_mask = pd.DataFrame(False, index=df.index, columns=critical_fields)
    
    for field in critical_fields:
        if field in df.columns:
            missing_mask[field] = df[field].isna()
        else:
            # If column missing entirely, all rows are "missing" for that field
            missing_mask[field] = True
    
    # Any row with at least one missing critical field is excluded
    exclusion_mask = missing_mask.any(axis=1)
    excluded_indices = df.index[exclusion_mask].tolist()
    
    # Generate detailed exclusion reasons for logging
    exclusion_reasons = []
    for idx in excluded_indices:
        row = df.loc[idx]
        reasons = []
        for field in critical_fields:
            if field in missing_mask.columns and missing_mask.loc[idx, field]:
                reasons.append(f"missing_{field}")
        exclusion_reasons.append(f"Record {idx}: {', '.join(reasons)}")
    
    # Log excluded records to pipeline.log
    log_path = get_log_path("pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as log_file:
        log_file.write(f"\n--- Exclusion Report: Missing Critical Fields ---\n")
        log_file.write(f"Total records excluded: {len(excluded_indices)}\n")
        for reason in exclusion_reasons:
            log_file.write(f"{reason}\n")
        log_file.write(f"-----------------------------------------------\n")
    
    filtered_df = df[~exclusion_mask].reset_index(drop=True)
    return filtered_df, len(excluded_indices), exclusion_reasons

def encode_weight_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode alloy composition columns as weight fractions.
    Assumes columns named like 'Fe_wt', 'Cr_wt', 'Ni_wt', etc.
    Normalizes to sum to 1.0 if necessary.
    """
    composition_cols = [col for col in df.columns if col.endswith('_wt')]
    
    if not composition_cols:
        return df
    
    # Normalize each row's composition to sum to 1.0
    # This handles cases where raw data might not be perfectly normalized
    df[composition_cols] = df[composition_cols].div(
        df[composition_cols].sum(axis=1), axis=0
    ).fillna(0)
    
    return df

def detect_and_remove_outliers(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Detect and remove outliers based on extreme pH values (pH < 0 or pH > 14).
    Logs details of excluded records to pipeline.log.
    
    Returns:
        Tuple of (filtered_df, count_excluded, list_of_exclusion_reasons)
    """
    if logger is None:
        logger = get_logger("preprocess")
    
    if 'pH' not in df.columns:
        logger.warning("pH column not found, skipping outlier detection")
        return df, 0, []
    
    # Identify extreme pH values
    extreme_mask = (df['pH'] < MIN_PH) | (df['pH'] > MAX_PH)
    excluded_indices = df.index[extreme_mask].tolist()
    
    # Generate detailed exclusion reasons for logging
    exclusion_reasons = []
    for idx in excluded_indices:
        ph_val = df.loc[idx, 'pH']
        if ph_val < MIN_PH:
            exclusion_reasons.append(f"Record {idx}: pH={ph_val} (below {MIN_PH})")
        else:
            exclusion_reasons.append(f"Record {idx}: pH={ph_val} (above {MAX_PH})")
    
    # Log excluded records to pipeline.log
    log_path = get_log_path("pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as log_file:
        log_file.write(f"\n--- Exclusion Report: Extreme pH Outliers ---\n")
        log_file.write(f"Total records excluded: {len(excluded_indices)}\n")
        for reason in exclusion_reasons:
            log_file.write(f"{reason}\n")
        log_file.write(f"-----------------------------------------------\n")
    
    filtered_df = df[~extreme_mask].reset_index(drop=True)
    return filtered_df, len(excluded_indices), exclusion_reasons

def validate_processed_data(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that processed data meets minimum requirements.
    Checks record count >= 500 and no nulls in critical fields.
    """
    if logger is None:
        logger = get_logger("preprocess")
    
    if len(df) < MIN_RECORDS:
        logger.error(f"Processed dataset has only {len(df)} records, minimum required is {MIN_RECORDS}")
        # Log to diagnostics
        diag_path = get_path('diagnostics/count_report.txt')
        diag_path.parent.mkdir(parents=True, exist_ok=True)
        with open(diag_path, 'w') as f:
            f.write(f"Data Insufficient: {len(df)} records found, {MIN_RECORDS} required.\n")
        raise DataInsufficientError(f"Processed dataset has only {len(df)} records, minimum required is {MIN_RECORDS}")
    
    # Check for nulls in critical fields
    critical_fields = ['pH', 'temperature_celsius', 'corrosion_rate_mpy']
    missing_count = 0
    for field in critical_fields:
        if field in df.columns:
            missing_count += df[field].isna().sum()
    
    if missing_count > 0:
        logger.warning(f"Processed dataset still has {missing_count} null values in critical fields")
        return False
    
    return True

def save_processed_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the processed dataset to Parquet format.
    """
    config = get_config()
    if output_path is None:
        output_path = Path(config.get('paths', {}).get('processed_data', 'data/processed/corrosion_dataset.parquet'))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger = get_logger("preprocess")
    logger.info(f"Saved processed dataset to {output_path} with {len(df)} records")
    
    return output_path

def main():
    """
    Main pipeline for preprocessing the NIST corrosion dataset.
    """
    logger = get_logger("preprocess")
    logger.info("Starting data preprocessing pipeline")
    
    try:
        # 1. Load raw dataset
        df = load_raw_dataset()
        logger.info(f"Loaded {len(df)} raw records")
        
        # 2. Filter missing critical fields (with diagnostic logging)
        df, count_missing, reasons_missing = filter_missing_critical_fields(df, logger)
        logger.info(f"Filtered {count_missing} records with missing critical fields")
        
        # 3. Encode weight fractions
        df = encode_weight_fractions(df)
        logger.info("Encoded weight fractions")
        
        # 4. Detect and remove outliers (with diagnostic logging)
        df, count_outliers, reasons_outliers = detect_and_remove_outliers(df, logger)
        logger.info(f"Filtered {count_outliers} records with extreme pH values")
        
        # 5. Validate processed data
        is_valid = validate_processed_data(df, logger)
        if not is_valid:
            logger.warning("Validation warnings present, but proceeding")
        
        # 6. Save processed dataset
        output_path = save_processed_dataset(df)
        
        logger.info(f"Preprocessing complete. Final dataset: {len(df)} records saved to {output_path}")
        
    except DataInsufficientError as e:
        logger.error(f"Pipeline halted due to insufficient data: {e}")
        # Ensure log is written before exit
        log_path = get_log_path("pipeline.log")
        with open(log_path, 'a') as f:
            f.write(f"\n--- PIPELINE HALTED: {str(e)} ---\n")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == "__main__":
    main()