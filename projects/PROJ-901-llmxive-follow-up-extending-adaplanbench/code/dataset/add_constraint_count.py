"""
Script to add the `constraint_count` metadata column to the filtered dataset.
This column is derived from the length of the `progressive_constraints` field
for each task, ensuring semantic alignment with US-1.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_paths, get_dataset_config

def compute_constraint_count(row: pd.Series) -> int:
    """
    Compute the constraint count for a single row.
    Extracts the 'progressive_constraints' field and returns its length.
    If the field is missing or not a list, returns 0 (or raises an error if strict).
    """
    progressive_constraints = row.get('progressive_constraints')
    if progressive_constraints is None:
        # This should not happen if filtering was done correctly
        return 0
    if isinstance(progressive_constraints, str):
        # Try to parse JSON string if it's stored as a string
        try:
            progressive_constraints = json.loads(progressive_constraints)
        except json.JSONDecodeError:
            return 0
    if isinstance(progressive_constraints, list):
        return len(progressive_constraints)
    return 0

def add_constraint_count_column(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Load the filtered tasks CSV, add the `constraint_count` column, and save.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load the dataset
    df = pd.read_csv(input_path)

    # Verify that 'progressive_constraints' column exists
    if 'progressive_constraints' not in df.columns:
        raise ValueError(f"Input file missing required column 'progressive_constraints': {input_path}")

    # Compute constraint_count
    df['constraint_count'] = df.apply(compute_constraint_count, axis=1)

    # Ensure constraint_count is integer type
    df['constraint_count'] = df['constraint_count'].astype(int)

    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Added 'constraint_count' column to {len(df)} tasks.")
    print(f"Output saved to: {output_path}")
    print(f"Sample constraint counts: {df['constraint_count'].head().tolist()}")

    return df

def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Add constraint_count column to filtered tasks.")
    parser.add_argument("--input", type=str, required=False,
                        help="Path to input filtered tasks CSV. Defaults to config path.")
    parser.add_argument("--output", type=str, required=False,
                        help="Path to output CSV. Defaults to config path.")
    args = parser.parse_args()

    paths = get_paths()
    dataset_config = get_dataset_config()

    input_path = Path(args.input) if args.input else paths.data_processed / "filtered_tasks.csv"
    output_path = Path(args.output) if args.output else paths.data_processed / "filtered_tasks.csv"

    # If input and output are the same, we overwrite (standard for this task)
    # If different, we write to new location

    try:
        df = add_constraint_count_column(input_path, output_path)
        # Verify the output
        if output_path.exists():
            print(f"Success: Output file created at {output_path}")
            # Optional: validate a few rows
            sample = df.sample(min(5, len(df)))
            for _, row in sample.iterrows():
                print(f"  Task {row['task_id']}: constraint_count={row['constraint_count']}")
        else:
            raise RuntimeError(f"Output file was not created: {output_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
