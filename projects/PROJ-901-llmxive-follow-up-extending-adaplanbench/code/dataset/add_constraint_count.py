"""
Task T014: Add constraint_count metadata column to filtered output.

This script reads the filtered tasks CSV, computes the 'constraint_count'
as the length of the 'progressive_constraints' list for each row, and
writes the result back to the same file (or a new output file if specified).
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

# Ensure the code directory is in the path for imports if running as script
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_paths

def compute_constraint_count(row: pd.Series) -> int:
    """
    Compute the number of constraints from the progressive_constraints field.
    Handles cases where the field might be a string representation of a list
    or an actual list.
    """
    constraints = row.get('progressive_constraints')
    if constraints is None:
        return 0
    
    if isinstance(constraints, list):
        return len(constraints)
    
    if isinstance(constraints, str):
        # Attempt to parse JSON if it looks like a list string
        try:
            parsed = json.loads(constraints)
            if isinstance(parsed, list):
                return len(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback: count non-empty lines or comma-separated items if not JSON
        # But per spec, it should be a list. If it's a string, we assume 0 or try to parse.
        # Given the strict schema, we return 0 if we can't parse it as a list.
        return 0
    
    return 0

def add_constraint_count_column(input_path: Path, output_path: Path = None) -> None:
    """
    Reads the filtered dataset, adds the constraint_count column, and saves it.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Loading filtered dataset from {input_path}...")
    df = pd.read_csv(input_path)

    # Verify required column exists
    if 'progressive_constraints' not in df.columns:
        raise ValueError(
            f"Input file missing required column 'progressive_constraints'. "
            f"Columns found: {list(df.columns)}"
        )

    print("Computing constraint_count...")
    df['constraint_count'] = df.apply(compute_constraint_count, axis=1)

    # Ensure constraint_count is integer type
    df['constraint_count'] = df['constraint_count'].astype(int)

    if output_path is None:
        output_path = input_path

    print(f"Writing updated dataset to {output_path}...")
    df.to_csv(output_path, index=False)

    print(f"Successfully added 'constraint_count' column. Total rows: {len(df)}")
    print(f"Constraint count distribution:\n{df['constraint_count'].value_counts().sort_index()}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Add constraint_count column to filtered tasks.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to input filtered_tasks.csv. Defaults to config path."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path to output CSV. Defaults to input path (overwrite)."
    )
    args = parser.parse_args()

    paths = get_paths()
    
    # Determine input path
    if args.input:
        input_path = Path(args.input)
    else:
        # Default to the standard filtered tasks location
        input_path = paths.DATA_PROCESSED / "filtered_tasks.csv"

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path

    try:
        add_constraint_count_column(input_path, output_path)
    except Exception as e:
        print(f"Error processing dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()