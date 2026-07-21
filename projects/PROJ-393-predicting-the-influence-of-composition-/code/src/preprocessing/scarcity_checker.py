import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from src.utils.logging_config import setup_logging, create_logger

# Constants
SCARCITY_THRESHOLD = 50
SCARCITY_FLAG_PATH = Path("data/.scarcity_warning")
PROCESSED_DATA_PATH = Path("data/processed/alloys_raw.csv")

logger = create_logger(__name__)

def load_processed_data() -> Optional[pd.DataFrame]:
    """
    Load the processed alloys raw data.
    
    Returns:
        pd.DataFrame: The loaded dataframe, or None if file not found.
    """
    if not PROCESSED_DATA_PATH.exists():
        logger.error(f"Processed data file not found: {PROCESSED_DATA_PATH}")
        return None
    
    try:
        df = pd.read_csv(PROCESSED_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from {PROCESSED_DATA_PATH}")
        return df
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        return None

def check_scarcity(df: pd.DataFrame, threshold: int = SCARCITY_THRESHOLD) -> bool:
    """
    Check if the number of rows is below the scarcity threshold.
    
    Args:
        df: The dataframe to check.
        threshold: The minimum number of rows required.
        
    Returns:
        bool: True if scarcity is detected (N < threshold), False otherwise.
    """
    n = len(df)
    logger.info(f"Scarcity check: N={n}, Threshold={threshold}")
    return n < threshold

def generate_warning_report(n: int, threshold: int) -> Dict[str, Any]:
    """
    Generate a warning report dictionary.
    
    Args:
        n: The actual number of rows.
        threshold: The threshold value.
        
    Returns:
        Dict: The warning report content.
    """
    return {
        "n": n,
        "threshold": threshold,
        "message": f"Data scarcity detected: {n} rows found, threshold is {threshold}. "
                   "Statistical power may be reduced."
    }

def save_check_log(report: Dict[str, Any]) -> None:
    """
    Save the scarcity check log to the flag file.
    
    Args:
        report: The report dictionary to save.
    """
    try:
        # Ensure data directory exists
        SCARCITY_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SCARCITY_FLAG_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Scarcity warning flag written to {SCARCITY_FLAG_PATH}")
    except Exception as e:
        logger.error(f"Failed to write scarcity warning flag: {e}")
        raise

def call_scarcity_warning_module(n: int, threshold: int) -> None:
    """
    Call the check_and_warn function in the scarcity_warning module.
    
    Args:
        n: The actual number of rows.
        threshold: The threshold value.
    """
    try:
        from src.validation.scarcity_warning import check_and_warn
        check_and_warn(n, threshold)
        logger.info("Successfully called scarcity_warning.check_and_warn()")
    except ImportError:
        logger.warning("scarcity_warning module not found; skipping external warning call.")
    except Exception as e:
        logger.error(f"Error calling scarcity_warning.check_and_warn(): {e}")
        # Don't fail the pipeline if the warning module fails, but log it.

def run_scarcity_check() -> bool:
    """
    Main function to run the scarcity check pipeline.
    
    Returns:
        bool: True if check completed successfully, False otherwise.
    """
    setup_logging()
    
    logger.info("Starting scarcity check...")
    
    # Load data
    df = load_processed_data()
    if df is None:
        logger.error("Cannot perform scarcity check: processed data missing.")
        return False
    
    n = len(df)
    
    # Check scarcity
    is_scarce = check_scarcity(df)
    
    if is_scarce:
        logger.warning(f"SCARCITY DETECTED: {n} rows < {SCARCITY_THRESHOLD}")
        
        # Generate report
        report = generate_warning_report(n, SCARCITY_THRESHOLD)
        
        # Save flag file
        save_check_log(report)
        
        # Call external warning module
        call_scarcity_warning_module(n, SCARCITY_THRESHOLD)
        
        return True
    else:
        logger.info(f"No scarcity detected: {n} rows >= {SCARCITY_THRESHOLD}")
        # Remove flag file if it exists from a previous run
        if SCARCITY_FLAG_PATH.exists():
            try:
                SCARCITY_FLAG_PATH.unlink()
                logger.info(f"Removed stale scarcity warning flag: {SCARCITY_FLAG_PATH}")
            except Exception as e:
                logger.warning(f"Failed to remove stale flag: {e}")
        return True

def main() -> int:
    """
    CLI entry point.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        success = run_scarcity_check()
        return 0 if success else 1
    except Exception as e:
        logger.critical(f"Scarcity check failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())