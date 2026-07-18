"""
Validate the existence and integrity of the hard-coded literature subset CSV.

This script checks for `data/raw/literature_subset.csv`.
If the file is missing or corrupted (e.g., cannot be parsed as a valid CSV with
expected columns), it raises a FileNotFoundError and exits with code 1.
No external data fetching or synthetic fallbacks are performed.
"""
import sys
import os
import pandas as pd
from pathlib import Path

# Relative to project root, assuming script is run from project root or via module
# We resolve the path relative to the data/raw directory structure defined in config
# Since we don't import config here to keep it standalone as per strict validation,
# we use the standard project path convention.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
FILE_PATH = DATA_RAW_DIR / "literature_subset.csv"

REQUIRED_COLUMNS = {
    "composition",
    "Tg",
    "Tx",
    "family"
}

def main():
    # Check existence
    if not FILE_PATH.exists():
        print(f"FATAL: literature_subset.csv missing or corrupted", file=sys.stderr)
        sys.exit(1)

    try:
        # Attempt to load and validate structure
        df = pd.read_csv(FILE_PATH)
        
        # Check for empty file
        if df.empty:
            print(f"FATAL: literature_subset.csv missing or corrupted", file=sys.stderr)
            sys.exit(1)

        # Check for required columns (case-insensitive check for robustness, then normalize)
        columns_lower = {col.lower() for col in df.columns}
        missing_cols = REQUIRED_COLUMNS - columns_lower
        
        if missing_cols:
            print(f"FATAL: literature_subset.csv missing or corrupted", file=sys.stderr)
            sys.exit(1)

        # Basic integrity check: ensure no NaN in critical columns (composition, Tg)
        # We assume 'composition' and 'Tg' are critical for the pipeline to proceed.
        critical_cols = ["composition", "Tg"]
        for col in critical_cols:
            # Find the actual column name (case preserved)
            actual_col = next((c for c in df.columns if c.lower() == col.lower()), None)
            if actual_col and df[actual_col].isna().any():
                print(f"FATAL: literature_subset.csv missing or corrupted", file=sys.stderr)
                sys.exit(1)

        print(f"Validation successful: {FILE_PATH} is valid.")
        print(f"Rows: {len(df)}, Columns: {list(df.columns)}")
        sys.exit(0)

    except Exception as e:
        # Catch any parsing errors (e.g., malformed CSV)
        print(f"FATAL: literature_subset.csv missing or corrupted", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
