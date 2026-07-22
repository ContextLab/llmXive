import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from src.utils.logging_config import setup_logging, create_logger
from src.validation.scarcity_warning import check_and_warn

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
INPUT_FILE = project_root / "data" / "processed" / "alloys_raw.csv"
FLAG_FILE = project_root / "data" / ".scarcity_warning"
THRESHOLD = 50

def load_processed_data() -> Optional[pd.DataFrame]:
    """Load the processed alloys raw CSV file."""
    if not INPUT_FILE.exists():
        logger.error(f"Processed data file not found: {INPUT_FILE}")
        return None
    try:
        df = pd.read_csv(INPUT_FILE)
        if df.empty:
            logger.warning(f"Processed data file exists but is empty: {INPUT_FILE}")
            return df
        return df
    except Exception as e:
        logger.error(f"Error loading processed data: {e}")
        return None

def check_scarcity(df: pd.DataFrame) -> bool:
    """
    Check dataset size against threshold.
    Returns True if warning is needed (N < 50), False if sufficient or error.
    Returns False (and logs Critical) if N=0.
    """
    if df is None or df.empty:
        logger.critical("Scarcity Check: Dataset is EMPTY (N=0). Halting pipeline.")
        return False # Indicates failure/halt

    n = len(df)
    if n == 0:
        logger.critical("Scarcity Check: Dataset is empty (N=0). Halting pipeline.")
        return False

    if n < THRESHOLD:
        logger.warning(f"Scarcity Check: Dataset size N={n} is below threshold {THRESHOLD}.")
        return True # Indicates warning needed

    logger.info(f"Scarcity Check: Dataset size N={n} is sufficient (>= {THRESHOLD}).")
    return False

def generate_warning_report(n: int, threshold: int) -> Dict[str, Any]:
    """Generate the warning report dictionary."""
    return {
        "n": n,
        "threshold": threshold,
        "warning": f"Dataset size ({n}) is below recommended threshold ({threshold}). Results may be subject to overfitting.",
        "status": "SCARCITY_WARNING"
    }

def save_check_log(report: Dict[str, Any]):
    """Write the flag file to disk."""
    FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FLAG_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Scarcity flag saved to {FLAG_FILE}")

def call_scarcity_warning_module():
    """Invoke the external warning generation module."""
    logger.info("Calling scarcity_warning module to generate report.")
    check_and_warn()

def run_scarcity_check() -> bool:
    """
    Execute the full scarcity check logic.
    Returns True if check passed (either sufficient data or warning issued).
    Returns False if critical error occurred (e.g., empty dataset).
    """
    logger.info("Running Scarcity Check (T028b)...")
    
    df = load_processed_data()
    
    if df is None:
        logger.critical("Scarcity Check failed: Input file missing or unreadable.")
        return False
    
    if df.empty:
        logger.critical("Scarcity Check failed: Dataset is empty (N=0). Halting pipeline.")
        return False

    n = len(df)
    
    if n == 0:
        logger.critical("Scarcity Check failed: Dataset is empty after loading.")
        return False

    if n < THRESHOLD:
        report = generate_warning_report(n, THRESHOLD)
        save_check_log(report)
        logger.warning(f"Scarcity warning triggered (N={n} < {THRESHOLD}). Calling warning module.")
        call_scarcity_warning_module()
        return True # Warning issued, but pipeline can technically continue to T046

    logger.info("Scarcity check passed.")
    return True

def main():
    """Entry point for the script."""
    setup_logging()
    logger.info("Scarcity Checker Main Entry")
    try:
        success = run_scarcity_check()
        # If success is False, it means a critical error occurred (N=0 or missing file)
        # We exit with error code 1 to halt the pipeline
        return 0 if success else 1
    except Exception as e:
        logger.critical(f"Scarcity check failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
