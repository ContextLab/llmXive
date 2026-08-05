import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verify_output(output_path: str = None) -> bool:
    """
    Verify that the output file `data/processed/subject_entropy_features.csv` exists,
    has the expected shape (N, 201), and contains no NaN values.

    Args:
        output_path: Path to the CSV file. Defaults to 'data/processed/subject_entropy_features.csv'.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    if output_path is None:
        output_path = "data/processed/subject_entropy_features.csv"

    path = Path(output_path)

    # Check 1: File existence
    if not path.exists():
        logger.error(f"Output file not found: {output_path}")
        return False

    logger.info(f"Found output file: {output_path}")

    # Check 2: Load data
    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False

    # Check 3: Shape verification (N, 201)
    # The first column is typically 'subject_id', so we expect 200 feature columns + 1 ID column = 201 total columns.
    # Or if the file is purely numeric without ID, it should be (N, 201).
    # Based on task description: "shape (N, 201)".
    # We will check the number of columns. If it has an index/ID column, total cols should be 201.
    # If the task implies 200 parcels + 1 ID, then cols=201.
    # Let's assume the standard format: subject_id + 200 parcels = 201 columns.
    
    n_rows, n_cols = df.shape
    logger.info(f"Output shape: ({n_rows}, {n_cols})")

    if n_cols != 201:
        logger.error(f"Column count mismatch: expected 201, got {n_cols}")
        return False

    # Check 4: No NaN values
    if df.isnull().any().any():
        nan_count = df.isnull().sum().sum()
        logger.error(f"NaN values detected: {nan_count} missing values found.")
        return False

    # Check 5: Numeric validation (ensure all feature columns are numeric)
    # Assuming column 0 is ID, columns 1..200 are features
    feature_cols = df.columns[1:] if df.columns[0] == 'subject_id' else df.columns
    try:
        df[feature_cols].astype(float)
    except ValueError as e:
        logger.error(f"Non-numeric values found in feature columns: {e}")
        return False

    logger.info("Verification PASSED: File exists, shape is (N, 201), and no NaN values.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Verify entropy output CSV")
    parser.add_argument("--output", type=str, default=None, help="Path to output CSV")
    args = parser.parse_args()

    success = verify_output(args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()