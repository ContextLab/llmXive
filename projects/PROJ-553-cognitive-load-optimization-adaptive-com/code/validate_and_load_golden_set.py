"""
Validate and Load Golden Set (Task T007f).

This script checks for the existence and validity of the Golden Set file.
If the file is missing, it checks for a public dataset with concurrent self-reports.
If neither exists, it raises a hard HALT error with a specific message.
NO synthetic generation is permitted.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Ensure we can import from the code directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import get_logger

def ensure_directories():
    """Ensure the data/processed directory exists."""
    data_processed = Path("data/processed")
    data_processed.mkdir(parents=True, exist_ok=True)
    return data_processed

def validate_golden_set_csv(file_path: Path) -> bool:
    """
    Validate the Golden Set CSV file.
    
    Checks:
    1. File exists.
    2. Contains required columns: 'interaction_id', 'expert_load_score'.
    3. Contains at least 50 rows.
    4. 'expert_load_score' values are within 0-100.
    
    Returns True if valid, raises ValueError otherwise.
    """
    logger = get_logger()
    
    if not file_path.exists():
        logger.error(f"Golden Set file not found: {file_path}")
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read Golden Set CSV: {e}")
        return False

    required_columns = {'interaction_id', 'expert_load_score'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"Golden Set missing required columns: {missing}")
        return False

    if len(df) < 50:
        logger.error(f"Golden Set has {len(df)} rows. Minimum 50 required.")
        return False

    if not df['expert_load_score'].between(0, 100).all():
        logger.error("Golden Set contains 'expert_load_score' values outside 0-100 range.")
        return False

    logger.info(f"Golden Set validated successfully: {len(df)} rows.")
    return True

def check_public_self_reports() -> bool:
    """
    Check if a public dataset with concurrent self-reports (e.g., NASA-TLX) was loaded.
    
    This checks for a specific marker file or column in the loaded data that indicates
    the presence of self-report labels, as per T004's verification logic.
    Since T004 loads data, we check if the loaded data (or a marker) indicates success.
    
    We look for a marker file created by T004 if it found self-reports, 
    or check the loaded dataset structure if we can access it.
    For robustness, we check for a specific marker file 'data/processed/.has_self_reports'
    which T004 should create if it finds valid self-reports.
    """
    logger = get_logger()
    marker_path = Path("data/processed/.has_self_reports")
    
    if marker_path.exists():
        logger.info("Public dataset with concurrent self-reports found (marker exists).")
        return True
    
    # Fallback: Check if the loaded ASSISTments/OULAD data exists and has self-report columns
    # This is a heuristic check based on T004's expected behavior
    assistments_path = Path("data/processed/assistments_dataset.csv")
    if assistments_path.exists():
        try:
            df = pd.read_csv(assistments_path)
            # Check for common self-report column names
            self_report_cols = ['nasa_tlx', 'self_report_load', 'perceived_load', 'tlx_score']
            if any(col in df.columns for col in self_report_cols):
                logger.info("Public dataset with concurrent self-reports found in loaded data.")
                return True
        except Exception:
            pass
    
    logger.warning("No public dataset with concurrent self-reports found.")
    return False

def main():
    logger = get_logger()
    logger.info("Starting Golden Set validation (Task T007f)...")

    ensure_directories()
    golden_set_path = Path("data/processed/golden_set.csv")

    # Step 1: Check for Golden Set file
    if golden_set_path.exists():
        if validate_golden_set_csv(golden_set_path):
            logger.info("Golden Set validation PASSED. Pipeline can proceed.")
            return 0
        else:
            logger.error("Golden Set validation FAILED. File exists but is invalid.")
            return 1

    # Step 2: If Golden Set is missing, check for public dataset with self-reports
    logger.warning("Golden Set file missing. Checking for public dataset with self-reports...")
    if check_public_self_reports():
        logger.info("Public dataset with self-reports found. Pipeline can proceed without manual Golden Set.")
        return 0

    # Step 3: If neither exists, HALT with specific error message
    halt_message = (
        "WAITING_FOR_HUMAN: Golden Set file (data/processed/golden_set.csv) is missing "
        "AND no public dataset with concurrent self-reports found. "
        "Please complete the manual labeling process described in `docs/golden_set_creation.md` "
        "to acquire the Golden Set. The pipeline cannot proceed without external expert labels."
    )
    logger.error(halt_message)
    print(halt_message) # Ensure message is printed to stdout for pipeline capture
    raise SystemExit(1)

if __name__ == "__main__":
    sys.exit(main())
