"""
Validation script for T014.
Verifies that `data/processed/crystal_dataset.csv` has no nulls in key columns
and that fingerprint bit counts are of a fixed, high-dimensional magnitude.
Outputs `data/validation/fingerprint_check.json`.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Import local config for path resolution
# Note: Using relative import to ensure it works when run as module or script
try:
    from config import get_path_processed_data, get_path_validation, ensure_directory
except ImportError:
    # Fallback for direct execution if path setup is different
    import os
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_path_processed_data, get_path_validation, ensure_directory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'validation_fingerprints.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_FILE = "crystal_dataset.csv"
OUTPUT_FILE = "fingerprint_check.json"
FINGERPRINT_COL = "fingerprint" # Assumed column name based on pipeline context
EXPECTED_DIM = 2048 # Standard ECFP4 dimension

def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the processed dataset."""
    logger.info(f"Loading dataset from {dataset_path}")
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    try:
        df = pd.read_csv(dataset_path)
        logger.info(f"Loaded dataset with shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def validate_no_nulls(df: pd.DataFrame, key_columns: List[str]) -> Dict[str, Any]:
    """Check for nulls in key columns."""
    issues = []
    for col in key_columns:
        if col not in df.columns:
            issues.append(f"Column '{col}' is missing from dataset.")
            continue
        
        null_count = df[col].isnull().sum()
        if null_count > 0:
            issues.append(f"Column '{col}' has {null_count} null values.")
    
    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "details": {col: int(df[col].isnull().sum()) for col in key_columns if col in df.columns}
    }

def validate_fingerprint_dimension(df: pd.DataFrame, fingerprint_col: str, expected_dim: int) -> Dict[str, Any]:
    """Verify fingerprint bit counts match expected high-dimensional magnitude."""
    issues = []
    passed = True
    
    if fingerprint_col not in df.columns:
        return {
            "passed": False,
            "issues": [f"Column '{fingerprint_col}' not found."],
            "details": {}
        }

    # Check if fingerprints are stored as lists or strings
    sample_val = df[fingerprint_col].iloc[0]
    
    counts = []
    valid_count = 0
    invalid_count = 0

    for idx, val in enumerate(df[fingerprint_col]):
        if pd.isna(val):
            invalid_count += 1
            continue

        try:
            if isinstance(val, str):
                # Assuming format: "[0, 1, 0, ...]" or similar
                # Remove brackets and split, or eval if safe (using ast is safer but string parsing is robust for CSV)
                clean_val = val.strip().strip('[]')
                if not clean_val:
                   bit_list = []
                else:
                   bit_list = [int(x.strip()) for x in clean_val.split(',')]
            elif isinstance(val, list):
                bit_list = val
            else:
                # Try to convert to list if it's a numpy array or similar
                bit_list = list(val)
            
            if len(bit_list) == expected_dim:
                valid_count += 1
                counts.append(len(bit_list))
            else:
                invalid_count += 1
                # Log first few mismatches for debugging
                if len(issues) < 5:
                    issues.append(f"Row {idx}: Expected dim {expected_dim}, got {len(bit_list)}")
        except Exception as e:
            invalid_count += 1
            if len(issues) < 5:
                issues.append(f"Row {idx}: Failed to parse fingerprint: {str(e)}")

    if invalid_count > 0:
        passed = False
        issues.append(f"Found {invalid_count} invalid fingerprints out of {len(df)} rows.")
    
    # Check magnitude (should be 2048, not 10 or 100)
    if valid_count > 0:
        avg_dim = np.mean(counts) if counts else 0
        if avg_dim < 1000: # Heuristic check for "high-dimensional"
            passed = False
            issues.append(f"Average fingerprint dimension is {avg_dim:.1f}, expected ~{expected_dim}.")

    return {
        "passed": passed,
        "issues": issues,
        "details": {
            "expected_dimension": expected_dim,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "total_rows": len(df),
            "average_dimension": float(np.mean(counts)) if counts else 0.0
        }
    }

def validate_dataset(dataset_path: Path, output_path: Path) -> Dict[str, Any]:
    """Run all validation steps."""
    logger.info("Starting fingerprint validation...")
    
    # 1. Load
    try:
        df = load_dataset(dataset_path)
    except FileNotFoundError as e:
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": str(pd.Timestamp.now())
        }

    # 2. Define Key Columns
    # Based on T013 output: SMILES, fingerprint, lattice params, space group
    key_columns = ["smiles", "fingerprint", "space_group"]
    # Add lattice params if they exist in the schema, usually 'a', 'b', 'c', 'alpha', 'beta', 'gamma'
    lattice_cols = ['a', 'b', 'c', 'alpha', 'beta', 'gamma']
    existing_lattice = [c for c in lattice_cols if c in df.columns]
    if existing_lattice:
        key_columns.extend(existing_lattice)

    # 3. Null Check
    null_result = validate_no_nulls(df, key_columns)

    # 4. Dimension Check
    dim_result = validate_fingerprint_dimension(df, FINGERPRINT_COL, EXPECTED_DIM)

    # 5. Aggregate Result
    overall_passed = null_result["passed"] and dim_result["passed"]
    
    result = {
        "status": "passed" if overall_passed else "failed",
        "timestamp": str(pd.Timestamp.now()),
        "dataset_path": str(dataset_path),
        "checks": {
            "null_check": null_result,
            "dimension_check": dim_result
        }
    }

    # 6. Save Output
    ensure_directory(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Validation complete. Status: {result['status']}")
    logger.info(f"Output written to: {output_path}")
    
    return result

def main():
    """Main entry point."""
    try:
        dataset_path = get_path_processed_data(DATASET_FILE)
        output_path = get_path_validation(OUTPUT_FILE)
        
        result = validate_dataset(dataset_path, output_path)
        
        if result["status"] == "failed":
            logger.error("Validation failed. See logs for details.")
            sys.exit(1)
        else:
            logger.info("Validation passed.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        # Write a failure report
        output_path = get_path_validation(OUTPUT_FILE)
        ensure_directory(output_path.parent)
        with open(output_path, 'w') as f:
            json.dump({
                "status": "error",
                "error": str(e),
                "timestamp": str(pd.Timestamp.now())
            }, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
