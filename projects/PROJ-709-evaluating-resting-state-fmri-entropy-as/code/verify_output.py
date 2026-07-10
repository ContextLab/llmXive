"""
T018b: Verify output file data/processed/subject_entropy_features.csv exists with shape (N, 201) and no NaN values.

This script performs the final validation check for User Story 1.
It loads the generated CSV, checks its existence, verifies the column count (201),
ensures there are no NaN values, and reports the subject count N.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_PATH = Path("data/processed/subject_entropy_features.csv")
EXPECTED_COLS = 201  # 200 parcels + 1 subject_id column (or just 201 if subject_id is index)
# Based on typical implementation: 200 parcels + 1 ID column = 201 columns
# Or if subject_id is index: 200 columns. Let's assume standard CSV with ID column.
# The task description says shape (N, 201).
# If the CSV has a header and index, we need to be careful.
# We will assume the file has 201 columns total (including subject_id if present).

def verify_output():
    """Verify the entropy features output file."""
    logger.info(f"Checking for output file: {OUTPUT_PATH}")

    if not OUTPUT_PATH.exists():
        logger.error(f"Output file does not exist: {OUTPUT_PATH}")
        logger.error("The pipeline (T018a) may not have run successfully or the path is incorrect.")
        return False

    try:
        logger.info("Loading CSV file...")
        df = pd.read_csv(OUTPUT_PATH)
        
        logger.info(f"File loaded successfully. Shape: {df.shape}")
        
        # Check 1: Column count
        actual_cols = df.shape[1]
        if actual_cols != EXPECTED_COLS:
            logger.warning(f"Column count mismatch. Expected {EXPECTED_COLS}, got {actual_cols}.")
            # Depending on implementation, sometimes the ID column is separate or index.
            # If the task strictly says (N, 201), we enforce it.
            # If the data was saved with index=False and has 200 parcels + 1 ID, it's 201.
            # If it has 200 parcels and ID is index, it's 200 columns.
            # Let's be strict: if it's not 201, we flag it unless it's exactly 200 (which might be valid if ID is index).
            # However, the task explicitly says (N, 201).
            if actual_cols == 200:
                logger.warning("Detected 200 columns. If the first column is subject_id, this might be correct if the index was dropped.")
                # We will proceed but warn. If strict compliance is needed, this is a failure.
                # For this verification, we will assume 201 is the hard requirement.
                logger.error(f"Strict requirement failed: Expected 201 columns, found {actual_cols}.")
                return False
            else:
                logger.error(f"Critical column count failure: Expected {EXPECTED_COLS}, found {actual_cols}.")
                return False
        else:
            logger.info(f"Column count verified: {actual_cols} columns.")

        # Check 2: NaN values
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            logger.error(f"NaN values detected: {nan_count} missing values found in the dataset.")
            # Show where NaNs are
            nan_cols = df.columns[df.isna().any()]
            logger.warning(f"Columns with NaNs: {list(nan_cols)}")
            return False
        else:
            logger.info("No NaN values detected.")

        # Check 3: Data types (ensure numeric for feature columns)
        # Assuming column 0 is ID and 1..200 are features
        feature_cols = df.columns[1:]
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns
        if len(numeric_cols) != len(feature_cols):
            logger.warning(f"Some feature columns are not numeric. Non-numeric: {set(feature_cols) - set(numeric_cols)}")
            # This might be a soft fail, but for a biomarker matrix, they should be numeric.
            # We will treat this as a warning but not a hard failure if the count is correct, 
            # unless the task implies strict numeric matrix.
            # Let's assume strict numeric is required for the "matrix".
            if len(numeric_cols) < len(feature_cols):
                logger.error("Feature columns must be numeric for the entropy matrix.")
                return False
        
        logger.info("Data type verification passed.")

        # Check 4: Value range (Biological plausibility check - optional but good practice)
        # Sample entropy is typically positive and usually < 2 or 3 for fMRI.
        # We'll check for extreme outliers or negative values if any.
        min_val = df[feature_cols].min().min()
        max_val = df[feature_cols].max().max()
        logger.info(f"Value range: [{min_val:.4f}, {max_val:.4f}]")
        
        if min_val < 0:
            logger.warning("Negative values detected. Sample Entropy should be non-negative.")
            # This might indicate a calculation error or normalization issue.
            # We will flag it but not fail unless it's a hard constraint.
        
        # Final Result
        logger.info("=" * 50)
        logger.info("VERIFICATION SUCCESSFUL")
        logger.info(f"File: {OUTPUT_PATH}")
        logger.info(f"Shape: {df.shape} (N={df.shape[0]}, Variables={df.shape[1]-1})")
        logger.info(f"Missing Values: 0")
        logger.info(f"Data Types: All numeric")
        logger.info("=" * 50)
        return True

    except Exception as e:
        logger.error(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_output()
    sys.exit(0 if success else 1)