import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from utils.logging import get_logger
from utils.exceptions import DataInsufficientError
from utils.validation import validate_non_nulls, filter_null_records
from data.models import AlloyRecord, EnvironmentRecord, CorrosionMeasurement

logger = get_logger(__name__)

def load_raw_dataset(raw_path: str) -> pd.DataFrame:
    """Load the raw NIST dataset into a DataFrame."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")
    df = pd.read_csv(raw_path)
    logger.info(f"Loaded raw dataset with {len(df)} records")
    return df

def filter_missing_critical_fields(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter out records with missing critical fields (pH, temperature).
    Returns cleaned DataFrame and a list of excluded records with reasons.
    """
    critical_fields = ['ph_value', 'temperature_c']
    excluded_records = []
    valid_mask = pd.Series([True] * len(df), index=df.index)

    for field in critical_fields:
        if field not in df.columns:
            logger.warning(f"Critical field '{field}' not found in dataset")
            continue

        null_mask = df[field].isnull()
        if null_mask.any():
            # Extract excluded records for logging
            excluded = df[null_mask][critical_fields].to_dict('records')
            for i, rec in enumerate(excluded):
                excluded_records.append({
                    'index': df.index[null_mask][i],
                    'reason': f"Missing {field}",
                    'values': rec
                })
            valid_mask = valid_mask & ~null_mask

    cleaned_df = df[valid_mask]
    logger.info(f"Filtered {len(df) - len(cleaned_df)} records due to missing critical fields")
    return cleaned_df, excluded_records

def encode_weight_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """Encode weight fractions of alloying elements into numeric features."""
    # Assuming columns like 'wt_Fe', 'wt_Cr', etc. exist
    metal_columns = [col for col in df.columns if col.startswith('wt_')]
    if not metal_columns:
        logger.warning("No weight fraction columns found (expected wt_*)")
        return df

    logger.info(f"Encoding {len(metal_columns)} weight fraction columns")
    # Ensure numeric type, coerce errors to NaN
    df[metal_columns] = pd.to_numeric(df[metal_columns], errors='coerce')
    
    # Fill NaN with 0 (assuming missing implies 0 weight fraction)
    df[metal_columns] = df[metal_columns].fillna(0)
    
    return df

def detect_and_remove_outliers(df: pd.DataFrame, threshold: float = 3.0) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Detect and remove outliers based on IQR method for corrosion potential.
    Returns cleaned DataFrame and excluded records.
    """
    target_col = 'corrosion_potential_mv'
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found, skipping outlier detection")
        return df, []

    Q1 = df[target_col].quantile(0.25)
    Q3 = df[target_col].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - threshold * IQR
    upper_bound = Q3 + threshold * IQR

    outlier_mask = (df[target_col] < lower_bound) | (df[target_col] > upper_bound)
    excluded_records = []
    
    if outlier_mask.any():
        excluded = df[outlier_mask][[target_col]].to_dict('records')
        for i, rec in enumerate(excluded):
            excluded_records.append({
                'index': df.index[outlier_mask][i],
                'reason': 'Outlier (IQR)',
                'values': rec
            })
    
    cleaned_df = df[~outlier_mask]
    logger.info(f"Removed {len(outlier_mask) - outlier_mask.sum()} outlier records")
    return cleaned_df, excluded_records

def validate_processed_data(df: pd.DataFrame) -> int:
    """
    Validate processed data: check for non-nulls in critical fields.
    Returns the count of valid records.
    """
    critical_fields = ['ph_value', 'temperature_c', 'corrosion_potential_mv', 'specific_alloy_designation_id']
    valid_count = len(df)
    
    for field in critical_fields:
        if field in df.columns:
            nulls = df[field].isnull().sum()
            if nulls > 0:
                logger.warning(f"Found {nulls} nulls in critical field '{field}' after processing")
                valid_count -= nulls
                # Filter them out strictly
                df = df.dropna(subset=[field])
        else:
            raise ValueError(f"Critical field '{field}' missing after processing")
    
    return len(df)

def log_excluded_records(excluded_records: List[Dict[str, Any]], log_path: Path, phase: str = "Preprocessing"):
    """
    Write detailed diagnostic logs for excluded records to the pipeline log.
    """
    if not excluded_records:
        logger.info(f"No records excluded during {phase}.")
        return

    logger.info(f"--- {phase} Exclusion Diagnostics ---")
    logger.info(f"Total excluded records: {len(excluded_records)}")
    
    # Group by reason for summary
    reasons = {}
    for rec in excluded_records:
        reason = rec['reason']
        reasons[reason] = reasons.get(reason, 0) + 1

    for reason, count in reasons.items():
        logger.info(f"  - {reason}: {count} records")

    # Write detailed breakdown
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"\n{phase} Exclusion Details:\n")
        for i, rec in enumerate(excluded_records):
            f.write(f"  Record Index {rec['index']}: {rec['reason']} -> {rec['values']}\n")
    
    logger.info(f"Exclusion details written to {log_path}")

def save_processed_dataset(df: pd.DataFrame, output_path: str):
    """Save the processed dataset to parquet."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved processed dataset to {output_path} ({len(df)} records)")

def main():
    """Main pipeline execution for preprocessing."""
    # Configuration
    raw_path = "data/raw/nist_corrosion.csv"  # Adjust based on actual download output
    output_path = "data/processed/corrosion_dataset.parquet"
    log_path = Path("data/logs/pipeline.log")
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup file logging
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info("Starting preprocessing pipeline...")

    try:
        # 1. Load Raw Data
        df = load_raw_dataset(raw_path)

        # 2. Filter Missing Critical Fields
        df, excluded_missing = filter_missing_critical_fields(df)
        log_excluded_records(excluded_missing, log_path, "Missing Critical Fields")

        # 3. Encode Weight Fractions
        df = encode_weight_fractions(df)

        # 4. Detect and Remove Outliers
        df, excluded_outliers = detect_and_remove_outliers(df)
        log_excluded_records(excluded_outliers, log_path, "Outliers")

        # 5. Validate Processed Data
        final_count = validate_processed_data(df)

        # 6. Enforce Minimum Record Count (FR-014)
        if final_count < 500:
            logger.error(f"Insufficient records: {final_count} < 500. Halting pipeline.")
            # Write count to diagnostics
            diag_path = Path("data/logs/diagnostics/count_report.txt")
            diag_path.parent.mkdir(parents=True, exist_ok=True)
            with open(diag_path, 'w') as f:
                f.write(f"Pipeline Halted: Record count {final_count} is below minimum 500.\n")
            raise DataInsufficientError(f"Processed dataset has {final_count} records, minimum required is 500.")

        # 7. Save Dataset
        save_processed_dataset(df, output_path)
        logger.info("Preprocessing pipeline completed successfully.")

    except DataInsufficientError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()