from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# Import the real dataset loader used by the project
# The project uses the QM9 dataset via the datasets library (T021 dependency)
from datasets import load_dataset

def parse_xyz_file(file_path: Path) -> Tuple[List[str], List[List[float]]]:
    """
    Parse a XYZ file to extract atom types and coordinates.
    Returns (atom_types, coordinates).
    Raises ValueError if the file is malformed or contains NaN/Inf.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"XYZ file not found: {file_path}")

    atoms = []
    coords = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                raise ValueError("XYZ file too short")
            
            num_atoms = int(lines[0].strip())
            # Skip comment line
            
            for i, line in enumerate(lines[2:2+num_atoms]):
                parts = line.strip().split()
                if len(parts) < 4:
                    raise ValueError(f"Invalid atom line {i}: {line}")
                
                atom_type = parts[0]
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                except ValueError:
                    raise ValueError(f"Non-numeric coordinate in line {i}")
                
                if np.isnan(x) or np.isnan(y) or np.isnan(z):
                    raise ValueError(f"NaN coordinate found in line {i}")
                if np.isinf(x) or np.isinf(y) or np.isinf(z):
                    raise ValueError(f"Inf coordinate found in line {i}")
                
                atoms.append(atom_type)
                coords.append([x, y, z])
                
        if len(atoms) != num_atoms:
            raise ValueError(f"Atom count mismatch: expected {num_atoms}, got {len(atoms)}")
            
    except Exception as e:
        raise ValueError(f"Failed to parse XYZ file {file_path}: {e}")
        
    return atoms, coords


def handle_missing_coordinates(
    dataset_name: str = "qm9",
    output_path: Optional[Path] = None,
    subset_size: int = 5000
) -> pd.DataFrame:
    """
    Load the QM9 dataset, filter out molecules with missing 3D coordinates
    or invalid structures, and generate an exclusion report.
    
    Args:
        dataset_name: Name of the HuggingFace dataset (default: "qm9")
        output_path: Path to write the exclusion CSV. Defaults to data/reports/excluded_molecules.csv
        subset_size: Number of molecules to process from the dataset.
    
    Returns:
        DataFrame with columns: molecule_id, exclusion_reason, exclusion_timestamp
    """
    if output_path is None:
        output_path = Path("data/reports/excluded_molecules.csv")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading dataset: {dataset_name}...")
    try:
        # Load QM9 dataset. QM9 is small enough to load fully, but we stream to be safe.
        # The dataset contains 'atom_positions' (3D coords) and 'atom_symbols'
        ds = load_dataset(dataset_name, split="train", streaming=True)
    except Exception as e:
        print(f"CRITICAL: Failed to load dataset {dataset_name}: {e}")
        # Fail loudly as per constraints - no synthetic fallback
        raise RuntimeError(f"Real data source {dataset_name} is inaccessible. Cannot proceed.")

    excluded_rows = []
    processed_count = 0
    timestamp = datetime.now().isoformat()

    print(f"Processing molecules (limit: {subset_size})...")
    
    for idx, item in enumerate(ds):
        if processed_count >= subset_size:
            break
        
        processed_count += 1
        molecule_id = item.get('molecule_id') or item.get('mol_id') or f"mol_{idx}"
        
        # Check for missing 3D coordinates
        # In QM9, atom_positions is a list of [x,y,z] for each atom
        atom_positions = item.get('atom_positions')
        atom_symbols = item.get('atom_symbols')
        
        exclusion_reason = None
        
        # Condition 1: Missing 3D coordinates
        if atom_positions is None or len(atom_positions) == 0:
            exclusion_reason = "missing_3d"
        # Condition 2: Invalid structure (NaN/Inf in coordinates)
        elif atom_positions:
            try:
                coords = np.array(atom_positions)
                if np.isnan(coords).any() or np.isinf(coords).any():
                    exclusion_reason = "invalid_structure"
                # Check for empty coordinates list or mismatched atom count
                elif atom_symbols and len(atom_positions) != len(atom_symbols):
                    exclusion_reason = "invalid_structure"
                # Check for degenerate structures (all atoms at same point)
                elif len(coords) > 1:
                    # Calculate distances between all pairs
                    dists = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
                    # If all distances are 0 (or very close), it's invalid
                    if np.all(dists < 1e-6):
                        exclusion_reason = "invalid_structure"
            except Exception:
                exclusion_reason = "invalid_structure"
        
        if exclusion_reason:
            excluded_rows.append({
                "molecule_id": str(molecule_id),
                "exclusion_reason": exclusion_reason,
                "exclusion_timestamp": timestamp
            })
            
        if idx % 1000 == 0:
            print(f"  Processed {idx} molecules, excluded {len(excluded_rows)} so far...")

    print(f"Finished processing. Total excluded: {len(excluded_rows)}")
    
    df = pd.DataFrame(excluded_rows)
    if not df.empty:
        df.to_csv(output_path, index=False)
        print(f"Exclusion report written to: {output_path}")
    else:
        # Write empty file with headers if no exclusions
        df.to_csv(output_path, index=False)
        print(f"No exclusions found. Empty report written to: {output_path}")
        
    return df


def update_state_with_hash(state_path: Path, output_path: Path) -> None:
    """
    Compute SHA-256 hash of the exclusion report and update state file.
    """
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found: {output_path}")
        
    with open(output_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
        
    # Simple append to state file for now (T019a specific)
    # In a full pipeline, this would update the YAML structure properly
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'a') as f:
        f.write(f"T019a_exclusion_report_hash: {file_hash}\n")
        f.write(f"T019a_exclusion_report_path: {output_path}\n")
        f.write(f"T019a_timestamp: {datetime.now().isoformat()}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter molecules with missing 3D coordinates from QM9 dataset."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="qm9",
        help="HuggingFace dataset name (default: qm9)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/reports/excluded_molecules.csv",
        help="Output path for exclusion CSV"
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=5000,
        help="Number of molecules to process (default: 5000)"
    )
    parser.add_argument(
        "--update-state",
        type=str,
        default="state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml",
        help="Path to state YAML file to update with hash"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    
    try:
        df = handle_missing_coordinates(
            dataset_name=args.dataset,
            output_path=output_path,
            subset_size=args.subset_size
        )
        
        # Update state with hash
        state_path = Path(args.update_state)
        update_state_with_hash(state_path, output_path)
        
        print("T019a completed successfully.")
        
    except Exception as e:
        print(f"T019a FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()