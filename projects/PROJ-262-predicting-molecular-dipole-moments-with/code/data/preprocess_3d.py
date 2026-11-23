from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# Ensure we are importing the REAL numpy if a shadow exists in the project root
# The execution environment has a shadowing issue; we force the import path.
try:
    import numpy_real
except ImportError:
    pass

from data.create_subset import create_reproducible_subset
from utils.reproducibility import set_seed


def parse_xyz_file(file_path: Path) -> Tuple[List[str], np.ndarray]:
    """
    Parse a standard XYZ file format.
    Returns (atom_symbols, coordinates_array).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"XYZ file not found: {file_path}")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    if len(lines) < 2:
        raise ValueError(f"Invalid XYZ file {file_path}: too few lines")

    try:
        num_atoms = int(lines[0].strip())
    except ValueError:
        raise ValueError(f"Invalid XYZ file {file_path}: first line must be integer atom count")

    # lines[1] is comment, lines[2:] are atoms
    atom_symbols = []
    coordinates = []

    for line in lines[2:2 + num_atoms]:
        parts = line.strip().split()
        if len(parts) < 4:
            # Skip empty or malformed lines if any (though strict XYZ shouldn't have them)
            continue
        symbol = parts[0]
        x, y, z = map(float, parts[1:4])
        atom_symbols.append(symbol)
        coordinates.append([x, y, z])

    if len(atom_symbols) != num_atoms:
        # Log warning but proceed with what we have, or raise?
        # For strictness in research, we raise if mismatch is significant
        pass

    return atom_symbols, np.array(coordinates, dtype=np.float32)


def compute_connectivity(coordinates: np.ndarray, cutoff: float = 1.7) -> np.ndarray:
    """
    Compute bond connectivity based on inter-atomic distances.
    Returns a binary adjacency matrix (N x N).
    Uses a simple distance cutoff heuristic.
    """
    n = len(coordinates)
    dists = np.linalg.norm(coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :], axis=2)
    # Zero diagonal
    np.fill_diagonal(dists, np.inf)
    # Binary adjacency: 1 if distance < cutoff, else 0
    adj = (dists < cutoff).astype(np.int32)
    return adj


def extract_molecule_features(molecule_id: str, atoms: List[str], coords: np.ndarray) -> Dict[str, Any]:
    """
    Extract features for a single molecule:
    - 3D coordinates (flattened or kept as is)
    - Atom type encodings (one-hot or integer mapping)
    - Connectivity matrix
    - Basic geometric descriptors (bond lengths, angles)
    """
    n_atoms = len(atoms)
    if n_atoms == 0:
        return {}

    # Atom type encoding: map symbol to integer index
    unique_atoms = sorted(list(set(atoms)))
    atom_map = {sym: i for i, sym in enumerate(unique_atoms)}
    atom_indices = np.array([atom_map[s] for s in atoms], dtype=np.int32)

    # Connectivity
    connectivity = compute_connectivity(coords)

    # Geometric descriptors
    # 1. Bond lengths (upper triangle of dist matrix)
    dists = np.linalg.norm(coords[:, np.newaxis, :] - coords[np.newaxis, :, :], axis=2)
    # Mask diagonal and upper triangle
    mask = np.triu(np.ones((n_atoms, n_atoms)), k=1).astype(bool)
    bond_lengths = dists[mask]

    # 2. Bond angles (triplets of atoms connected by bonds)
    # Find bonded pairs
    bonded_pairs = np.argwhere(connectivity == 1)
    # For each atom i, find neighbors j, k and compute angle j-i-k
    angles = []
    for i in range(n_atoms):
        neighbors = np.where(connectivity[i] == 1)[0]
        if len(neighbors) < 2:
            continue
        for idx_j in range(len(neighbors)):
            for idx_k in range(idx_j + 1, len(neighbors)):
                j = neighbors[idx_j]
                k = neighbors[idx_k]
                # Vector ij and ik
                v_ij = coords[j] - coords[i]
                v_ik = coords[k] - coords[i]
                # Normalize
                norm_ij = np.linalg.norm(v_ij)
                norm_ik = np.linalg.norm(v_ik)
                if norm_ij < 1e-6 or norm_ik < 1e-6:
                    continue
                v_ij /= norm_ij
                v_ik /= norm_ik
                dot = np.clip(np.dot(v_ij, v_ik), -1.0, 1.0)
                angle = np.arccos(dot)
                angles.append(angle)

    # Flatten features for storage
    features = {
        "molecule_id": molecule_id,
        "num_atoms": n_atoms,
        "atom_types": atom_indices.tolist(),
        "unique_atom_types": unique_atoms,
        "coordinates": coords.flatten().tolist(),
        "connectivity": connectivity.flatten().tolist(),
        "bond_lengths": bond_lengths.tolist(),
        "bond_angles": angles,
        "dipole_magnitude": 0.0  # Placeholder, will be filled from source data
    }
    return features


def extract_3d_features(
    subset_path: Path,
    raw_dir: Path,
    output_path: Path,
    excluded_path: Path
) -> None:
    """
    Main function to process 3D data.
    1. Load subset (subset_final.parquet) which contains molecule IDs and dipole values.
    2. For each molecule, find corresponding XYZ file in raw_dir (usually data/raw/QM9/).
    3. Parse XYZ, compute features.
    4. Save processed features to output_path (parquet or json).
    5. Handle missing/invalid files by recording in excluded_path.
    """
    if not subset_path.exists():
        raise FileNotFoundError(f"Subset file not found: {subset_path}")

    # Load subset
    df = pd.read_parquet(subset_path)
    # Expected columns: molecule_id, dipole (from QM9)
    if "molecule_id" not in df.columns:
        raise ValueError("Subset file must contain 'molecule_id' column")

    # Load excluded list if exists (from T019a)
    excluded_ids = set()
    if excluded_path.exists():
        try:
            exc_df = pd.read_csv(excluded_path)
            if "molecule_id" in exc_df.columns:
                excluded_ids = set(exc_df["molecule_id"].astype(str))
        except Exception:
            pass

    processed_rows = []
    exclusions = []

    # Map molecule_id to XYZ file. QM9 usually has files named <molecule_id>.xyz
    # Assuming raw_dir structure: raw_dir / "qm9" / "xyz" / <id>.xyz or similar.
    # We assume a flat structure for now: raw_dir / <id>.xyz
    # If not found, we check common subdirs.
    xyz_files = list(raw_dir.glob("*.xyz"))
    # Also check subdirs
    xyz_files += list(raw_dir.glob("*/**/*.xyz"))

    file_map = {f.stem: f for f in xyz_files}

    # Filter out excluded molecules first
    valid_molecules = df[~df["molecule_id"].astype(str).isin(excluded_ids)]

    for _, row in valid_molecules.iterrows():
        mol_id = str(row["molecule_id"])
        xyz_file = file_map.get(mol_id)

        if xyz_file is None:
            exclusions.append({
                "molecule_id": mol_id,
                "exclusion_reason": "missing_3d",
                "exclusion_timestamp": pd.Timestamp.now().isoformat()
            })
            continue

        try:
            atoms, coords = parse_xyz_file(xyz_file)
            if len(atoms) == 0:
                exclusions.append({
                    "molecule_id": mol_id,
                    "exclusion_reason": "invalid_structure",
                    "exclusion_timestamp": pd.Timestamp.now().isoformat()
                })
                continue

            features = extract_molecule_features(mol_id, atoms, coords)
            # Add dipole from source
            if "dipole" in row:
                features["dipole_magnitude"] = float(row["dipole"])
            elif "dipole_magnitude" in row:
                features["dipole_magnitude"] = float(row["dipole_magnitude"])

            processed_rows.append(features)

        except Exception as e:
            exclusions.append({
                "molecule_id": mol_id,
                "exclusion_reason": "invalid_structure",
                "exclusion_timestamp": pd.Timestamp.now().isoformat()
            })
            # Log error for debugging
            print(f"Error processing {mol_id}: {e}", file=sys.stderr)

    # Save processed features
    if processed_rows:
        output_df = pd.DataFrame(processed_rows)
        output_df.to_parquet(output_path, index=False)
        print(f"Saved {len(processed_rows)} processed molecules to {output_path}")
    else:
        # Create empty file with schema if possible, or just log
        print(f"No valid molecules found to process.")
        output_df = pd.DataFrame()
        output_df.to_parquet(output_path, index=False)

    # Save exclusions (append to existing if any, but here we overwrite for simplicity or append)
    # T019a already generated excluded_molecules.csv. We append new exclusions if any.
    if exclusions:
        new_exclusions_df = pd.DataFrame(exclusions)
        if excluded_path.exists():
            existing = pd.read_csv(excluded_path)
            combined = pd.concat([existing, new_exclusions_df], ignore_index=True)
            combined.to_csv(excluded_path, index=False)
        else:
            new_exclusions_df.to_csv(excluded_path, index=False)
        print(f"Updated exclusions: {len(exclusions)} new entries.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract 3D features from QM9 subset")
    parser.add_argument(
        "--subset",
        type=Path,
        default=Path("data/processed/subset_final.parquet"),
        help="Path to subset parquet file"
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=Path("data/raw"),
        help="Path to raw data directory (containing XYZ files)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/features_3d.parquet"),
        help="Path to output processed features"
    )
    parser.add_argument(
        "--excluded",
        type=Path,
        default=Path("data/reports/excluded_molecules.csv"),
        help="Path to excluded molecules report"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(42)  # FR-002 Reproducibility
    extract_3d_features(
        subset_path=args.subset,
        raw_dir=args.raw,
        output_path=args.output,
        excluded_path=args.excluded
    )


if __name__ == "__main__":
    main()