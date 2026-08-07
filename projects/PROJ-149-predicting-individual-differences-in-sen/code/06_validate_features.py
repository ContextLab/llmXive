"""
Task T016: Validate schema of data/processed/features.csv.

Validates the output of T015 (05_compute_relative_power.py) to ensure:
1. File exists and is readable.
2. Contains required columns (participant_id, median_rt, and band powers).
3. No null values in critical columns.
4. median_rt is within valid physiological range (100ms - 2000ms).

Outputs:
- Prints validation summary to stdout.
- Exits with code 0 if valid, 1 if invalid.
- Optionally generates a validation report log.
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, get_all_band_names, get_band_freqs
import utils.stats_helpers as stats_helpers


def validate_schema(input_path: Path) -> dict:
    """
    Validates the schema and content of the features CSV.
    
    Args:
        input_path: Path to the features CSV file.
        
    Returns:
        dict: Validation results with 'valid' boolean and 'errors' list.
    """
    errors = []
    warnings = []
    
    # 1. Check file existence
    if not input_path.exists():
        return {
            "valid": False,
            "errors": [f"File not found: {input_path}"],
            "warnings": []
        }
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to read CSV: {str(e)}"],
            "warnings": []
        }
    
    if df.empty:
        return {
            "valid": False,
            "errors": ["DataFrame is empty"],
            "warnings": []
        }
    
    # 2. Check required columns
    # Expected columns: participant_id, median_rt, and relative power bands
    all_bands = get_all_band_names()
    # T015 produces relative power columns, typically named 'rel_<band>' or similar
    # Based on T015 description: "produce data/processed/features.csv" with relative power
    # We expect columns like: participant_id, median_rt, rel_delta, rel_theta, etc.
    required_base_cols = ["participant_id", "median_rt"]
    required_rel_cols = [f"rel_{band}" for band in all_bands]
    required_cols = required_base_cols + required_rel_cols
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for unexpected extra columns (optional warning)
    existing_cols = set(df.columns)
    expected_cols_set = set(required_cols)
    extra_cols = existing_cols - expected_cols_set
    if extra_cols:
        warnings.append(f"Extra columns detected (ignoring): {extra_cols}")
    
    # 3. Check for nulls in critical columns
    critical_cols = required_cols
    null_counts = df[critical_cols].isnull().sum()
    null_cols_with_values = null_counts[null_counts > 0]
    
    if not null_cols_with_values.empty:
        for col, count in null_cols_with_values.items():
            errors.append(f"Column '{col}' contains {count} null values")
    
    # 4. Validate RT range (100ms to 2000ms)
    if "median_rt" in df.columns:
        rt_min = df["median_rt"].min()
        rt_max = df["median_rt"].max()
        
        if rt_min < 100:
            outliers_low = df[df["median_rt"] < 100].shape[0]
            errors.append(f"Found {outliers_low} participants with median RT < 100ms (physiologically impossible)")
        
        if rt_max > 2000:
            outliers_high = df[df["median_rt"] > 2000].shape[0]
            errors.append(f"Found {outliers_high} participants with median RT > 2000ms (exceeds exclusion threshold)")
    
    # 5. Validate power values are non-negative (relative power should be 0-1)
    for band in all_bands:
        col_name = f"rel_{band}"
        if col_name in df.columns:
            if (df[col_name] < 0).any():
                errors.append(f"Column '{col_name}' contains negative values (relative power cannot be negative)")
            if (df[col_name] > 1).any():
                # This might be a data issue or just a very small total power denominator
                # But relative power > 1 is physically impossible
                errors.append(f"Column '{col_name}' contains values > 1.0")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "column_count": len(df.columns)
    }


def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema and content")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to features.csv. Defaults to config path."
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="Path to write validation report (JSON). Optional."
    )
    
    args = parser.parse_args()
    
    # Determine input path
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = get_path("processed_features_csv")
    
    print(f"Validating: {input_path}")
    
    result = validate_schema(input_path)
    
    # Print results
    if result["valid"]:
        print("✅ Validation PASSED")
        print(f"   - Rows: {result['row_count']}")
        print(f"   - Columns: {result['column_count']}")
        if result["warnings"]:
            print("   - Warnings:")
            for w in result["warnings"]:
                print(f"      ⚠ {w}")
        sys.exit(0)
    else:
        print("❌ Validation FAILED")
        print(f"   - Rows: {result['row_count']}")
        print(f"   - Columns: {result['column_count']}")
        print("   - Errors:")
        for e in result["errors"]:
            print(f"      ✖ {e}")
        if result["warnings"]:
            print("   - Warnings:")
            for w in result["warnings"]:
                print(f"      ⚠ {w}")
        
        if args.output_report:
            import json
            with open(args.output_report, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nDetailed report saved to: {args.output_report}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()