"""
Task T012d: Verify dual-source compliance for perovskite data.

This script asserts that both NREL and Materials Project data sources have been
successfully fetched and contain valid data. It fails loudly if either file is
missing or empty, ensuring the pipeline does not proceed with incomplete data.
"""
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NREL_PATH = PROJECT_ROOT / "data" / "raw" / "nrel_perovskites.csv"
MP_PATH = PROJECT_ROOT / "data" / "raw" / "mp_perovskites.csv"

def check_source(path: Path, source_name: str) -> Tuple[bool, int, List[str]]:
    """
    Check if a source file exists and contains data.

    Args:
        path: Path to the CSV file.
        source_name: Human-readable name of the source for logging.

    Returns:
        Tuple of (is_valid, row_count, error_messages)
    """
    errors = []
    if not path.exists():
        errors.append(f"CRITICAL: File '{path}' does not exist.")
        return False, 0, errors

    try:
        df = pd.read_csv(path)
    except Exception as e:
        errors.append(f"CRITICAL: Failed to read '{path}': {e}")
        return False, 0, errors

    row_count = len(df)
    if row_count == 0:
        errors.append(f"CRITICAL: File '{path}' exists but contains 0 rows.")
        return False, 0, errors

    logger.info(f"OK: {source_name} loaded successfully. Rows: {row_count}")
    return True, row_count, errors

def main() -> int:
    """
    Main execution function for T012d.

    Returns:
        Exit code: 0 if both sources are valid, 1 if verification fails.
    """
    logger.info("Starting dual-source compliance verification (T012d)...")

    nrel_ok, nrel_count, nrel_errors = check_source(NREL_PATH, "NREL Perovskites")
    mp_ok, mp_count, mp_errors = check_source(MP_PATH, "Materials Project Perovskites")

    all_errors = nrel_errors + mp_errors

    if all_errors:
        for error in all_errors:
            logger.error(error)
        logger.critical("Dual-source verification FAILED. One or more sources are missing or empty.")
        return 1

    logger.info("-" * 60)
    logger.info("DUAL-SOURCE VERIFICATION PASSED")
    logger.info(f"  NREL Perovskites: {nrel_count} rows")
    logger.info(f"  Materials Project: {mp_count} rows")
    logger.info(f"  Total validated rows: {nrel_count + mp_count}")
    logger.info("-" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())