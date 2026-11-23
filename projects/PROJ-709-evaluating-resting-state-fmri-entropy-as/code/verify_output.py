"""
Verification module for entropy output artifacts.
Implements T018b: Verify output file exists, correct shape, and no NaN values.
Implements T019: Validate biologically plausible range.
"""
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from config (hardcoded here to match T004 specs)
ATLAS_N = 200
EXPECTED_COLS = ATLAS_N + 1  # 200 parcels + 1 subject_id column
EXPECTED_MIN_ROWS = 1       # At least one valid subject
ENTROPY_LOWER_BOUND = 0.0
ENTROPY_UPPER_BOUND = 5.0   # Biologically plausible upper bound for SampEn

def validate_entropy_csv(file_path: str) -> dict:
    """
    Validates the entropy features CSV file.
    
    Checks:
    1. File exists
    2. Shape is (N, 201) where N >= 1
    3. No NaN values
    4. Values within biologically plausible range [0, 5]
    
    Returns:
        dict: Validation results with status and details
    """
    result = {
        "status": "failed",
        "file_exists": False,
        "shape_valid": False,
        "no_nans": False,
        "range_valid": False,
        "details": {}
    }

    path = Path(file_path)
    
    # 1. Check file existence
    if not path.exists():
        result["details"]["error"] = f"File not found: {file_path}"
        logger.error(result["details"]["error"])
        return result
    
    result["file_exists"] = True
    logger.info(f"File found: {file_path}")

    try:
        # Load CSV
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV with shape: {df.shape}")
        
        # 2. Check shape
        expected_shape = (pd.notna(df).any(axis=1).sum(), EXPECTED_COLS)
        actual_shape = df.shape
        
        # We expect at least EXPECTED_MIN_ROWS and exactly EXPECTED_COLS
        rows_valid = actual_shape[0] >= EXPECTED_MIN_ROWS
        cols_valid = actual_shape[1] == EXPECTED_COLS
        
        result["shape_valid"] = rows_valid and cols_valid
        result["details"]["expected_shape"] = (f">={EXPECTED_MIN_ROWS}, {EXPECTED_COLS}")
        result["details"]["actual_shape"] = str(actual_shape)
        
        if not rows_valid:
            logger.error(f"Insufficient rows: expected >= {EXPECTED_MIN_ROWS}, got {actual_shape[0]}")
        if not cols_valid:
            logger.error(f"Wrong column count: expected {EXPECTED_COLS}, got {actual_shape[1]}")

        # 3. Check for NaN values
        nan_count = df.isna().sum().sum()
        result["no_nans"] = nan_count == 0
        result["details"]["nan_count"] = int(nan_count)
        
        if nan_count > 0:
            logger.error(f"Found {nan_count} NaN values in the dataset")
            # Identify columns with NaNs
            nan_cols = df.columns[df.isna().any()].tolist()
            result["details"]["nan_columns"] = nan_cols

        # 4. Check biologically plausible range
        # Exclude the first column (subject_id) if it's non-numeric
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            numeric_data = df[numeric_cols]
            min_val = numeric_data.min().min()
            max_val = numeric_data.max().max()
            
            result["details"]["min_value"] = float(min_val)
            result["details"]["max_value"] = float(max_val)
            
            # Check if all values are within bounds
            all_in_range = (min_val >= ENTROPY_LOWER_BOUND) and (max_val <= ENTROPY_UPPER_BOUND)
            result["range_valid"] = all_in_range
            
            if not all_in_range:
                logger.warning(f"Values out of range [{ENTROPY_LOWER_BOUND}, {ENTROPY_UPPER_BOUND}]: "
                             f"min={min_val}, max={max_val}")
        else:
            logger.warning("No numeric columns found in the dataset")
            result["range_valid"] = False

        # Final status
        if all([result["file_exists"], result["shape_valid"], 
                result["no_nans"], result["range_valid"]]):
            result["status"] = "passed"
            logger.info("✅ Validation PASSED: All checks successful")
        else:
            logger.error("❌ Validation FAILED: One or more checks failed")

    except Exception as e:
        result["details"]["error"] = str(e)
        logger.error(f"Error validating CSV: {e}")
        return result

    return result

def main():
    """Main entry point for verification script."""
    parser = argparse.ArgumentParser(
        description="Verify entropy output CSV file for T018b/T019"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/subject_entropy_features.csv",
        help="Path to the entropy features CSV file"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting verification for: {args.input}")
    
    validation_result = validate_entropy_csv(args.input)
    
    # Print summary
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    print(f"File Exists:        {'✅' if validation_result['file_exists'] else '❌'}")
    print(f"Shape Valid:        {'✅' if validation_result['shape_valid'] else '❌'}")
    print(f"No NaN Values:      {'✅' if validation_result['no_nans'] else '❌'}")
    print(f"Range Valid:        {'✅' if validation_result['range_valid'] else '❌'}")
    print("-"*60)
    print(f"Overall Status:     {validation_result['status'].upper()}")
    print("="*60)
    
    if validation_result["details"]:
        print("\nDetails:")
        for key, value in validation_result["details"].items():
            print(f"  {key}: {value}")
    
    # Exit with appropriate code
    sys.exit(0 if validation_result["status"] == "passed" else 1)

if __name__ == "__main__":
    main()