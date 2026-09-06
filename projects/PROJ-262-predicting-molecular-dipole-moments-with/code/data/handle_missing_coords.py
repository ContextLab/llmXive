"""
handle_missing_coords.py

Implements filtering and exclusion logic for the QM9 dataset.
Identifies molecules with missing 3D coordinates or invalid structures.
Generates a report of excluded molecules and updates the project state.

Output:
    data/reports/excluded_molecules.csv
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

# Ensure we can import sibling modules if needed, though this script is mostly self-contained
# The project structure assumes this runs from the project root or code/ directory
# We use absolute paths relative to the project root for robustness.

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-262-predicting-molecular-dipole-moments-with.yaml"

# QM9 specific paths (assuming standard download location from T021)
# The QM9 dataset is typically stored as .xyz files or a single large .xyz file
# We assume the raw data is in data/raw/qm9/ or similar.
# Based on T021, we expect the data to be downloaded.
QM9_XYZ_PATH = DATA_RAW_DIR / "qm9" / "uncharacterized"
# If uncharacterized doesn't exist, check for the main file
# Standard QM9 download structure: data/raw/qm9/target_uncharacterized.xyz (excluded) and target.xyz (included)
# We are looking for molecules that *should* be in the included set but have issues.
# However, the task implies filtering the *source* data before subset creation.
# Let's assume the raw data is in a format we can iterate over.
# Common QM9 raw file: data/raw/qm9/xyz_target.xyz (or similar)
# We will look for .xyz files in data/raw/qm9/ recursively.
RAW_XYZ_GLOB = DATA_RAW_DIR / "qm9" / "*.xyz"


def parse_xyz_file(file_path: Path) -> list[dict]:
    """
    Parses a single .xyz file into a list of molecule dictionaries.
    Each molecule dict contains:
      - molecule_id (str)
      - atoms (list of str)
      - coordinates (list of [float, float, float])
      - has_missing_coords (bool)
      - is_invalid_structure (bool)
    """
    molecules = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return molecules

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        try:
            num_atoms = int(line)
        except ValueError:
            # Skip malformed header lines
            i += 1
            continue

        if i + 1 + num_atoms > len(lines):
            # File ends prematurely
            break

        # Comment line (usually contains molecule ID or formula)
        comment_line = lines[i + 1].strip()
        # Extract molecule ID if possible, otherwise generate one
        # QM9 files often have the ID in the comment or filename
        # We'll use a hash of the file name and index for uniqueness if not found
        molecule_id = comment_line.split()[0] if comment_line else f"mol_{file_path.stem}_{i}"

        atoms = []
        coordinates = []
        has_missing = False
        is_invalid = False

        for j in range(num_atoms):
            atom_line = lines[i + 2 + j].strip()
            parts = atom_line.split()
            if len(parts) < 4:
                # Missing coordinates or malformed line
                has_missing = True
                is_invalid = True
                continue

            try:
                symbol = parts[0]
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                if any(pd.isna(coord) for coord in [x, y, z]):
                    has_missing = True
                coordinates.append([x, y, z])
                atoms.append(symbol)
            except ValueError:
                has_missing = True
                is_invalid = True

        # Basic validity check: must have atoms and coordinates
        if not atoms or not coordinates:
            is_invalid = True

        molecules.append({
            "molecule_id": molecule_id,
            "atoms": atoms,
            "coordinates": coordinates,
            "has_missing_coords": has_missing,
            "is_invalid_structure": is_invalid
        })

        i += 1 + num_atoms + 1  # Skip header, comment, and atom lines

    return molecules


def handle_missing_coordinates(
    input_glob: str | None = None,
    output_path: str | None = None
) -> pd.DataFrame:
    """
    Scans raw data files, identifies molecules with missing 3D coordinates
    or invalid structures, and generates an exclusion report.

    Args:
        input_glob: Glob pattern for input XYZ files (default: RAW_XYZ_GLOB)
        output_path: Path for the output CSV (default: DATA_REPORTS_DIR/excluded_molecules.csv)

    Returns:
        DataFrame of excluded molecules.
    """
    if input_glob is None:
        input_glob = str(RAW_XYZ_GLOB)
    if output_path is None:
        output_path = str(DATA_REPORTS_DIR / "excluded_molecules.csv")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_molecules = []
    glob_pattern = Path(input_glob)
    xyz_files = list(glob_pattern.parent.glob(glob_pattern.name)) if glob_pattern.is_absolute() else list(glob_pattern.parent.glob(glob_pattern.name))

    if not xyz_files:
        # Fallback: try to find any xyz file in the raw directory
        xyz_files = list(DATA_RAW_DIR.rglob("*.xyz"))

    if not xyz_files:
        print(f"Warning: No XYZ files found matching {input_glob} or in {DATA_RAW_DIR}.", file=sys.stderr)
        # Create an empty report
        df = pd.DataFrame(columns=["molecule_id", "exclusion_reason", "exclusion_timestamp"])
        df.to_csv(output_file, index=False)
        return df

    for xyz_file in xyz_files:
        print(f"Processing {xyz_file}...")
        molecules = parse_xyz_file(xyz_file)
        all_molecules.extend(molecules)

    excluded_rows = []
    timestamp = datetime.now().isoformat()

    for mol in all_molecules:
        reason = None
        if mol["has_missing_coords"]:
            reason = "missing_3d"
        elif mol["is_invalid_structure"]:
            reason = "invalid_structure"

        if reason:
            excluded_rows.append({
                "molecule_id": mol["molecule_id"],
                "exclusion_reason": reason,
                "exclusion_timestamp": timestamp
            })

    df = pd.DataFrame(excluded_rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["molecule_id"])
        df.to_csv(output_file, index=False)
        print(f"Exclusion report written to {output_file} ({len(df)} molecules excluded).")
    else:
        df.to_csv(output_file, index=False)
        print(f"No molecules excluded. Report written to {output_file}.")

    return df


def update_state_with_hash(excluded_csv_path: str) -> None:
    """
    Computes the SHA-256 hash of the exclusion report and updates the state YAML.
    """
    csv_path = Path(excluded_csv_path)
    if not csv_path.exists():
        print(f"Error: {csv_path} does not exist.", file=sys.stderr)
        return

    sha256_hash = hashlib.sha256()
    with open(csv_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    file_hash = sha256_hash.hexdigest()

    state_path = STATE_FILE
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Ensure structure
    if "artifacts" not in state:
        state["artifacts"] = {}
    if "excluded_molecules" not in state["artifacts"]:
        state["artifacts"]["excluded_molecules"] = {}

    state["artifacts"]["excluded_molecules"]["path"] = str(csv_path.relative_to(PROJECT_ROOT))
    state["artifacts"]["excluded_molecules"]["sha256"] = file_hash
    state["artifacts"]["excluded_molecules"]["updated_at"] = datetime.now().isoformat()

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    print(f"State updated with hash for {csv_path.name}: {file_hash}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Handle missing coordinates in QM9 dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(RAW_XYZ_GLOB),
        help="Glob pattern for input XYZ files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_REPORTS_DIR / "excluded_molecules.csv"),
        help="Path for the output CSV report."
    )
    parser.add_argument(
        "--update-state",
        action="store_true",
        help="Update the project state file with the hash of the output."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = handle_missing_coordinates(input_glob=args.input, output_path=args.output)
    if args.update_state:
        update_state_with_hash(args.output)


if __name__ == "__main__":
    main()