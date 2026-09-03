"""
T035a: Validate schema of data/processed/features.csv.

This script verifies:
1. Required columns exist.
2. No null values in required columns.
3. median_rt is within a plausible response time range (50ms - 5000ms).
4. Data types are correct.

It exits with code 0 if valid, code 1 if invalid.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parents[0]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "features.csv"
DEFAULT_OUTPUT_LOG = PROJECT_ROOT / "data" / "interim" / "validation_log.json"

REQUIRED_COLUMNS = [
    "participant_id",
    "median_rt",
    "delta_rel",
    "theta_rel",
    "alpha_rel",
    "low_beta_rel",
    "high_beta_rel",
    "gamma_rel"
]

MIN_RT_MS = 50.0
MAX_RT_MS = 5000.0

def validate_schema(input_path: Path, output_log: Path):
    """
    Validate the schema of the features CSV file.
    
    Returns a tuple (is_valid, validation_report_dict).
    """
    report = {
        "file": str(input_path),
        "valid": True,
        "errors": [],
        "warnings": [],
        "row_count": 0,
        "column_count": 0
    }

    # 1. Check file existence
    if not input_path.exists():
        report["valid"] = False
        report["errors"].append(f"File not found: {input_path}")
        return False, report

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Failed to read CSV: {str(e)}")
        return False, report

    report["row_count"] = len(df)
    report["column_count"] = len(df.columns)

    # 2. Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        report["valid"] = False
        report["errors"].append(f"Missing required columns: {sorted(missing_cols)}")
    else:
        report["warnings"].append("All required columns present.")

    if not report["valid"]:
        # If columns are missing, we can't reliably check values
        save_report(output_log, report)
        return False, report

    # 3. Check for nulls
    null_counts = df[REQUIRED_COLUMNS].isna().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        report["valid"] = False
        for col, count in null_cols.items():
            report["errors"].append(f"Column '{col}' has {count} null values.")

    # 4. Check median_rt range
    if "median_rt" in df.columns:
        rt_col = df["median_rt"]
        invalid_low = rt_col[rt_col < MIN_RT_MS]
        invalid_high = rt_col[rt_col > MAX_RT_MS]
        
        if len(invalid_low) > 0:
            report["valid"] = False
            report["errors"].append(
                f"Found {len(invalid_low)} participants with RT < {MIN_RT_MS}ms."
            )
        if len(invalid_high) > 0:
            report["valid"] = False
            report["errors"].append(
                f"Found {len(invalid_high)} participants with RT > {MAX_RT_MS}ms."
            )

    # 5. Check numeric types for non-ID columns
    numeric_cols = [c for c in REQUIRED_COLUMNS if c != "participant_id"]
    for col in numeric_cols:
        if col in df.columns:
            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    # Try to coerce to see if it's just a string representation of numbers
                    pd.to_numeric(df[col], errors='raise')
                    report["warnings"].append(f"Column '{col}' is object type but contains numeric data.")
                except (ValueError, TypeError):
                    report["valid"] = False
                    report["errors"].append(f"Column '{col}' is not numeric.")

    # 6. Check participant_id non-empty
    if "participant_id" in df.columns:
        empty_ids = df["participant_id"].astype(str).str.strip().eq("")
        if empty_ids.any():
            report["valid"] = False
            report["errors"].append("Found empty participant_id values.")

    if report["valid"]:
        report["warnings"].append("Schema validation passed.")
    
    save_report(output_log, report)
    return report["valid"], report

def save_report(output_path: Path, report: dict):
    """Save validation report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="Validate schema of data/processed/features.csv"
    )
    parser.add_argument(
        "--input", 
        type=Path, 
        default=DEFAULT_INPUT_PATH,
        help=f"Path to features CSV (default: {DEFAULT_INPUT_PATH})"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=DEFAULT_OUTPUT_LOG,
        help=f"Path to validation log JSON (default: {DEFAULT_OUTPUT_LOG})"
    )

    args = parser.parse_args()

    is_valid, report = validate_schema(args.input, args.output)

    if is_valid:
        print(f"Validation PASSED: {args.input}")
        print(f"  Rows: {report['row_count']}, Columns: {report['column_count']}")
        sys.exit(0)
    else:
        print(f"Validation FAILED: {args.input}")
        for err in report["errors"]:
            print(f"  ERROR: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()