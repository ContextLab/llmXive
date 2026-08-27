import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'sample_id', 'method', 'prediction', 'variance',
    'lower_50', 'upper_50', 'lower_90', 'upper_90'
]

# Optional columns that might be added by other tasks (e.g., uncertainty types)
OPTIONAL_COLUMNS = ['aleatoric', 'epistemic', 'total']

def verify_schema(df: pd.DataFrame) -> bool:
    """
    Verify that the DataFrame contains all required columns.
    """
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        logger.error(f"Schema verification failed. Missing columns: {missing_cols}")
        return False
    
    logger.info("Schema verification passed: All required columns present.")
    
    # Check for optional columns and log presence
    optional_present = set(df.columns) & set(OPTIONAL_COLUMNS)
    if optional_present:
        logger.info(f"Optional columns detected: {optional_present}")
    
    return True

def verify_data_integrity(df: pd.DataFrame) -> bool:
    """
    Verify data integrity:
    1. No NaN values in required columns.
    2. Variance must be non-negative.
    3. Lower bounds must be <= prediction <= Upper bounds.
    4. lower_50 <= lower_90 and upper_90 <= upper_50 (assuming 90% interval is wider).
    """
    is_valid = True

    # 1. Check for NaNs in required columns
    for col in REQUIRED_COLUMNS:
        if df[col].isna().any():
            logger.error(f"Data integrity failed: Column '{col}' contains NaN values.")
            is_valid = False

    # 2. Check variance non-negative
    if (df['variance'] < 0).any():
        logger.error("Data integrity failed: Variance contains negative values.")
        is_valid = False

    # 3. Check interval logic: lower <= prediction <= upper
    # For 50% interval
    if ((df['lower_50'] > df['prediction']) | (df['prediction'] > df['upper_50'])).any():
        logger.error("Data integrity failed: 50% interval does not contain prediction.")
        is_valid = False
    
    # For 90% interval
    if ((df['lower_90'] > df['prediction']) | (df['prediction'] > df['upper_90'])).any():
        logger.error("Data integrity failed: 90% interval does not contain prediction.")
        is_valid = False

    # 4. Check interval nesting: 90% should be wider than 50%
    # lower_90 <= lower_50 and upper_50 <= upper_90
    if ((df['lower_90'] > df['lower_50']) | (df['upper_50'] > df['upper_90'])).any():
        logger.error("Data integrity failed: 90% interval is not wider than 50% interval.")
        is_valid = False

    if is_valid:
        logger.info("Data integrity verification passed.")
    else:
        logger.error("Data integrity verification failed.")
    
    return is_valid

def main():
    """
    Main entry point to verify the uq_predictions.csv artifact.
    """
    input_path = "results/uq_predictions.csv"
    
    if not os.path.exists(input_path):
        logger.error(f"Artifact not found: {input_path}")
        print(json.dumps({"status": "failed", "reason": "File not found"}))
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {input_path} with shape {df.shape}")
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        print(json.dumps({"status": "failed", "reason": f"Read error: {str(e)}"}))
        sys.exit(1)

    schema_ok = verify_schema(df)
    integrity_ok = verify_data_integrity(df)

    if schema_ok and integrity_ok:
        logger.info("Verification complete: SUCCESS")
        result = {
            "status": "success",
            "rows_verified": len(df),
            "columns_verified": REQUIRED_COLUMNS,
            "message": "All checks passed."
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        logger.error("Verification complete: FAILED")
        result = {
            "status": "failed",
            "rows_verified": len(df),
            "message": "Schema or data integrity checks failed."
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()