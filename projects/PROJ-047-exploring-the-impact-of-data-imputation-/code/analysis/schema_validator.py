"""
Schema validation for simulation results.

Validates that data/results/simulation_summary.csv contains all columns
required for T031 plots (bias_vs_beta, coverage_vs_beta, bias_distributions).
"""
import os
import pandas as pd
import sys
from typing import List, Set

# Required columns for T031 plots (bias_vs_beta, coverage_vs_beta, bias_distributions)
# Based on T029c schema definition:
# [beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta_value, status]
REQUIRED_COLUMNS: Set[str] = {
    'beta',
    'method',
    'estimator',
    'ate',
    'bias',
    'rmse',
    'coverage_rate',
    'seed',
    'run_id',
    'ground_truth_ate',
    'beta_value',
    'status'
}

# Additional columns that might be useful but are not strictly required for T031
OPTIONAL_COLUMNS: Set[str] = {
    'alpha',
    'vif_max',
    'missing_rate'
}

def validate_schema(input_path: str) -> bool:
    """
    Validate that the input CSV file contains all required columns.
    
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
            f"Schema validation failed. Missing required columns: {sorted(missing_columns)}\n"
            f"Expected columns: {sorted(REQUIRED_COLUMNS)}\n"
            f"Actual columns: {sorted(actual_columns)}"
        )
        raise ValueError(error_msg)
    
    # Check for any unexpected columns (optional warning)
    unexpected_columns = actual_columns - REQUIRED_COLUMNS - OPTIONAL_COLUMNS
    if unexpected_columns:
        print(f"Warning: Unexpected columns found: {sorted(unexpected_columns)}")
    
    print(f"Schema validation passed. Found {len(actual_columns)} columns.")
    return True

def main():
    """Main entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate simulation summary schema')
    parser.add_argument(
        '--input',
        type=str,
        default='data/results/simulation_summary.csv',
        help='Path to the CSV file to validate'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed validation information'
    )
    
    args = parser.parse_args()
    
    try:
        validate_schema(args.input)
        if args.verbose:
            df = pd.read_csv(args.input)
            print(f"File contains {len(df)} rows.")
            print(f"Column types:\n{df.dtypes}")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()