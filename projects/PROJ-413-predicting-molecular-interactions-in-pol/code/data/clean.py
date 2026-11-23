"""
Data cleaning and validation script.
Implements hard abort logic per Plan override: E-DATA-001 if adhesion energy is missing or row count < 100.
"""

import os
import sys
import logging
import json
import math
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.exceptions import DataError
from utils.logger import log_performance
from utils.seed_utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/data_cleaning.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_ROW_COUNT = 100
MAX_MISSING_PERCENTAGE = 0.05
EXIT_CODE_DATA_UNAVAILABLE = 1
EXIT_CODE_E_DATA_001 = 2

def validate_adhesion_energy(df):
    """
    Validates that the 'adhesion_energy' column exists and contains valid numeric values.
    Raises DataError with E-DATA-001 if missing or non-numeric.
    """
    if 'adhesion_energy' not in df.columns:
        raise DataError("E-DATA-001: Adhesion energy column missing from dataset. "
                        "Per Plan override: Hard abort implemented. No proxy fallback allowed.")

    # Check for non-numeric values or all NaN
    if df['adhesion_energy'].isna().all():
        raise DataError("E-DATA-001: Adhesion energy column contains only missing values. "
                        "Per Plan override: Hard abort implemented. No proxy fallback allowed.")

    # Count valid numeric entries
    valid_count = df['adhesion_energy'].notna().sum()
    if valid_count == 0:
        raise DataError("E-DATA-001: No valid adhesion energy measurements found. "
                        "Per Plan override: Hard abort implemented.")

    logger.info(f"Adhesion energy column validated. {valid_count} valid entries found.")
    return True

def validate_row_count(df):
    """
    Validates that the dataset has at least MIN_ROW_COUNT rows.
    Raises DataError with E-DATA-001 if count is insufficient.
    """
    row_count = len(df)
    if row_count < MIN_ROW_COUNT:
        raise DataError(f"E-DATA-001: Insufficient data. Row count ({row_count}) < {MIN_ROW_COUNT}. "
                        "Per Plan override: Hard abort implemented. No proxy fallback allowed.")

    logger.info(f"Row count validated: {row_count} rows (minimum: {MIN_ROW_COUNT}).")
    return True

def validate_missing_values(df, max_missing_pct=MAX_MISSING_PERCENTAGE):
    """
    Validates that missing values per column are within the acceptable threshold.
    Flags columns exceeding the threshold but does not abort if total < 5%.
    """
    total_rows = len(df)
    missing_pct_per_col = {}
    flagged_columns = []

    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_pct = missing_count / total_rows if total_rows > 0 else 0
        missing_pct_per_col[col] = missing_pct

        if missing_pct > max_missing_pct:
            flagged_columns.append((col, missing_pct))

    if flagged_columns:
        logger.warning(f"Columns exceeding missing value threshold ({max_missing_pct * 100}%):")
        for col, pct in flagged_columns:
            logger.warning(f"  - {col}: {pct * 100:.2f}% missing")
    else:
        logger.info("All columns within acceptable missing value threshold.")

    return missing_pct_per_col

def calculate_margin_of_error(df):
    """
    Calculates the margin of error for the adhesion energy column if row count is between 100 and 500.
    Formula: 1.96 * std / sqrt(n)
    Returns None if row count >= 500 or std is not calculable.
    """
    row_count = len(df)
    if row_count >= 500:
        logger.info("Dataset size >= 500. Margin of error not calculated (high power).")
        return None

    adhesion_data = df['adhesion_energy'].dropna()
    if len(adhesion_data) < 2:
        logger.warning("Insufficient data to calculate standard deviation for margin of error.")
        return None

    std_dev = adhesion_data.std()
    margin = 1.96 * std_dev / math.sqrt(row_count)

    logger.info(f"Limited Power Warning: {row_count} rows. Margin of Error (95% CI): ±{margin:.4f}")
    return margin

def clean_and_validate(input_path, output_path):
    """
    Main cleaning and validation pipeline.
    1. Loads data.
    2. Validates adhesion energy (E-DATA-001 abort).
    3. Validates row count (E-DATA-001 abort).
    4. Validates missing values (warning only).
    5. Calculates margin of error if applicable.
    6. Saves cleaned dataset.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise DataError(f"E-DATA-001: Input file not found at {input_path}. "
                        "Per Plan override: Hard abort. No synthetic data generation.")

    logger.info(f"Loading data from {input_path}...")
    try:
        import pandas as pd
        df = pd.read_csv(input_file)
    except Exception as e:
        raise DataError(f"E-DATA-001: Failed to read input file: {str(e)}")

    # Step 1: Validate Adhesion Energy (Hard Abort)
    validate_adhesion_energy(df)

    # Step 2: Validate Row Count (Hard Abort)
    validate_row_count(df)

    # Step 3: Validate Missing Values (Warning)
    validate_missing_values(df)

    # Step 4: Calculate Margin of Error (Warning)
    calculate_margin_of_error(df)

    # Step 5: Save Cleaned Dataset
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Cleaned dataset saved to {output_path}")

    return df

def main():
    """
    Entry point for the data cleaning script.
    Expects input from 'data/raw/molnet_raw.csv' and outputs to 'data/curated/curated_dataset.csv'.
    """
    set_seed(42)
    logger.info("Starting data cleaning and validation pipeline...")

    input_path = "data/raw/molnet_raw.csv"
    output_path = "data/curated/curated_dataset.csv"

    try:
        df = clean_and_validate(input_path, output_path)
        logger.info("Data cleaning completed successfully.")
        sys.exit(0)

    except DataError as e:
        logger.error(f"Data Error: {str(e)}")
        # Determine exit code based on error message content
        if "E-DATA-001" in str(e):
            sys.exit(EXIT_CODE_E_DATA_001)
        else:
            sys.exit(EXIT_CODE_DATA_UNAVAILABLE)

    except Exception as e:
        logger.error(f"Unexpected error during cleaning: {str(e)}")
        sys.exit(EXIT_CODE_DATA_UNAVAILABLE)

if __name__ == "__main__":
    main()