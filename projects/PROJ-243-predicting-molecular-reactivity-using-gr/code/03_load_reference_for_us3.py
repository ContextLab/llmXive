import os
import sys
import logging
import pandas as pd
from typing import Optional

from config import get_config, ensure_directories

def setup_script_logging():
    """Configure logging for the reference loading script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("artifacts/logs/03_load_reference.log"),
        ],
    )
    return logging.getLogger(__name__)

def load_reference_substructures(logger: logging.Logger, file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the curated reference set of known reactive substructures.

    This function loads the data from `data/assets/reference_substructures.csv`,
    which is produced by T009c (Ingest verified data).

    Args:
        logger: Logger instance for progress and error reporting.
        file_path: Optional override for the file path. Defaults to config path.

    Returns:
        pd.DataFrame: The loaded reference substructures dataframe.

    Raises:
        FileNotFoundError: If the reference file does not exist.
        ValueError: If the file is empty or schema validation fails.
    """
    config = get_config()
    if file_path is None:
        file_path = os.path.join(config["data"]["assets"], "reference_substructures.csv")

    logger.info(f"Loading reference substructures from: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"Reference file not found at {file_path}. Ensure T009c has been completed.")
        raise FileNotFoundError(f"Reference substructures file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        raise

    if df.empty:
        logger.error("Loaded reference substructures dataframe is empty.")
        raise ValueError("Reference substructures file is empty.")

    # Basic schema validation
    required_columns = ["smiles", "name", "reactivity_type"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Schema validation failed. Missing columns: {missing_cols}")

    logger.info(f"Successfully loaded {len(df)} reference substructures.")
    logger.debug(f"Columns: {list(df.columns)}")
    logger.debug(f"Sample data:\n{df.head()}")

    return df

def main():
    """Main entry point for the reference loading script."""
    logger = setup_script_logging()
    
    try:
        # Ensure directories exist for logging
        ensure_directories()
        
        # Load the data
        df = load_reference_substructures(logger)
        
        # Log a summary for verification
        logger.info("Reference data availability verified for US3.")
        logger.info(f"Total unique substructures: {df['smiles'].nunique()}")
        logger.info(f"Reactivity types present: {df['reactivity_type'].unique().tolist()}")
        
        return df
    except Exception as e:
        logger.critical(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
