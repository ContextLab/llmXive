import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

def calculate_completeness_percentage(df: pd.DataFrame, date_col: str = 'date') -> float:
    """
    Calculate the percentage of days with valid (non-null) values in the target date range.
    
    Args:
        df: DataFrame containing the time series data
        date_col: Name of the date column
        
    Returns:
        Percentage of days with valid values (0.0 to 100.0)
    """
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Get the date range
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    
    # Calculate total expected days in range
    total_expected_days = (max_date - min_date).days + 1
    
    # Count non-null values for numeric columns (excluding date column)
    # We assume the 'value' column contains the actual data points
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    if len(numeric_cols) == 0:
        # If no numeric columns, check if any value column exists
        if 'value' in df.columns:
            valid_count = df['value'].notna().sum()
        else:
            # Fallback: count non-null in any column except date
            valid_count = df.drop(columns=[date_col]).notna().any(axis=1).sum()
    else:
        # Use the first numeric column as the primary metric
        valid_count = df[numeric_cols[0]].notna().sum()
    
    # Calculate percentage
    if total_expected_days == 0:
        return 0.0
        
    percentage = (valid_count / total_expected_days) * 100.0
    return percentage

def verify_data_completeness(file_path: str, min_threshold: float = 95.0) -> bool:
    """
    Verify that a data file meets the completeness threshold.
    
    Args:
        file_path: Path to the CSV file to verify
        min_threshold: Minimum required completeness percentage (default 95.0%)
        
    Returns:
        True if completeness >= threshold, False otherwise
    """
    logger = get_logger(__name__)
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        
        # Check for date column
        if 'date' not in df.columns:
            logger.error(f"File {file_path} missing 'date' column")
            return False
        
        # Check for value column
        if 'value' not in df.columns:
            logger.error(f"File {file_path} missing 'value' column")
            return False
        
        # Calculate completeness
        completeness = calculate_completeness_percentage(df, 'date')
        logger.info(f"Data completeness for {os.path.basename(file_path)}: {completeness:.2f}%")
        
        # Check threshold
        if completeness >= min_threshold:
            logger.info(f"PASS: Completeness ({completeness:.2f}%) >= threshold ({min_threshold}%)")
            return True
        else:
            logger.error(f"FAIL: Completeness ({completeness:.2f}%) < threshold ({min_threshold}%)")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False

def main():
    """
    Main entry point for verifying data completeness.
    
    Checks both gdelt_events.csv and google_trends.csv for completeness >= 95%.
    Exits with code 0 if all checks pass, 1 if any fail.
    """
    logger = get_logger(__name__)
    logger.info("Starting data completeness verification for T015c")
    
    # Define target files
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    files_to_check = [
        data_dir / "gdelt_events.csv",
        data_dir / "google_trends.csv"
    ]
    
    all_passed = True
    
    for file_path in files_to_check:
        if not file_path.exists():
            logger.error(f"Required file missing: {file_path}")
            all_passed = False
            continue
        
        if not verify_data_completeness(str(file_path), min_threshold=95.0):
            all_passed = False
    
    if all_passed:
        logger.info("All data completeness checks PASSED")
        sys.exit(0)
    else:
        logger.error("Data completeness verification FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()