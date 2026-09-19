"""
T012d: MMSE Flag Validation

Validates the presence of the 'MMSE' column in the score-filtered dataset.
Checks if the column exists AND contains at least one non-null value.
Writes the result (True/False) to data/processed/mmse_flag.json.

Dependencies:
    - data/processed/cleaned_score_filtered.csv (from T012b)
Outputs:
    - data/processed/mmse_flag.json
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error

# Configuration
INPUT_FILE = "data/processed/cleaned_score_filtered.csv"
OUTPUT_FILE = "data/processed/mmse_flag.json"
MMSE_COLUMN = "MMSE"

def load_score_filtered_dataset() -> pd.DataFrame:
    """Load the dataset filtered by age and cognitive scores."""
    path = Path(INPUT_FILE)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. "
                                "Ensure T012b (Score Exclusion) has run successfully.")
    log_info(f"Loading dataset from {INPUT_FILE}")
    return pd.read_csv(path)

def validate_mmse_presence(df: pd.DataFrame) -> bool:
    """
    Check if 'MMSE' column exists and has at least one non-null value.
    
    Returns:
        bool: True if column exists and has non-null values, False otherwise.
    """
    if MMSE_COLUMN not in df.columns:
        log_warning(f"Column '{MMSE_COLUMN}' not found in dataset.")
        return False
    
    non_null_count = df[MMSE_COLUMN].notna().sum()
    if non_null_count == 0:
        log_warning(f"Column '{MMSE_COLUMN}' exists but contains only null values.")
        return False
    
    log_info(f"Column '{MMSE_COLUMN}' found with {non_null_count} non-null values.")
    return True

def save_mmse_flag(has_mmse: bool) -> None:
    """Save the validation result to the JSON flag file."""
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {"has_mmse": has_mmse}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    log_info(f"Saved MMSE flag to {OUTPUT_FILE}: {data}")

def main():
    """Main entry point for T012d."""
    setup_logging()
    log_info("Starting T012d: MMSE Flag Validation")
    
    try:
        # 1. Load the score-filtered dataset
        df = load_score_filtered_dataset()
        
        # 2. Validate MMSE presence
        has_mmse = validate_mmse_presence(df)
        
        # 3. Log specific error if missing
        if not has_mmse:
            log_error("ERR_MMSE_MISSING: MMSE column is missing or contains only null values.")
        else:
            log_info("MMSE column is present and valid.")
        
        # 4. Save the flag
        save_mmse_flag(has_mmse)
        
        log_info("T012d completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        log_error(f"File error: {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error during T012d: {e}")
        raise

if __name__ == "__main__":
    exit(main())