"""
T016: Validate schema of data/processed/features.csv
Checks:
  1. File exists
  2. No null values in required columns
  3. Correct column names (expected schema)
  4. Valid RT range (median_rt between 100ms and 2000ms)
  5. Participant IDs are unique
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to allow importing config
sys.path.insert(0, str(Path(__file__).parent))
from config import get_path, ensure_dirs

# Expected columns based on T015 output (relative power + CLR + behavioral)
EXPECTED_COLUMNS = [
    'participant_id',
    'delta_rel', 'theta_rel', 'alpha_rel', 'beta_low_rel', 'beta_high_rel', 'gamma_rel',
    'delta_clr', 'theta_clr', 'alpha_clr', 'beta_low_clr', 'beta_high_clr', 'gamma_clr',
    'median_rt'
]

def validate_schema(input_path: Path) -> dict:
    """
    Validates the features.csv file against the expected schema.
    
    Returns a dict with validation results:
    {
        "valid": bool,
        "errors": list of error messages,
        "warnings": list of warning messages,
        "stats": dict of summary stats (row count, null counts, etc.)
    }
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "stats": {}
    }

    # 1. Check file existence
    if not input_path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {input_path}")
        return result

    # 2. Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Failed to load CSV: {str(e)}")
        return result

    result["stats"]["row_count"] = len(df)
    result["stats"]["column_count"] = len(df.columns)

    # 3. Check for expected columns
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        result["valid"] = False
        result["errors"].append(f"Missing required columns: {missing_cols}")
    
    extra_cols = [col for col in df.columns if col not in EXPECTED_COLUMNS]
    if extra_cols:
        result["warnings"].append(f"Extra columns found (ignored): {extra_cols}")

    # 4. Check for null values in required columns
    # We check all columns that are not participant_id (which might be string ID)
    required_numeric_cols = [c for c in EXPECTED_COLUMNS if c != 'participant_id' and c in df.columns]
    null_counts = {}
    has_nulls = False
    
    for col in required_numeric_cols:
        null_count = df[col].isna().sum()
        null_counts[col] = null_count
        if null_count > 0:
            has_nulls = True
            result["valid"] = False
            result["errors"].append(f"Column '{col}' has {null_count} null values")
    
    result["stats"]["null_counts"] = null_counts

    # 5. Validate RT range (100ms to 2000ms)
    if 'median_rt' in df.columns:
        rt_min = df['median_rt'].min()
        rt_max = df['median_rt'].max()
        result["stats"]["rt_min"] = rt_min
        result["stats"]["rt_max"] = rt_max
        
        if rt_min < 100:
            result["valid"] = False
            result["errors"].append(f"median_rt minimum ({rt_min}) is below 100ms threshold")
        
        if rt_max > 2000:
            result["valid"] = False
            result["errors"].append(f"median_rt maximum ({rt_max}) exceeds 2000ms threshold")

    # 6. Check for duplicate participant IDs
    if 'participant_id' in df.columns:
        dup_count = df['participant_id'].duplicated().sum()
        if dup_count > 0:
            result["valid"] = False
            result["errors"].append(f"Found {dup_count} duplicate participant_ids")
        result["stats"]["unique_participants"] = df['participant_id'].nunique()

    # 7. Validate that all power values are positive (relative power should be > 0)
    power_cols = [c for c in df.columns if c.endswith('_rel') and c != 'median_rt']
    for col in power_cols:
        if col in df.columns:
            if (df[col] <= 0).any():
                result["valid"] = False
                result["errors"].append(f"Column '{col}' contains non-positive values (expected > 0 for relative power)")

    return result

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to features.csv (default: from config)"
    )
    args = parser.parse_args()

    # Determine input path
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = get_path("processed", "features.csv")

    print(f"Validating: {input_path}")
    validation_result = validate_schema(input_path)

    # Print results
    print("\n=== Validation Report ===")
    print(f"Valid: {validation_result['valid']}")
    print(f"Rows: {validation_result['stats'].get('row_count', 'N/A')}")
    print(f"Columns: {validation_result['stats'].get('column_count', 'N/A')}")
    
    if validation_result['stats'].get('unique_participants'):
        print(f"Unique Participants: {validation_result['stats']['unique_participants']}")
    
    if 'rt_min' in validation_result['stats'] and 'rt_max' in validation_result['stats']:
        print(f"RT Range: {validation_result['stats']['rt_min']:.2f}ms - {validation_result['stats']['rt_max']:.2f}ms")

    if validation_result['errors']:
        print("\nErrors:")
        for err in validation_result['errors']:
            print(f"  - {err}")

    if validation_result['warnings']:
        print("\nWarnings:")
        for warn in validation_result['warnings']:
            print(f"  - {warn}")

    # Exit with error code if validation failed
    if not validation_result['valid']:
        print("\nValidation FAILED.")
        sys.exit(1)
    else:
        print("\nValidation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()