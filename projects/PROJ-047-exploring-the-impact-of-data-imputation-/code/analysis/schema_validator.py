import os
import pandas as pd
import sys
from typing import List, Set

REQUIRED_COLUMNS: Set[str] = {
    "beta",
    "method",
    "estimator",
    "ate",
    "bias",
    "rmse",
    "coverage_rate",
    "seed",
    "run_id",
    "ground_truth_ate",
    "beta_value",
    "status",
}

def validate_schema(input_path: str) -> bool:
    """
    Validate that the input CSV contains all required columns for T031 plots.
    
    Args:
        input_path: Path to the CSV file to validate.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    actual_columns = set(df.columns)
    missing_columns = REQUIRED_COLUMNS - actual_columns
    
    if missing_columns:
        error_msg = (
            f"Schema validation failed. Missing required columns: {missing_columns}. "
            f"Expected: {REQUIRED_COLUMNS}, Found: {actual_columns}"
        )
        raise ValueError(error_msg)
    
    # Additional check: ensure no empty required fields in critical columns
    critical_fields = ["beta", "method", "estimator", "ate", "ground_truth_ate", "coverage_rate"]
    for field in critical_fields:
        if df[field].isna().any():
            raise ValueError(f"Column '{field}' contains null values, which is not allowed.")
    
    return True

def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate simulation summary CSV schema")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the simulation summary CSV file"
    )
    args = parser.parse_args()
    
    try:
        validate_schema(args.input)
        print(f"Schema validation passed for {args.input}")
        sys.exit(0)
    except (FileNotFoundError, ValueError) as e:
        print(f"Schema validation failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
