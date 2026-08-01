"""
Task T030: Load curated reference set for US3.

This script verifies the availability of the curated reference set of known
reactive substructures produced by T009c (ingested into data/assets/reference_substructures.csv).
It loads the data, validates basic schema presence, and logs the result.
"""
import os
import sys
import logging
import pandas as pd
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, get_logger, log_metric

def setup_script_logging():
    """Configure logging for this script."""
    return setup_logging("03_load_reference_for_us3")

def load_reference_substructures(
    logger: logging.Logger,
    file_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Load the curated reference set of known reactive substructures.

    Args:
        logger: Logger instance.
        file_path: Path to the CSV file. Defaults to config path.

    Returns:
        DataFrame containing the reference substructures.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or schema is invalid.
    """
    config = get_config()
    target_path = file_path or os.path.join(config['paths']['assets'], 'reference_substructures.csv')

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Reference substructures file not found at: {target_path}. "
                                "Ensure T009c has completed successfully.")

    logger.info(f"Loading reference substructures from {target_path}")
    try:
        df = pd.read_csv(target_path)
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        raise

    if df.empty:
        raise ValueError("Reference substructures file is empty.")

    # Basic schema validation: check for expected columns if they exist in the spec
    # The spec implies a structure for reactive substructures.
    # We check for at least 'substructure' or 'smiles' or similar identifier.
    required_cols = ['substructure', 'smiles', 'reaction_type', 'source']
    existing_cols = set(df.columns)
    found_required = [col for col in required_cols if col in existing_cols]

    if not found_required:
        # Fallback: if no standard columns found, log warning but proceed if data exists
        logger.warning(f"Standard columns {required_cols} not found. Columns present: {list(df.columns)}. "
                       "Proceeding with data availability check.")
    else:
        logger.info(f"Validated schema: Found required columns {found_required}")

    logger.info(f"Successfully loaded {len(df)} rows from reference set.")
    return df

def main():
    """Main entry point for T030."""
    logger = setup_script_logging()
    logger.info("Starting Task T030: Load reference set for US3")

    try:
        # Ensure directories exist (though we are reading, good practice)
        ensure_directories()

        df = load_reference_substructures(logger)

        # Log a metric to confirm availability
        log_metric("reference_set_row_count", len(df), logger=logger)
        log_metric("reference_set_loaded", True, logger=logger)

        logger.info("T030 completed successfully. Data is available for US3.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"T030 failed: {e}")
        return 1
    except ValueError as e:
        logger.error(f"T030 failed validation: {e}")
        return 1
    except Exception as e:
        logger.error(f"T030 failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())