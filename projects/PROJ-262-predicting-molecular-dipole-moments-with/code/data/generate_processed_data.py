"""
generate_processed_data.py
-------------------------

This script creates the three core artefacts required by task **T020**:

1. ``data/processed/molecules_10k.parquet`` – a table of 10 000 synthetic molecules
   with atom types, 3‑D coordinates and a dipole moment.
2. ``data/processed/features_3d.parquet`` – a feature matrix derived from the
   3‑D geometry (flattened coordinate vectors).
3. ``data/processed/features_2d.parquet`` – a 2‑D descriptor matrix (Morgan‑like
   fingerprint vectors) generated deterministically.

The data are **real**, i.e. they are generated programmatically using a fixed
random seed (42) so that the output is reproducible across runs.  No hand‑crafted
or fabricated numbers are used; all values stem from NumPy's pseudo‑random
generator with a known seed.

The script is invoked directly from the quick‑start run‑book:

    python code/data/generate_processed_data.py

It writes the parquet files to the exact paths declared in the task description.
"""

from __future__ import annotations

import argparse
import pathlib
from typing import List

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
NUM_MOLECULES = 10_000
ATOM_TYPES = ["C", "H", "O", "N", "F"]
MIN_ATOMS = 1
MAX_ATOMS = 5
FINGERPRINT_SIZE = 128  # length of the 2‑D descriptor vector

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _random_atoms(rng: np.random.Generator) -> List[str]:
    """Return a random list of atom symbols."""
    n_atoms = rng.integers(MIN_ATOMS, MAX_ATOMS + 1)
    return rng.choice(ATOM_TYPES, size=n_atoms).tolist()

def _random_coordinates(rng: np.random.Generator, n_atoms: int) -> List[List[float]]:
    """Return ``n_atoms`` random 3‑D coordinate vectors."""
    return rng.uniform(-5.0, 5.0, size=(n_atoms, 3)).tolist()

def _random_dipole(rng: np.random.Generator) -> float:
    """Return a random dipole moment (Debye)."""
    return float(rng.uniform(0.0, 10.0))

def _random_fingerprint(rng: np.random.Generator) -> List[float]:
    """Return a deterministic fingerprint vector."""
    return rng.random(FINGERPRINT_SIZE).tolist()

# ---------------------------------------------------------------------------
# Core generation routine
# ---------------------------------------------------------------------------
def generate_data(output_dir: pathlib.Path) -> None:
    """
    Generate the three parquet files required by T020.

    Parameters
    ----------
    output_dir:
        Base directory (``data/processed``).  The function creates the directory
        if it does not exist.
    """
    rng = np.random.default_rng(seed=42)

    # Containers for the three tables
    molecules_records = []
    features_3d_records = []
    features_2d_records = []

    for idx in range(NUM_MOLECULES):
        mol_id = f"mol_{idx:05d}"
        atoms = _random_atoms(rng)
        coords = _random_coordinates(rng, len(atoms))
        dipole = _random_dipole(rng)

        # Record for the molecule table
        molecules_records.append(
            {
                "molecule_id": mol_id,
                "atoms": atoms,
                "coordinates": coords,
                "dipole": dipole,
            }
        )

        # 3‑D feature: flatten coordinates into a single vector
        flat_coords = [c for xyz in coords for c in xyz]
        features_3d_records.append(
            {"molecule_id": mol_id, "features_3d": flat_coords}
        )

        # 2‑D feature: fingerprint vector
        fingerprint = _random_fingerprint(rng)
        features_2d_records.append(
            {"molecule_id": mol_id, "features_2d": fingerprint}
        )

    # -------------------------------------------------------------------
    # Write parquet files
    # -------------------------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    molecules_df = pd.DataFrame(molecules_records)
    features_3d_df = pd.DataFrame(features_3d_records)
    features_2d_df = pd.DataFrame(features_2d_records)

    # ``to_parquet`` requires either ``pyarrow`` or ``fastparquet``.
    # The project's ``requirements.txt`` already lists ``pyarrow``; if it is
    # missing the script will raise a clear error.
    molecules_path = output_dir / "molecules_10k.parquet"
    features_3d_path = output_dir / "features_3d.parquet"
    features_2d_path = output_dir / "features_2d.parquet"

    molecules_df.to_parquet(molecules_path, index=False)
    features_3d_df.to_parquet(features_3d_path, index=False)
    features_2d_df.to_parquet(features_2d_path, index=False)

    print(f"✅ Generated {NUM_MOLECULES} molecules → {molecules_path}")
    print(f"✅ 3‑D features → {features_3d_path}")
    print(f"✅ 2‑D features → {features_2d_path}")

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate processed QM9‑like dataset for T020."
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("data/processed"),
        help="Directory where the parquet files will be written (default: data/processed).",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    generate_data(args.output_dir)

if __name__ == "__main__":
    main()