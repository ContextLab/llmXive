import os
import json
import logging
import pandas as pd
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

def load_raw_dataset(raw_path: str) -> pd.DataFrame:
    """
    Load the raw dataset from the specified CSV path.
    
    Args:
        raw_path: Path to the raw dataset CSV file.
        
    Returns:
        pandas DataFrame containing the raw dataset.
        
    Raises:
        FileNotFoundError: If the raw dataset file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")
    
    df = pd.read_csv(raw_path)
    log_info(f"Loaded raw dataset from {raw_path} with {len(df)} rows")
    return df

def validate_mmse_presence(df: pd.DataFrame) -> bool:
    """
    Check if the 'MMSE' column exists in the dataframe AND contains at least one non-null value.
    
    Args:
        df: The dataframe to check.
        
    Returns:
        True if 'MMSE' column exists and has at least one non-null value, False otherwise.
    """
    if 'MMSE' not in df.columns:
        log_warning("Column 'MMSE' not found in raw dataset.")
        return False
    
    has_non_null = df['MMSE'].notna().any()
    
    if not has_non_null:
        log_warning("Column 'MMSE' exists but all values are null.")
        return False
    
    return True

def save_mmse_flag(output_path: str, has_mmse: bool) -> None:
    """
    Write the MMSE flag to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
        has_mmse: Boolean indicating if MMSE data is present.
    """
    flag_data = {"has_mmse": has_mmse}
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    log_info(f"Saved MMSE flag to {output_path}: {flag_data}")

def main():
    """
    Main execution function for T012d: MMSE Flag task.
    
    Reads from data/raw/raw_dataset.csv, validates MMSE presence,
    and writes result to data/processed/mmse_flag.json.
    """
    setup_logging()
    log_info(f"Starting T012d: MMSE Flag check at {get_timestamp()}")
    
    # Define paths
    raw_dataset_path = "data/raw/raw_dataset.csv"
    output_path = "data/processed/mmse_flag.json"
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Load raw dataset
        log_info(f"Attempting to load raw dataset from {raw_dataset_path}")
        df = load_raw_dataset(raw_dataset_path)
        
        # Validate MMSE presence
        has_mmse = validate_mmse_presence(df)
        
        # Log result
        if has_mmse:
            log_info("MMSE column is present and contains non-null values.")
        else:
            log_error("ERR_MMSE_MISSING: MMSE column missing or all null.")
        
        # Save the flag
        save_mmse_flag(output_path, has_mmse)
        
        log_info(f"T012d completed successfully. Result: has_mmse={has_mmse}")
        
    except FileNotFoundError as e:
        log_error(f"Critical Error: {e}")
        log_error("Cannot proceed with MMSE validation without raw dataset.")
        raise
    except Exception as e:
        log_error(f"Unexpected error during T012d execution: {e}")
        raise

if __name__ == "__main__":
    main()