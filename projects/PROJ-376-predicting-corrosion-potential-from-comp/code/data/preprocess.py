import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from utils.logging import get_logger
from utils.exceptions import DataInsufficientError, SchemaMismatchError
from utils.validation import validate_record_count
from utils.config import get_processed_data_path, get_log_path, get_diagnostics_path

# Constants for critical fields
CRITICAL_FIELDS = ['ph', 'temperature', 'potential_mV']
MIN_PH = 0.0
MAX_PH = 14.0

logger = get_logger(__name__)

def load_raw_dataset() -> pd.DataFrame:
    """
    Load the raw dataset from the NIST download location.
    Assumes T012 has successfully downloaded and extracted the data.
    """
    raw_data_path = get_processed_data_path().parent / "raw" / "nist_corrosion.csv"
    if not raw_data_path.exists():
        # Fallback check for common raw data locations if structure differs slightly
        alt_path = get_processed_data_path().parent / "raw" / "corrosion_data.csv"
        if alt_path.exists():
            raw_data_path = alt_path
        else:
            raise FileNotFoundError(f"Raw dataset not found at {raw_data_path} or {alt_path}. Ensure T012 has run.")
    
    logger.info(f"Loading raw dataset from {raw_data_path}")
    df = pd.read_csv(raw_data_path)
    return df

def filter_missing_critical_fields(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter out records with missing critical fields (pH, temperature, potential).
    Returns the filtered dataframe and a list of excluded records with reasons.
    """
    excluded_records = []
    
    for field in CRITICAL_FIELDS:
        if field not in df.columns:
            raise DataInsufficientError(f"Critical field '{field}' missing from dataset columns: {df.columns.tolist()}")
    
    # Identify rows with missing critical fields
    missing_mask = df[CRITICAL_FIELDS].isnull().any(axis=1)
    missing_indices = df[missing_mask].index.tolist()
    
    for idx in missing_indices:
        record = df.loc[idx].to_dict()
        excluded_records.append({
            "index": idx,
            "reason": "missing_critical_field",
            "missing_fields": [f for f in CRITICAL_FIELDS if pd.isna(record.get(f))]
        })
    
    filtered_df = df.dropna(subset=CRITICAL_FIELDS)
    logger.info(f"Filtered {len(missing_indices)} records due to missing critical fields.")
    
    return filtered_df, excluded_records

def log_excluded_records(excluded_records: List[Dict[str, Any]], log_path: Optional[Path] = None) -> None:
    """
    Log diagnostic information about excluded records to the pipeline log.
    Handles missing pH, extreme pH, and other exclusions.
    """
    if not log_path:
        log_path = get_log_path()
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use the global logger which is configured to write to this file
    # We also write a specific summary to the log file for diagnostic purposes
    logger.info("=" * 60)
    logger.info("PIPELINE EXCLUSION DIAGNOSTICS")
    logger.info("=" * 60)
    
    if not excluded_records:
        logger.info("No records were excluded during preprocessing.")
        return

    # Categorize exclusions
    missing_critical = [r for r in excluded_records if r.get("reason") == "missing_critical_field"]
    extreme_ph = [r for r in excluded_records if r.get("reason") == "extreme_ph"]
    outliers = [r for r in excluded_records if r.get("reason") == "outlier"]
    
    if missing_critical:
        logger.warning(f"EXCLUDED (Missing Critical Fields): {len(missing_critical)} records")
        for i, record in enumerate(missing_critical[:10]):  # Log first 10
            fields = record.get("missing_fields", [])
            logger.warning(f"  - Index {record['index']}: Missing {fields}")
        if len(missing_critical) > 10:
            logger.warning(f"  ... and {len(missing_critical) - 10} more records with missing critical fields.")
    
    if extreme_ph:
        logger.warning(f"EXCLUDED (Extreme pH): {len(extreme_ph)} records")
        for i, record in enumerate(extreme_ph[:10]):
            ph_val = record.get("ph_value", "N/A")
            logger.warning(f"  - Index {record['index']}: pH={ph_val} (Outside range [{MIN_PH}, {MAX_PH}])")
        if len(extreme_ph) > 10:
            logger.warning(f"  ... and {len(extreme_ph) - 10} more records with extreme pH.")

    if outliers:
        logger.info(f"EXCLUDED (Outliers): {len(outliers)} records detected by statistical methods.")

    logger.info("=" * 60)

def encode_weight_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode composition weight fractions.
    Ensures all composition columns are numeric and normalized if needed.
    """
    composition_cols = [col for col in df.columns if col.startswith('comp_') or col in ['Fe', 'Cr', 'Ni', 'Mn', 'Mo']]
    if not composition_cols:
        # Assume composition might be in a nested dict or specific column structure
        # For this implementation, we assume flat columns based on typical CSV structures
        # If not found, we just return the df as is, assuming other preprocessing handles it
        logger.warning("No standard composition columns found. Skipping weight fraction encoding.")
        return df

    for col in composition_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Normalize if sum != 1.0 (optional, depending on data quality)
    # For now, just ensuring numeric type is sufficient for model input
    return df

def detect_and_remove_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Detect and remove statistical outliers based on IQR method for continuous variables.
    Returns filtered dataframe and list of excluded outlier records.
    """
    excluded_records = []
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Filter out composition columns from outlier detection if they sum to 1.0
    # We focus on target and environmental variables
    target_cols = ['potential_mV']
    env_cols = ['ph', 'temperature']
    cols_to_check = [c for c in numeric_cols if c in target_cols + env_cols]
    
    if not cols_to_check:
        return df, excluded_records

    for col in cols_to_check:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_indices = df[outlier_mask].index.tolist()
        
        for idx in outlier_indices:
            record = df.loc[idx].to_dict()
            excluded_records.append({
                "index": idx,
                "reason": "outlier",
                "field": col,
                "value": record.get(col)
            })
    
    # Drop outliers
    outlier_indices_set = set([r["index"] for r in excluded_records])
    filtered_df = df.drop(index=list(outlier_indices_set))
    
    logger.info(f"Detected and removed {len(outlier_indices_set)} outlier records.")
    return filtered_df, excluded_records

def validate_processed_data(df: pd.DataFrame, min_records: int = 500) -> None:
    """
    Validate that the processed dataset meets minimum requirements.
    Raises SchemaMismatchError if requirements are not met.
    """
    if len(df) < min_records:
        msg = f"Processed dataset has {len(df)} records, which is less than the required {min_records}."
        logger.error(msg)
        raise SchemaMismatchError(msg)
    
    # Check for nulls in critical fields again after processing
    if df[CRITICAL_FIELDS].isnull().any().any():
        msg = f"Processed dataset still contains nulls in critical fields: {CRITICAL_FIELDS}."
        logger.error(msg)
        raise SchemaMismatchError(msg)
    
    logger.info(f"Validation passed: {len(df)} records, no nulls in critical fields.")

def save_processed_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Save the processed dataset to a Parquet file.
    """
    if not output_path:
        output_path = get_processed_data_path()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved processed dataset to {output_path} with {len(df)} records.")

def write_count_report(count: int, report_path: Optional[Path] = None) -> None:
    """
    Write a count report to the diagnostics log.
    """
    if not report_path:
        report_path = get_diagnostics_path() / "count_report.txt"
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_content = f"{{\"record_count\": {count}, \"timestamp\": \"now\"}}"
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Wrote count report to {report_path}")

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    try:
        # 1. Load Raw Data
        raw_df = load_raw_dataset()
        logger.info(f"Loaded {len(raw_df)} raw records.")

        # 2. Filter Missing Critical Fields
        filtered_df, excluded_missing = filter_missing_critical_fields(raw_df)

        # 3. Detect and Remove Outliers
        processed_df, excluded_outliers = detect_and_remove_outliers(filtered_df)

        # 4. Log Excluded Records (Diagnostic Step for T016)
        all_excluded = excluded_missing + excluded_outliers
        
        # Also check for extreme pH explicitly if not covered by outliers or missing
        # (Assuming pH range 0-14 is a hard constraint separate from statistical outliers)
        extreme_ph_records = []
        if 'ph' in processed_df.columns:
            extreme_mask = (processed_df['ph'] < MIN_PH) | (processed_df['ph'] > MAX_PH)
            extreme_indices = processed_df[extreme_mask].index.tolist()
            for idx in extreme_indices:
                record = processed_df.loc[idx].to_dict()
                extreme_ph_records.append({
                    "index": idx,
                    "reason": "extreme_ph",
                    "ph_value": record.get('ph')
                })
            processed_df = processed_df.drop(index=extreme_indices)
            all_excluded.extend(extreme_ph_records)
            if extreme_ph_records:
                logger.warning(f"Removed {len(extreme_ph_records)} records with extreme pH values.")

        log_excluded_records(all_excluded)

        # 5. Encode Weight Fractions
        final_df = encode_weight_fractions(processed_df)

        # 6. Validate Processed Data
        validate_processed_data(final_df)

        # 7. Save Processed Dataset
        save_processed_dataset(final_df)

        # 8. Write Count Report
        write_count_report(len(final_df))

        logger.info("Preprocessing pipeline completed successfully.")

    except (DataInsufficientError, SchemaMismatchError) as e:
        logger.error(f"Pipeline failed due to data issues: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()