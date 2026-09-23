import os
import json
import logging
import pandas as pd
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Constants
INPUT_FILE = "data/processed/cleaned_score_filtered.csv"
OUTPUT_FILE = "data/processed/mmse_flag.json"
LOG_MESSAGE_MISSING = "ERR_MMSE_MISSING"

logger = logging.getLogger(__name__)

def load_score_filtered_dataset(file_path: str) -> pd.DataFrame:
    """Load the score-filtered dataset."""
    path = Path(file_path)
    if not path.exists():
        log_error(f"Input file not found: {path}")
        raise FileNotFoundError(f"Input file not found: {path}")
    
    logger.info(f"Loading dataset from {path}")
    return pd.read_csv(path)

def validate_mmse_presence(df: pd.DataFrame) -> bool:
    """
    Check if 'MMSE' column exists AND contains at least one non-null value.
    Logic: df['MMSE'].notna().any()
    """
    if 'MMSE' not in df.columns:
        log_warning("MMSE column not found in dataset.")
        return False
    
    has_non_null = df['MMSE'].notna().any()
    if not has_non_null:
        log_warning("MMSE column exists but all values are null.")
        return False
    
    return True

def save_mmse_flag(has_mmse: bool, output_path: str) -> None:
    """Write the mmse flag to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "has_mmse": has_mmse,
        "timestamp": get_timestamp()
    }
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"MMSE flag saved to {path}: has_mmse={has_mmse}")

def main():
    """Main entry point for T012d."""
    setup_logging()
    logger.info("Starting T012d: MMSE Flag Validation")
    
    try:
        # Load input
        df = load_score_filtered_dataset(INPUT_FILE)
        
        # Validate
        has_mmse = validate_mmse_presence(df)
        
        # Log specific error if missing
        if not has_mmse:
            log_error(LOG_MESSAGE_MISSING)
        
        # Save result
        save_mmse_flag(has_mmse, OUTPUT_FILE)
        
        logger.info("T012d completed successfully.")
        return 0
        
    except Exception as e:
        log_error(f"Task failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
