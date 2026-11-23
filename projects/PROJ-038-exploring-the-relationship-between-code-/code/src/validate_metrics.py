import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd

# Custom exception for data integrity failures
class DataIntegrityError(Exception):
    """Raised when data integrity checks fail (e.g., NaNs found and dropped)."""
    pass

logger = logging.getLogger(__name__)

def validate_no_nan_in_metrics(df: pd.DataFrame, metric_columns: List[str]) -> Tuple[pd.DataFrame, int]:
    """
    Validates that no NaN values exist in the specified metric columns.
    
    If NaNs are found, the corresponding rows are dropped.
    If the count of dropped rows > 0 OR if the resulting DataFrame is empty,
    a DataIntegrityError is raised.
    
    Args:
        df (pd.DataFrame): The input dataframe containing metrics.
        metric_columns (List[str]): List of column names to check for NaNs.
        
    Returns:
        Tuple[pd.DataFrame, int]: The cleaned dataframe and the count of dropped rows.
        
    Raises:
        DataIntegrityError: If rows were dropped or if the dataframe becomes empty.
    """
    if df.empty:
        raise DataIntegrityError("Input DataFrame is empty.")

    initial_count = len(df)
    
    # Identify rows with NaN in any of the metric columns
    nan_mask = df[metric_columns].isna().any(axis=1)
    dropped_count = nan_mask.sum()
    
    if dropped_count > 0:
        logger.warning(f"Found {dropped_count} rows with NaN values in metric columns. Dropping these rows.")
        df_clean = df[~nan_mask].reset_index(drop=True)
    else:
        df_clean = df
        
    final_count = len(df_clean)
    
    # Fail condition: dropped rows > 0 OR resulting CSV is empty
    if dropped_count > 0 or final_count == 0:
        reason = []
        if dropped_count > 0:
            reason.append(f"{dropped_count} rows dropped due to NaN values.")
        if final_count == 0:
            reason.append("Resulting DataFrame is empty after dropping NaNs.")
        
        error_msg = f"DataIntegrityError: {' '.join(reason)} Pipeline halted."
        logger.error(error_msg)
        raise DataIntegrityError(error_msg)
        
    logger.info(f"Validation passed. Dropped {dropped_count} rows. Remaining rows: {final_count}")
    return df_clean, dropped_count

def validate_schema_and_metrics(df: pd.DataFrame, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Validates the schema (required columns) and data integrity (NaNs) of the features dataframe.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        output_path (Optional[Path]): If provided, the validated dataframe is saved to this path.
        
    Returns:
        pd.DataFrame: The validated dataframe.
        
    Raises:
        DataIntegrityError: If validation fails.
        KeyError: If required columns are missing.
    """
    required_columns = ['file_path', 'cc', 'halstead', 'loc', 'is_buggy']
    
    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")
    
    # Validate no NaNs in metric columns (numeric)
    metric_cols = ['cc', 'halstead', 'loc']
    df_clean, dropped_count = validate_no_nan_in_metrics(df, metric_cols)
    
    # Validate no NaNs in is_buggy (target)
    if df_clean['is_buggy'].isna().any():
        raise DataIntegrityError("DataIntegrityError: NaN values found in 'is_buggy' column. Pipeline halted.")
        
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_clean.to_csv(output_path, index=False)
        logger.info(f"Validated features saved to {output_path}")
        
    return df_clean

def main():
    """
    Main entry point for validation script.
    Expects a CSV file path as a command-line argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python validate_metrics.py <input_csv_path> [output_csv_path]")
        sys.exit(1)
        
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        
        validated_df = validate_schema_and_metrics(df, output_path)
        logger.info("Validation successful.")
        
    except DataIntegrityError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
