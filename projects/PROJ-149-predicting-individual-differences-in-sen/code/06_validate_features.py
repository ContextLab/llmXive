"""
T035a: Validate schema of data/processed/features_clr.csv
Validates:
- No nulls in required columns
- Correct columns exist
- Valid RT range (100ms to 2000ms) as per FR-004
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Import config utilities for path resolution and directory creation
from config import get_path, ensure_dirs

REQUIRED_COLUMNS = [
    "participant_id",
    "median_rt",
    "delta_clr",
    "theta_clr",
    "alpha_clr",
    "low_beta_clr",
    "high_beta_clr",
    "gamma_clr",
]

def validate_schema(
    input_path: str,
    rt_min: float = 100.0,
    rt_max: float = 2000.0,
    verbose: bool = True
) -> dict:
    """
    Validate the schema of the features CSV.

    Args:
        input_path: Path to the features CSV file.
        rt_min: Minimum allowed RT in ms.
        rt_max: Maximum allowed RT in ms.
        verbose: If True, print validation details.

    Returns:
        dict: Validation results with 'valid' boolean and 'errors' list.
    """
    errors = []
    warnings = []

    # 1. Check file existence
    if not os.path.exists(input_path):
        errors.append(f"File not found: {input_path}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # 2. Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        errors.append(f"Failed to read CSV: {str(e)}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if verbose:
        print(f"Loaded {len(df)} rows from {input_path}")

    # 3. Check required columns
    # Expected columns based on T015: participant_id, median_rt, delta, theta, alpha, low_beta, high_beta, gamma (CLR transformed)
    required_cols = ['participant_id', 'median_rt', 'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    else:
        if verbose:
            print(f"All required columns present: {required_cols}")

    # 4. Check for nulls
    null_counts = df[required_cols].isnull().sum()
    null_cols_with_data = null_counts[null_counts > 0]

    if not null_cols_with_data.empty:
        for col, count in null_cols_with_data.items():
            errors.append(f"Column '{col}' contains {count} null values")
    else:
        if verbose:
            print("No null values found in required columns.")

    # 5. Validate RT range (FR-004)
    if 'median_rt' in df.columns:
        rt_outliers = df[
            (df['median_rt'] < rt_min) | (df['median_rt'] > rt_max)
        ]
        if not rt_outliers.empty:
            count = len(rt_outliers)
            errors.append(f"Found {count} participants with median_rt outside [{rt_min}, {rt_max}] ms range")
            if verbose:
                print(f"RT Outliers (count={count}):")
                print(rt_outliers[['participant_id', 'median_rt']].head())
        else:
            if verbose:
                print(f"RT range valid for all participants ({rt_min}-{rt_max} ms).")

    # 6. Validate numeric types (basic check)
    numeric_cols = ['median_rt', 'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    for col in numeric_cols:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' is not numeric (dtype: {df[col].dtype})")

    # 7. Summary
    is_valid = len(errors) == 0

    if verbose:
        print("\n--- Validation Summary ---")
        if is_valid:
            print("STATUS: VALID")
        else:
            print("STATUS: INVALID")
            print(f"Errors: {len(errors)}")
            for err in errors:
                print(f"  - {err}")
        if warnings:
            print(f"Warnings: {len(warnings)}")
            for warn in warnings:
                print(f"  - {warn}")

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "column_count": len(df.columns)
    }


def main():
    parser = argparse.ArgumentParser(description="Validate features_clr.csv schema (T035a)")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to features CSV. Defaults to config path."
    )
    parser.add_argument(
        "--rt-min",
        type=float,
        default=100.0,
        help="Minimum RT in ms (default: 100)"
    )
    parser.add_argument(
        "--rt-max",
        type=float,
        default=2000.0,
        help="Maximum RT in ms (default: 2000)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    args = parser.parse_args()

    # Resolve input path
    if args.input:
        input_path = args.input
    else:
        # Default path from config/tasks.md
        # The task description says: Validate schema of `data/processed/features_clr.csv`
        try:
            # Attempt to use the config helper if it supports the key
            input_path = get_path("features_clr")
        except (ValueError, TypeError):
            # Fallback to direct relative path if config key doesn't exist
            input_path = "data/processed/features_clr.csv"

    # Ensure output directory exists (though this task is validation, we might write a log)
    # We'll write a validation log if needed, but for now just validate.
    # If we were to write a report, we'd do:
    # log_path = get_path("processed", "validation_log.json") # if supported
    # ensure_dirs(log_path)

    print(f"Validating: {input_path}")
    result = validate_schema(
        input_path,
        rt_min=args.rt_min,
        rt_max=args.rt_max,
        verbose=not args.quiet
    )

    # Exit with error code if invalid
    if not result["valid"]:
        sys.exit(1)

    sys.exit(0)

    # Determine output log path
    if args.output_log:
        output_log_path = args.output_log
    else:
        output_log_path = get_path("processed", "validation_log.json")
        # Ensure directory exists
        ensure_dirs(Path(output_log_path).parent)

    print(f"Validating schema of: {input_path}")

    validation_result = {
        "status": "success",
        "file": input_path,
        "errors": [],
        "warnings": [],
    }

    try:
        validate_schema(input_path)
        print("✓ Validation PASSED: Schema is correct, no nulls, RT in range.")
        validation_result["message"] = "Validation passed"
    except FileNotFoundError as e:
        print(f"✗ Validation FAILED: {e}")
        validation_result["status"] = "failed"
        validation_result["errors"].append(str(e))
    except ValueError as e:
        print(f"✗ Validation FAILED: {e}")
        validation_result["status"] = "failed"
        validation_result["errors"].append(str(e))

    # Write log
    import json
    with open(output_log_path, "w") as f:
        json.dump(validation_result, f, indent=2)
    print(f"Validation log written to: {output_log_path}")

    # Exit with code 1 if failed
    if validation_result["status"] == "failed":
        sys.exit(1)

if __name__ == "__main__":
    main()