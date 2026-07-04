"""
Verify External Golden Set for Cognitive Load Optimization Pipeline.

This script ensures that `data/processed/golden_set.csv` exists and contains
at least 50 expert-labeled interactions. It does NOT generate synthetic data.
If the file is missing or insufficient, it exits with a clear error code.

Dependencies:
    - pandas
    - pathlib

Usage:
    python code/verify_golden_set.py
"""

import sys
import os
from pathlib import Path

import pandas as pd


def verify_golden_set(
    path: Path,
    min_rows: int = 50,
    required_columns: list[str] | None = None,
) -> bool:
    """
    Verify the existence and validity of the Golden Set CSV.

    Args:
        path: Path to the golden_set.csv file.
        min_rows: Minimum number of rows required (default 50).
        required_columns: Optional list of columns that must exist.

    Returns:
        True if valid, False otherwise.
    """
    if not path.exists():
        print(f"ERROR: Golden set file not found at: {path.resolve()}", file=sys.stderr)
        print("This task requires an external, expert-labeled dataset.", file=sys.stderr)
        print("Please fetch `data/processed/golden_set.csv` manually or run T006b to create it.", file=sys.stderr)
        return False

    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"ERROR: Failed to read Golden Set CSV: {e}", file=sys.stderr)
        return False

    if len(df) < min_rows:
        print(f"ERROR: Golden set has {len(df)} rows, but requires at least {min_rows}.", file=sys.stderr)
        print("This task requires an external, expert-labeled dataset with sufficient sample size.", file=sys.stderr)
        return False

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            print(f"ERROR: Golden set is missing required columns: {missing}", file=sys.stderr)
            return False

    print(f"SUCCESS: Golden set verified at {path.resolve()} with {len(df)} rows.")
    return True


def main():
    """Entry point for the script."""
    # Define project root relative to this file location
    # Assuming script is at code/verify_golden_set.py
    project_root = Path(__file__).resolve().parent.parent
    golden_set_path = project_root / "data" / "processed" / "golden_set.csv"

    # Define expected columns based on the task description (expert_load_score or concurrent self-reports)
    # We check for at least one of these to ensure it's an expert-labeled set
    required_cols = ["expert_load_score"]

    success = verify_golden_set(golden_set_path, min_rows=50, required_columns=required_cols)

    if not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()