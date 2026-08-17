"""
T035a: Validate schema of data/processed/features_clr.csv.

Checks:
- File exists
- No null values
- Correct columns (participant_id, median_rt, delta_clr, theta_clr, alpha_clr,
  low_beta_clr, high_beta_clr, gamma_clr)
- RT range valid: 100ms <= median_rt <= 2000ms (FR-004)
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Import from config using the defined public API
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

RT_MIN = 100.0  # ms
RT_MAX = 2000.0  # ms

def validate_schema(input_path: str) -> bool:
    """
    Validate the schema of the features_clr.csv file.

    Args:
        input_path: Path to the features_clr.csv file.

    Returns:
        True if validation passes, False otherwise.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If validation fails.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Check for required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check for null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        null_details = null_counts[null_counts > 0].to_dict()
        raise ValueError(f"Null values found in columns: {null_details}")

    # Validate RT range (FR-004)
    rt_values = df["median_rt"]
    invalid_rt = rt_values[(rt_values < RT_MIN) | (rt_values > RT_MAX)]
    if len(invalid_rt) > 0:
        raise ValueError(
            f"Found {len(invalid_rt)} RT values outside valid range "
            f"[{RT_MIN}ms, {RT_MAX}ms]. "
            f"Values: {invalid_rt.tolist()}"
        )

    # Check participant_id is not empty
    empty_ids = df[df["participant_id"].isnull() | (df["participant_id"] == "")]
    if len(empty_ids) > 0:
        raise ValueError("Found empty or null participant_id values")

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Validate schema of features_clr.csv (T035a)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to features_clr.csv. Defaults to config path.",
    )
    parser.add_argument(
        "--output-log",
        type=str,
        default=None,
        help="Path to write validation log. Defaults to config path.",
    )
    args = parser.parse_args()

    # Determine input path
    if args.input:
        input_path = args.input
    else:
        # Use config to get the standard path
        input_path = get_path("processed", "features_clr.csv")

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
