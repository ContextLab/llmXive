"""
Schema validation for simulation results.

Validates that data/results/simulation_summary.csv contains all columns
required for downstream analysis and plotting tasks (T031, T042).
"""
import os
import pandas as pd
import sys

# Define the required schema based on T029c and T031 requirements
# Schema: [beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta_value, status]
REQUIRED_COLUMNS = [
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
    "status"
]

def validate_schema(file_path: str) -> bool:
    """
    Validates that the CSV file at file_path contains all required columns.
    
    Args:
        file_path: Path to the simulation_summary.csv file.
        
    Returns:
        True if validation passes.
        
    Raises:
        ValueError: If the file does not exist or is missing required columns.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Validation failed: File not found at {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Validation failed: Could not read CSV file: {e}")
    
    if df.empty:
        # If the file exists but is empty, we check if it has headers or raise an error
        # Based on T029c, the file should be populated. An empty file implies no runs.
        # We raise an error to prevent downstream tasks from crashing on empty data.
        raise ValueError("Validation failed: Simulation summary CSV is empty. No runs were recorded.")
    
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"Validation failed: Missing required columns in {file_path}: {missing_columns}. "
            f"Expected columns: {REQUIRED_COLUMNS}. Found columns: {list(df.columns)}"
        )
    
    # Additional type/value checks could go here if needed, 
    # but the task specifically asks for column presence validation.
    return True

def main():
    """
    Entry point for schema validation.
    Validates data/results/simulation_summary.csv.
    """
    file_path = "data/results/simulation_summary.csv"
    
    try:
        validate_schema(file_path)
        print(f"Schema validation passed for {file_path}")
        print(f"Found {len(REQUIRED_COLUMNS)} required columns.")
        return 0
    except ValueError as e:
        print(f"Schema validation FAILED: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
