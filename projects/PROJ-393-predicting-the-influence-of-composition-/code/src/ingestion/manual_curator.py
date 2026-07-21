"""
Manual Curator for Heusler Alloy Data.

Loads manually curated data from data/raw/manual_curated.csv.
Implements graceful degradation: if the file is missing, logs a warning
and returns an empty DataFrame instead of failing.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List

from src.utils.logging_config import setup_logging, create_logger

# Configuration
DEFAULT_DATA_PATH = Path("data/raw/manual_curated.csv")
LOGGER_NAME = "manual_curator"

logger = create_logger(LOGGER_NAME) if create_logger else logging.getLogger(LOGGER_NAME)
setup_logging()

def load_manual_curated_data(
    file_path: Optional[Path] = None,
    required_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load manually curated alloy data from a CSV file.

    Args:
        file_path: Path to the CSV file. Defaults to data/raw/manual_curated.csv.
        required_columns: Optional list of columns that must be present.
                         If a column is missing, a warning is logged but
                         the DataFrame is returned with the available columns.

    Returns:
        pd.DataFrame: The loaded data. Returns an empty DataFrame with no columns
                      if the file is missing (graceful degradation).

    Raises:
        ValueError: If the file exists but is malformed.
    """
    if file_path is None:
        file_path = DEFAULT_DATA_PATH

    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(
            f"Manual curated data file not found at {file_path}. "
            "Proceeding with 0 entries from this source (graceful degradation)."
        )
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded {len(df)} entries from {file_path}")

        if df.empty:
            logger.warning(f"File {file_path} exists but contains no data rows.")
            return pd.DataFrame()

        # Validate columns if specified
        if required_columns:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                logger.warning(
                    f"Missing required columns in {file_path}: {missing_cols}. "
                    "Proceeding with available columns."
                )
            else:
                logger.info("All required columns present.")

        return df

    except pd.errors.EmptyDataError:
        logger.error(f"File {file_path} is empty.")
        return pd.DataFrame()
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse CSV file {file_path}: {e}")
        raise ValueError(f"Malformed CSV file: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        raise

def main():
    """
    Entry point for running the manual curator as a script.
    Loads the default file and prints summary statistics.
    """
    setup_logging()
    logger.info("Starting Manual Curator...")

    # Define expected columns based on typical Heusler alloy data schema
    # This aligns with the alloy_entry.schema.yaml properties
    expected_cols = [
        "composition", "coercivity_oe", "saturation_magnetization_emu_g",
        "remanence_emu_g", "source_type", "synthesis_method",
        "crystal_structure", "doi"
    ]

    try:
        df = load_manual_curated_data(required_columns=expected_cols)

        if df.empty:
            logger.info("No data loaded from manual curator. Pipeline will continue with other sources.")
            return 0

        logger.info(f"Data Summary:")
        logger.info(f"  - Total Rows: {len(df)}")
        logger.info(f"  - Columns: {list(df.columns)}")
        logger.info(f"  - Missing Values per Column:\n{df.isnull().sum()}")

        return 0

    except Exception as e:
        logger.error(f"Manual curator failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())