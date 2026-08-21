"""
Task T019: Validation for missing 3D coordinates.

This script validates molecule data for missing 3D coordinates or invalid structures.
It generates a report of excluded molecules with specific exclusion reasons.

Output: data/reports/excluded_molecules.csv
Columns: molecule_id, exclusion_reason, exclusion_timestamp
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import numpy as np
import argparse
import json

def handle_missing_coordinates(
    input_path: str | Path,
    output_path: str | Path,
    schema_path: str | Path | None = None
) -> pd.DataFrame:
    """
    Validates molecule data for missing 3D coordinates or invalid structures.

    Args:
        input_path: Path to the input molecule data (JSON or CSV).
        output_path: Path where the exclusion report will be written.
        schema_path: Optional path to a schema file for validation (not strictly used here).

    Returns:
        DataFrame of excluded molecules.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Try to load as JSON first, then CSV
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'molecules' in data:
            df = pd.DataFrame(data['molecules'])
        else:
            # Try to infer structure
            df = pd.DataFrame([data])
    except json.JSONDecodeError:
        df = pd.read_csv(input_path)

    excluded_rows = []
    timestamp = datetime.now().isoformat()

    for idx, row in df.iterrows():
        molecule_id = row.get('molecule_id', f"unknown_{idx}")
        exclusion_reason = None

        # Check for missing 3D coordinates
        coordinates = row.get('coordinates')
        if coordinates is None:
            exclusion_reason = 'missing_3d'
        elif isinstance(coordinates, list):
            # Check if coordinates contain NaN or are empty
            try:
                coords_array = np.array(coordinates)
                if coords_array.size == 0 or np.isnan(coords_array).any():
                    exclusion_reason = 'missing_3d'
            except (ValueError, TypeError):
                exclusion_reason = 'missing_3d'
        else:
            exclusion_reason = 'missing_3d'

        # Check for invalid structure (e.g., missing atoms)
        if exclusion_reason is None:
            atoms = row.get('atoms')
            if atoms is None or (isinstance(atoms, list) and len(atoms) == 0):
                exclusion_reason = 'invalid_structure'

        if exclusion_reason:
            excluded_rows.append({
                'molecule_id': molecule_id,
                'exclusion_reason': exclusion_reason,
                'exclusion_timestamp': timestamp
            })

    # Create DataFrame of excluded molecules
    excluded_df = pd.DataFrame(excluded_rows)

    # Write to CSV
    if not excluded_df.empty:
        excluded_df.to_csv(output_path, index=False)
    else:
        # Write empty file with headers if no exclusions
        excluded_df.to_csv(output_path, index=False)

    return excluded_df


def main():
    parser = argparse.ArgumentParser(description="Handle missing coordinates in molecule data.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/subset_final.parquet",
        help="Path to input molecule data file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/reports/excluded_molecules.csv",
        help="Path to output exclusion report."
    )
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="Optional path to schema file for validation."
    )

    args = parser.parse_args()

    try:
        excluded_df = handle_missing_coordinates(args.input, args.output, args.schema)
        print(f"Exclusion report written to: {args.output}")
        print(f"Total molecules excluded: {len(excluded_df)}")
        if not excluded_df.empty:
            print("Exclusion breakdown:")
            print(excluded_df['exclusion_reason'].value_counts())
    except Exception as e:
        print(f"Error processing molecule data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
