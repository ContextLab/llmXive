import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

from utils.exceptions import DataQualityError
from ingestion.logging_utils import log_validation_failure, log_excluded_record

def calculate_match_proportion(df: pd.DataFrame) -> float:
    """
    Calculate the proportion of rows with valid soil data for all predictors.
    
    Args:
        df: DataFrame containing soil nutrient columns (N, P, K, pH).
    
    Returns:
        Proportion of rows where all predictor columns are non-null.
    """
    predictors = ["N", "P", "K", "pH"]
    total = len(df)
    if total == 0:
        return 0.0
    
    # Count rows where all predictors are non-null
    valid_mask = df[predictors].notna().all(axis=1)
    valid_count = valid_mask.sum()
    
    return valid_count / total

def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows where all predictors (N, P, K, pH) are non-null.
    
    Args:
        df: Input DataFrame.
    
    Returns:
        DataFrame containing only rows with valid soil data for all predictors.
    """
    predictors = ["N", "P", "K", "pH"]
    valid_mask = df[predictors].notna().all(axis=1)
    return df[valid_mask].reset_index(drop=True)

def validate_soil_data_coverage(
    df: pd.DataFrame, 
    threshold: float = 0.90,
    log_path: Optional[Path] = None,
    record_id_col: str = "record_id"
) -> pd.DataFrame:
    """
    Validate that match proportion >= threshold.
    If not, raise DataQualityError.
    Logs excluded records if provided.
    
    Args:
        df: Merged dataset DataFrame.
        threshold: Minimum required match proportion (default 0.90).
        log_path: Path to the exclusion log file. If provided, excluded records are logged.
        record_id_col: Name of the column containing unique record IDs.
    
    Returns:
        Filtered DataFrame containing only valid rows.
    
    Raises:
        DataQualityError: If match proportion is below threshold.
    """
    predictors = ["N", "P", "K", "pH"]
    total_rows = len(df)
    
    if total_rows == 0:
        raise DataQualityError("Input DataFrame is empty.", 0.0)
    
    # Identify valid and invalid rows
    valid_mask = df[predictors].notna().all(axis=1)
    valid_count = valid_mask.sum()
    invalid_count = total_rows - valid_count
    
    match_prop = valid_count / total_rows
    
    # Log excluded records if log_path is provided
    if log_path is not None and invalid_count > 0:
        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        invalid_df = df[~valid_mask].copy()
        
        # Ensure record_id column exists, otherwise use index
        if record_id_col not in invalid_df.columns:
            invalid_df[record_id_col] = invalid_df.index
        
        # Log each excluded record
        for _, row in invalid_df.iterrows():
            record_id = row[record_id_col]
            log_excluded_record(
                record_id=record_id,
                reason_code="missing_soil_data",
                log_path=log_path
            )
    
    # Log validation summary
    timestamp = pd.Timestamp.now().isoformat()
    summary = {
        "timestamp": timestamp,
        "match_proportion": match_prop,
        "total_rows": total_rows,
        "valid_rows": valid_count,
        "excluded_rows": invalid_count
    }
    
    logging.info(f"Validation Summary: {summary}")
    
    # Check threshold
    if match_prop < threshold:
        error_msg = f"Match proportion {match_prop:.4f} < {threshold}. Pipeline halted."
        if log_path:
            log_validation_failure(error_msg, log_path)
        raise DataQualityError(error_msg, match_prop)
    
    logging.info(f"Validation passed: Match proportion = {match_prop:.4f}")
    
    # Return only valid rows
    return df[valid_mask].reset_index(drop=True)

def main():
    """
    Main entry point for T015.
    Executes validation on the merged dataset.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"
    
    # Ensure directories exist
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    merged_dataset_path = processed_dir / "merged_dataset.csv"
    exclusion_log_path = logs_dir / "record_exclusions.log"
    validation_log_path = logs_dir / "validation_summary.log"
    
    if not merged_dataset_path.exists():
        logging.error(f"Merged dataset not found at {merged_dataset_path}")
        raise FileNotFoundError(f"Merged dataset not found: {merged_dataset_path}")
    
    logging.info(f"Loading merged dataset from {merged_dataset_path}")
    df = pd.read_csv(merged_dataset_path)
    
    logging.info(f"Loaded {len(df)} rows")
    
    try:
        valid_df = validate_soil_data_coverage(
            df,
            threshold=0.90,
            log_path=exclusion_log_path
        )
        
        logging.info(f"Validation successful. {len(valid_df)} valid rows remaining.")
        
        # Save valid rows back to processed dataset
        output_path = processed_dir / "validated_dataset.csv"
        valid_df.to_csv(output_path, index=False)
        logging.info(f"Validated dataset saved to {output_path}")
        
    except DataQualityError as e:
        logging.error(f"Validation failed: {e}")
        raise
    
    logging.info("T015 validation completed successfully.")

if __name__ == "__main__":
    main()