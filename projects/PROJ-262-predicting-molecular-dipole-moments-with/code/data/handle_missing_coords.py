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
import hashlib
import yaml

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_yaml(artifact_path: Path, state_path: Path):
    """Update the project state YAML with the artifact hash."""
    if not state_path.exists():
        # Create basic state structure if missing
        state_data = {
            "project": "PROJ-262-predicting-molecular-dipole-moments-with",
            "artifacts": {}
        }
    else:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {"project": "PROJ-262-predicting-molecular-dipole-moments-with", "artifacts": {}}

    if "artifacts" not in state_data:
        state_data["artifacts"] = {}

    # Record the hash for the exclusion report
    file_hash = calculate_sha256(artifact_path)
    state_data["artifacts"]["excluded_molecules.csv"] = {
        "hash": file_hash,
        "path": str(artifact_path),
        "updated_at": datetime.now().isoformat()
    }

    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def handle_missing_coordinates(
    input_path: str | Path,
    output_path: str | Path,
    schema_path: str | Path | None = None
) -> pd.DataFrame:
    """
    Validates molecule data for missing 3D coordinates or invalid structures.

    Args:
        input_path: Path to the input molecule data (JSON, CSV, or Parquet).
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

    # Try to load based on extension
    df = None
    suffix = input_path.suffix.lower()

    if suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif suffix == '.csv':
        df = pd.read_csv(input_path)
    elif suffix == '.json':
        with open(input_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'molecules' in data:
            df = pd.DataFrame(data['molecules'])
        else:
            df = pd.DataFrame([data])
    else:
        # Fallback to CSV if extension is unknown
        try:
            df = pd.read_csv(input_path)
        except Exception:
            raise ValueError(f"Unsupported file format: {suffix}")

    excluded_rows = []
    timestamp = datetime.now().isoformat()

    # Normalize column names for safety
    df.columns = df.columns.str.strip()

    for idx, row in df.iterrows():
        molecule_id = row.get('molecule_id', row.get('id', f"unknown_{idx}"))
        exclusion_reason = None

        # Check for missing 3D coordinates
        coordinates = row.get('coordinates')
        if coordinates is None:
            exclusion_reason = 'missing_3d'
        elif isinstance(coordinates, list):
            # Check if coordinates contain NaN or are empty
            try:
                # Handle list of lists or flat list depending on format
                if len(coordinates) == 0:
                    exclusion_reason = 'missing_3d'
                else:
                    # Attempt to convert to numpy array to check for NaN
                    # Coordinates might be [[x,y,z], [x,y,z], ...] or a flat list
                    flat_coords = []
                    for item in coordinates:
                        if isinstance(item, list):
                            flat_coords.extend(item)
                        else:
                            flat_coords.append(item)
                    
                    if len(flat_coords) == 0:
                        exclusion_reason = 'missing_3d'
                    else:
                        coords_array = np.array(flat_coords, dtype=float)
                        if np.isnan(coords_array).any():
                            exclusion_reason = 'missing_3d'
            except (ValueError, TypeError):
                exclusion_reason = 'missing_3d'
        elif isinstance(coordinates, str) and (coordinates == '' or coordinates.lower() == 'nan'):
            exclusion_reason = 'missing_3d'
        else:
            exclusion_reason = 'missing_3d'

        # Check for invalid structure (e.g., missing atoms) only if coordinates are valid
        if exclusion_reason is None:
            atoms = row.get('atoms')
            if atoms is None:
                exclusion_reason = 'invalid_structure'
            elif isinstance(atoms, list) and len(atoms) == 0:
                exclusion_reason = 'invalid_structure'
            elif isinstance(atoms, str) and atoms.strip() == '':
                exclusion_reason = 'invalid_structure'

        if exclusion_reason:
            excluded_rows.append({
                'molecule_id': str(molecule_id),
                'exclusion_reason': exclusion_reason,
                'exclusion_timestamp': timestamp
            })

    # Create DataFrame of excluded molecules
    excluded_df = pd.DataFrame(excluded_rows)

    # Write to CSV (always write, even if empty, to satisfy contract)
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
    parser.add_argument(
        "--state",
        type=str,
        default="state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml",
        help="Path to state YAML file to update."
    )

    args = parser.parse_args()

    try:
        excluded_df = handle_missing_coordinates(args.input, args.output, args.schema)
        
        # Update state file with artifact hash
        state_path = Path(args.state)
        if state_path.parent.exists():
            update_state_yaml(Path(args.output), state_path)
        
        print(f"Exclusion report written to: {args.output}")
        print(f"Total molecules excluded: {len(excluded_df)}")
        if not excluded_df.empty:
            print("Exclusion breakdown:")
            print(excluded_df['exclusion_reason'].value_counts())
        else:
            print("No molecules excluded.")
    except FileNotFoundError as e:
        print(f"File error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing molecule data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()