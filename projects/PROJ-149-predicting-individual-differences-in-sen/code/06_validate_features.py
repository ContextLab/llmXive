import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

REQUIRED_COLUMNS = [
    'participant_id',
    'median_rt',
    'delta_rel_clr',
    'theta_rel_clr',
    'alpha_rel_clr',
    'beta_low_rel_clr',
    'beta_high_rel_clr',
    'gamma_rel_clr'
]

RT_LOWER_BOUND = 1000.0
RT_UPPER_BOUND = 2000.0

def validate_schema(input_path: str) -> tuple[bool, list[str]]:
    """
    Validates the schema and content of the features CSV.
    
    Checks:
    1. File exists and is readable.
    2. Contains all required columns.
    3. No null values in any column.
    4. median_rt is within valid bounds (>= 1000ms).
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    path = Path(input_path)
    if not path.exists():
        errors.append(f"File not found: {input_path}")
        return False, errors

    try:
        df = pd.read_csv(path)
    except Exception as e:
        errors.append(f"Failed to read CSV: {str(e)}")
        return False, errors

    # Check columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for nulls
    null_counts = df.isnull().sum()
    if null_counts.any():
        null_cols = null_counts[null_counts > 0].index.tolist()
        errors.append(f"Columns with null values: {null_cols}")

    # Check RT bounds
    if 'median_rt' in df.columns:
        invalid_rt = df[df['median_rt'] < RT_LOWER_BOUND]
        if len(invalid_rt) > 0:
            errors.append(f"Found {len(invalid_rt)} rows with median_rt < {RT_LOWER_BOUND}ms")
        
        # Optional: check upper bound if data is dirty, though task specifies lower bound
        invalid_rt_high = df[df['median_rt'] > RT_UPPER_BOUND]
        if len(invalid_rt_high) > 0:
            errors.append(f"Found {len(invalid_rt_high)} rows with median_rt > {RT_UPPER_BOUND}ms (outliers)")

    is_valid = len(errors) == 0
    return is_valid, errors

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema and content.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to features.csv. Defaults to data/processed/features.csv."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if validation fails."
    )
    args = parser.parse_args()

    input_path = args.input if args.input else str(get_path("processed", "features.csv"))
    
    print(f"Validating: {input_path}")
    is_valid, errors = validate_schema(input_path)

    if is_valid:
        print("Validation PASSED: Schema is correct, no nulls, RT bounds valid.")
        sys.exit(0)
    else:
        print("Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        if args.strict:
            sys.exit(1)
        else:
            # Non-strict mode prints errors but exits 0 (or 1 depending on policy, 
            # but task implies blocking downstream if failed, so usually 1 is safer for CI)
            sys.exit(1)

if __name__ == "__main__":
    main()