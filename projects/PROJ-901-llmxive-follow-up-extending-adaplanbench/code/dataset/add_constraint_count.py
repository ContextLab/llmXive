"""
Module to add constraint_count column to filtered tasks dataset.
Ensures the constraint_count is an integer derived from len(progressive_constraints).
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, get_paths

def compute_constraint_count(constraints_field: Any) -> int:
    """
    Compute constraint count from the progressive_constraints field.
    Handles stringified JSON and list formats.
    """
    if constraints_field is None:
        return 0
    
    if isinstance(constraints_field, list):
        return len(constraints_field)
    
    if isinstance(constraints_field, str):
        try:
            parsed = json.loads(constraints_field)
            if isinstance(parsed, list):
                return len(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    
    return 0

def add_constraint_count_column(input_path: Path, output_path: Path):
    """
    Read CSV, add constraint_count column, and write back.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)

    if 'progressive_constraints' not in df.columns:
        raise ValueError("Input CSV must contain 'progressive_constraints' column.")

    print("Computing constraint_count...")
    df['constraint_count'] = df['progressive_constraints'].apply(compute_constraint_count)

    # Ensure constraint_count is integer
    df['constraint_count'] = df['constraint_count'].astype(int)

    print(f"Writing to {output_path}...")
    df.to_csv(output_path, index=False)
    print(f"Added constraint_count column. Total rows: {len(df)}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Add constraint_count column to dataset")
    parser.add_argument('--input', type=str, required=True, help="Input CSV path")
    parser.add_argument('--output', type=str, required=True, help="Output CSV path")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        add_constraint_count_column(input_path, output_path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
