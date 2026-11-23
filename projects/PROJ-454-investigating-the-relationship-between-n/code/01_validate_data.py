"""
Task T012b: Validate Variable Fit for EEG datasets.

Loads parquet files from data/raw/, checks for the required behavioral
column 'wcst_perseverative_errors', and flags datasets as excluded in
logs/validation_status.json if the column is missing.

The pipeline proceeds only with valid datasets. If no datasets remain
after exclusion, the script fails loudly.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from utils.logging_config import setup_exclusion_logger, get_logger

TARGET_COLUMN = "wcst_perseverative_errors"
LOG_FILE = "logs/validation_status.json"

def setup_logger():
    """Setup the logger for this module."""
    logger = get_logger("validate_data")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def load_raw_parquet_files(raw_dir: Path) -> list:
    """
    Load all parquet files from the raw directory.
    Returns a list of tuples: (filename, dataframe).
    """
    logger = setup_logger()
    if not raw_dir.exists():
        logger.error(f"Raw directory does not exist: {raw_dir}")
        return []
    
    files = list(raw_dir.glob("*.parquet"))
    if not files:
        logger.warning(f"No parquet files found in {raw_dir}")
        return []
    
    dataframes = []
    for f in files:
        try:
            logger.info(f"Loading {f.name}...")
            df = pd.read_parquet(f)
            dataframes.append((f.name, df))
        except Exception as e:
            logger.error(f"Failed to load {f.name}: {e}")
    
    return dataframes

def verify_variable_fit(dataframes: list, target_col: str) -> dict:
    """
    Check if the target column exists in each dataframe.
    Returns a dict with validation status for each file.
    """
    logger = setup_logger()
    results = {}
    valid_count = 0
    excluded_count = 0

    for filename, df in dataframes:
        if target_col in df.columns:
            results[filename] = {
                "status": "valid",
                "column_found": True,
                "row_count": len(df),
                "exclusion_reason": None
            }
            valid_count += 1
            logger.info(f"File {filename}: VALID (found {target_col})")
        else:
            results[filename] = {
                "status": "excluded",
                "column_found": False,
                "exclusion_reason": f"Missing required column: {target_col}"
            }
            excluded_count += 1
            logger.warning(f"File {filename}: EXCLUDED (missing {target_col})")

    logger.info(f"Validation complete: {valid_count} valid, {excluded_count} excluded.")
    return results

def save_validation_status(results: dict, output_path: Path):
    """Save the validation status to a JSON file."""
    logger = setup_logger()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    status_payload = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "target_column": TARGET_COLUMN,
        "datasets": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(status_payload, f, indent=2)
    
    logger.info(f"Validation status saved to {output_path}")

def main():
    """Main entry point for T012b."""
    logger = setup_logger()
    config = get_config()
    
    # Determine paths based on config or defaults
    raw_dir = Path(config.get('DATA_RAW_DIR', 'data/raw'))
    log_dir = Path(config.get('LOG_DIR', 'logs'))
    output_file = log_dir / LOG_FILE

    logger.info(f"Starting variable fit validation for column: {TARGET_COLUMN}")
    
    # Load raw data
    dataframes = load_raw_parquet_files(raw_dir)
    
    if not dataframes:
        logger.error("No data files found to validate. Pipeline cannot proceed.")
        sys.exit(1)

    # Verify variable fit
    results = verify_variable_fit(dataframes, TARGET_COLUMN)
    
    # Save status
    save_validation_status(results, output_file)

    # Check if any datasets remain
    valid_datasets = [k for k, v in results.items() if v['status'] == 'valid']
    
    if not valid_datasets:
        logger.error("CRITICAL: No datasets remain after validation. Pipeline halting.")
        sys.exit(1)
    
    logger.info(f"Pipeline will proceed with {len(valid_datasets)} valid dataset(s).")
    return valid_datasets

if __name__ == "__main__":
    main()