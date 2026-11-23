"""
Script to validate the schema of data/processed/features.csv.
This script checks for required columns, data types, null values, and plausible ranges.
It generates a validation report and exits with code 0 on success, 1 on failure.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path, ensure_dirs

REQUIRED_COLUMNS = [
    "participant_id",
    "median_rt",
    "delta_rel",
    "theta_rel",
    "alpha_rel",
    "low_beta_rel",
    "high_beta_rel",
    "gamma_rel",
]

# Plausible response time range in milliseconds (100ms to 2000ms)
MIN_PLAUSIBLE_RT = 100.0
MAX_PLAUSIBLE_RT = 2000.0

def validate_schema(input_path):
    """
    Validates the schema of the features CSV file.
    
    Args:
        input_path (Path): Path to the features.csv file.
        
    Returns:
        dict: Validation results containing status, errors, and summary.
    """
    results = {
        "status": "success",
        "errors": [],
        "warnings": [],
        "summary": {}
    }

    if not input_path.exists():
        results["status"] = "failed"
        results["errors"].append(f"File not found: {input_path}")
        return results

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(f"Failed to read CSV: {str(e)}")
        return results

    results["summary"]["total_rows"] = len(df)
    results["summary"]["total_columns"] = len(df.columns)

    # 1. Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        results["status"] = "failed"
        results["errors"].append(f"Missing required columns: {missing_cols}")
    else:
        results["summary"]["columns_present"] = REQUIRED_COLUMNS

    # 2. Check for null values in required columns
    null_issues = []
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                null_issues.append(f"{col}: {null_count} nulls")
    
    if null_issues:
        results["status"] = "failed"
        results["errors"].append(f"Null values found in: {', '.join(null_issues)}")
    else:
        results["summary"]["null_check"] = "passed"

    # 3. Check median_rt range
    if "median_rt" in df.columns:
        rt_values = df["median_rt"]
        out_of_range = rt_values[(rt_values < MIN_PLAUSIBLE_RT) | (rt_values > MAX_PLAUSIBLE_RT)]
        if len(out_of_range) > 0:
            results["status"] = "failed"
            results["errors"].append(
                f"Found {len(out_of_range)} median_rt values outside range "
                f"[{MIN_PLAUSIBLE_RT}, {MAX_PLAUSIBLE_RT}]"
            )
        else:
            results["summary"]["rt_range_check"] = "passed"
    else:
        results["errors"].append("Cannot check RT range: 'median_rt' column missing")

    # 4. Check data types
    type_issues = []
    if "participant_id" in df.columns:
        if pd.api.types.is_numeric_dtype(df["participant_id"]):
            type_issues.append("participant_id should be string, found numeric")
    
    numeric_cols = [c for c in REQUIRED_COLUMNS if c != "participant_id"]
    for col in numeric_cols:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                type_issues.append(f"{col} should be numeric, found {df[col].dtype}")
    
    if type_issues:
        results["status"] = "failed"
        results["errors"].extend(type_issues)
    else:
        results["summary"]["type_check"] = "passed"

    return results

def save_report(results, output_path):
    """
    Saves the validation report to a JSON file.
    
    Args:
        results (dict): Validation results dictionary.
        output_path (Path): Path to save the report.
    """
    ensure_dirs(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Validation report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to features.csv. Defaults to data/processed/features.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save validation report. Defaults to data/processed/feature_validation_report.json"
    )
    
    args = parser.parse_args()

    # Resolve paths
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = get_path("processed", "features.csv")
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path("processed", "feature_validation_report.json")

    print(f"Validating schema for: {input_path}")
    
    results = validate_schema(input_path)
    
    print(f"Validation Status: {results['status'].upper()}")
    if results['errors']:
        for err in results['errors']:
            print(f"  - {err}")
    
    save_report(results, output_path)

    # Exit with code 1 if validation failed
    if results["status"] == "failed":
        sys.exit(1)
    else:
        print("Schema validation passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()