import os
import json
import logging
import pandas as pd
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configuration paths
SCORE_FILTERED_PATH = Path("data/processed/cleaned_score_filtered.csv")
MMSE_FLAG_PATH = Path("data/processed/mmse_flag.json")
EXCLUSION_LOG_PATH = Path("data/processed/exclusion_counts.json")

def load_score_filtered_dataset():
    """
    Loads the score-filtered dataset from disk.
    Raises FileNotFoundError if the file does not exist.
    """
    if not SCORE_FILTERED_PATH.exists():
        raise FileNotFoundError(f"Required input file not found: {SCORE_FILTERED_PATH}")
    
    log_info(f"Loading score-filtered dataset from {SCORE_FILTERED_PATH}")
    df = pd.read_csv(SCORE_FILTERED_PATH)
    log_info(f"Loaded dataset with {len(df)} rows and columns: {list(df.columns)}")
    return df

def validate_mmse_presence(df):
    """
    Validates the presence of the 'MMSE' column and checks for at least one non-null value.
    
    Returns:
        bool: True if 'MMSE' column exists AND has at least one non-null value.
              False otherwise.
    """
    if 'MMSE' not in df.columns:
        log_warning("ERR_MMSE_MISSING: Column 'MMSE' not found in dataset.")
        return False
    
    has_non_null = df['MMSE'].notna().any()
    
    if not has_non_null:
        log_warning("ERR_MMSE_MISSING: Column 'MMSE' exists but contains only null values.")
        return False
    
    log_info("MMSE column present and contains valid data.")
    return True

def save_mmse_flag(has_mmse):
    """
    Saves the MMSE flag status to the designated JSON file.
    
    Args:
        has_mmse (bool): True if MMSE data is valid, False otherwise.
    """
    log_info(f"Saving MMSE flag: has_mmse={has_mmse}")
    
    data = {
        "has_mmse": has_mmse,
        "timestamp": get_timestamp()
    }
    
    # Ensure directory exists
    MMSE_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(MMSE_FLAG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    
    log_info(f"MMSE flag saved to {MMSE_FLAG_PATH}")

def main():
    """
    Main entry point for T012d: MMSE Flag generation.
    
    1. Loads cleaned_score_filtered.csv.
    2. Checks for 'MMSE' column and non-null values.
    3. Writes has_mmse boolean to mmse_flag.json.
    """
    setup_logging()
    log_info("Starting Task T012d: MMSE Flag Validation")
    
    try:
        # Load the pre-processed dataset
        df = load_score_filtered_dataset()
        
        # Validate MMSE presence
        has_mmse = validate_mmse_presence(df)
        
        # Save the result
        save_mmse_flag(has_mmse)
        
        if not has_mmse:
            # Update exclusion counts if necessary (optional side effect per spec flow)
            # The spec says "log ERR_MMSE_MISSING", which is done in validate_mmse_presence
            log_info("T012d completed. MMSE data not available for filtering.")
        else:
            log_info("T012d completed. MMSE data available for filtering.")
            
        return 0
        
    except FileNotFoundError as e:
        log_error(f"Critical error: Input file missing - {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error during T012d execution: {e}")
        raise

if __name__ == "__main__":
    exit(main())
