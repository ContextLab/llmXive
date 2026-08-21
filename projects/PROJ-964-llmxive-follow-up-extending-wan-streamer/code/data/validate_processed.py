import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required columns and their expected types
REQUIRED_COLUMNS = {
    'timestamp': (int, np.integer, float, np.floating),
    'semantic_feature': (list, np.ndarray),
    'prosodic_feature': (list, np.ndarray),
    'latent_delta_magnitude': (int, np.integer, float, np.floating),
    'turn_label': (str, int, np.integer)
}

def load_sampled_dataset(path: Path) -> pd.DataFrame:
    """Load the sampled dataset from parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Sampled dataset not found at {path}")
    
    logger.info(f"Loading sampled dataset from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def validate_columns_exist(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check that all required columns are present."""
    missing = [col for col in REQUIRED_COLUMNS.keys() if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False, missing
    logger.info("All required columns are present")
    return True, []

def validate_no_nulls(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check that required columns have no null values."""
    null_issues = []
    for col in REQUIRED_COLUMNS.keys():
        if df[col].isnull().any():
            count = df[col].isnull().sum()
            null_issues.append(f"{col}: {count} null values")
            logger.error(f"Column '{col}' has {count} null values")
    
    if null_issues:
        logger.error(f"Null value issues found: {null_issues}")
        return False, null_issues
    
    logger.info("No null values found in required columns")
    return True, []

def validate_types(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check that required columns have correct types."""
    type_issues = []
    
    for col, expected_types in REQUIRED_COLUMNS.items():
        # Special handling for list/ndarray columns (semantic/prosodic features)
        if expected_types == (list, np.ndarray):
            # Check if values are list-like or array-like
            sample_val = df[col].iloc[0] if len(df) > 0 else None
            if sample_val is None:
                type_issues.append(f"{col}: values are None")
            elif not isinstance(sample_val, (list, np.ndarray)):
                type_issues.append(f"{col}: expected list/ndarray, got {type(sample_val)}")
            else:
                logger.info(f"Column '{col}' has correct type (list/ndarray)")
        else:
            # For scalar types, check if all values are instances of expected types
            if not df[col].apply(lambda x: isinstance(x, expected_types)).all():
                sample_val = df[col].iloc[0] if len(df) > 0 else None
                type_issues.append(f"{col}: expected {expected_types}, got {type(sample_val)}")
            else:
                logger.info(f"Column '{col}' has correct type")
    
    if type_issues:
        logger.error(f"Type issues found: {type_issues}")
        return False, type_issues
    
    logger.info("All required columns have correct types")
    return True, []

def write_validation_report(report_path: Path, passed: bool, issues: list[str]):
    """Write the validation report to disk."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("Data Validation Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Status: {'PASS' if passed else 'FAIL'}\n\n")
        
        if issues:
            f.write("Issues found:\n")
            for issue in issues:
                f.write(f"  - {issue}\n")
        else:
            f.write("No issues found. All validations passed.\n")
        
        f.write("\n" + "=" * 50 + "\n")
    
    logger.info(f"Validation report written to {report_path}")

def main():
    """Main entry point for data validation."""
    parser = argparse.ArgumentParser(description="Validate processed dataset")
    parser.add_argument(
        '--input', 
        type=Path, 
        default=Path('data/processed/sampled_dataset.parquet'),
        help='Path to the sampled dataset parquet file'
    )
    parser.add_argument(
        '--output', 
        type=Path, 
        default=Path('data/logs/validation_report.txt'),
        help='Path to write the validation report'
    )
    
    args = parser.parse_args()
    
    try:
        # Load dataset
        df = load_sampled_dataset(args.input)
        
        # Run validations
        all_passed = True
        all_issues = []
        
        # Check columns exist
        col_ok, col_issues = validate_columns_exist(df)
        all_passed = all_passed and col_ok
        all_issues.extend(col_issues)
        
        if col_ok:
            # Check for nulls
            null_ok, null_issues = validate_no_nulls(df)
            all_passed = all_passed and null_ok
            all_issues.extend(null_issues)
            
            # Check types
            if null_ok:
                type_ok, type_issues = validate_types(df)
                all_passed = all_passed and type_ok
                all_issues.extend(type_issues)
        
        # Write report
        write_validation_report(args.output, all_passed, all_issues)
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        # Write failure report
        write_validation_report(args.output, False, [str(e)])
        sys.exit(1)

if __name__ == '__main__':
    main()