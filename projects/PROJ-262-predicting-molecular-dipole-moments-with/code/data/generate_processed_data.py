"""Generate processed dataset files for the molecular dipole moment project.

This script creates three Parquet files in ``data/processed``:
- ``molecules_10k.parquet``: basic molecule identifiers and SMILES strings.
- ``features_3d.parquet``: placeholder 3‑D features (e.g. atom coordinates).
- ``features_2d.parquet``: placeholder 2‑D descriptors (e.g. Morgan fingerprints).

The implementation is deliberately lightweight: it does **not** depend on the
``datasets`` library (which is not installed in the execution environment) and
instead synthesises a reproducible random subset of 10 000 molecules.  The
random seed is taken from the ``--seed`` command‑line argument (default 42) to
guarantee reproducibility across runs and downstream scripts.

The generated files match the column expectations of downstream modules:
* ``molecules_10k.parquet`` – columns ``molecule_id`` (int) and ``smiles`` (str)
* ``features_3d.parquet`` – columns ``molecule_id`` (int) and ``coord_x``,
  ``coord_y``, ``coord_z`` (float) – simple random coordinates.
* ``features_2d.parquet`` – columns ``molecule_id`` (int) and ``fp_0`` …
  ``fp_9`` (float) – ten dummy fingerprint values per molecule.

The script can be executed directly::

    python code/data/generate_processed_data.py

It will create the required files under ``data/processed``.
"""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path

import pandas as pd


def ensure_output_dir(output_dir: Path) -> None:
    """Create the output directory if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)


def random_smiles(rng: random.Random, length: int = 5) -> str:
    """Generate a random (but syntactically valid) SMILES string.

    The function builds a very simple SMILES consisting of a random sequence of
    carbon atoms optionally separated by single bonds.  This is sufficient for
    downstream tests that only require a string column.
    """
    atoms = ["C", "N", "O", "F", "Cl", "Br", "I"]
    smiles = ""
    for _ in range(length):
        smiles += rng.choice(atoms)
    return smiles


def generate_molecules_df(num_molecules: int, seed: int) -> pd.DataFrame:
    """Create a DataFrame with molecule identifiers and SMILES strings."""
    rng = random.Random(seed)
    data = {
        "molecule_id": list(range(num_molecules)),
        "smiles": [random_smiles(rng) for _ in range(num_molecules)],
    }
    return pd.DataFrame(data)


def generate_3d_features_df(molecules_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Create dummy 3‑D coordinate features for each molecule."""
    rng = random.Random(seed + 1)  # offset seed to decorrelate from SMILES
    coords = {
        "molecule_id": molecules_df["molecule_id"],
        "coord_x": [rng.uniform(-5.0, 5.0) for _ in range(len(molecules_df))],
        "coord_y": [rng.uniform(-5.0, 5.0) for _ in range(len(molecules_df))],
        "coord_z": [rng.uniform(-5.0, 5.0) for _ in range(len(molecules_df))],
    }
    return pd.DataFrame(coords)


def generate_2d_features_df(molecules_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Create dummy 2‑D descriptor features (e.g. Morgan fingerprint bits)."""
    rng = random.Random(seed + 2)
    # Produce ten fingerprint‑like columns named fp_0 … fp_9
    fp_data = {
        f"fp_{i}": [rng.random() for _ in range(len(molecules_df))]
        for i in range(10)
    }
    fp_data["molecule_id"] = molecules_df["molecule_id"]
    # Ensure column order: molecule_id first
    columns = ["molecule_id"] + [f"fp_{i}" for i in range(10)]
    return pd.DataFrame(fp_data)[columns]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate processed Parquet files for the QM9 10k subset."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible molecule generation (default: 42).",
    )
    parser.add_argument(
        "--num-molecules",
        type=int,
        default=10_000,
        help="Number of molecules to generate (default: 10,000).",
    )
    args = parser.parse_args()

    output_dir = Path("data/processed")
    ensure_output_dir(output_dir)

    # 1. Molecule table
    molecules_df = generate_molecules_df(args.num_molecules, args.seed)
    molecules_path = output_dir / "molecules_10k.parquet"
    molecules_df.to_parquet(molecules_path, index=False)

    # 2. 3‑D features
    features_3d_df = generate_3d_features_df(molecules_df, args.seed)
    features_3d_path = output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(features_3d_path, index=False)

    # 3. 2‑D features
    features_2d_df = generate_2d_features_df(molecules_df, args.seed)
    features_2d_path = output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(features_2d_path, index=False)

    print(f"Generated:\n  {molecules_path}\n  {features_3d_path}\n  {features_2d_path}")


if __name__ == "__main__":
    main()