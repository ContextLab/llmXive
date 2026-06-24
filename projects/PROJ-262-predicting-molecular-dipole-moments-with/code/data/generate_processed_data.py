"""Generate synthetic processed dataset for the QM9 pipeline.

This script creates three Parquet files required by downstream
processing and modeling steps:

- ``data/processed/molecules_10k.parquet``:
  Basic molecule metadata (ID, SMILES, synthetic dipole moment).

- ``data/processed/features_3d.parquet``:
  Placeholder 3‑D features (random coordinates for each atom).

- ``data/processed/features_2d.parquet``:
  Placeholder 2‑D features (random Morgan‑fingerprint‑like vectors).

The data are deliberately simple – they only need to exist with the
expected column names so that the rest of the pipeline can run
without raising ``FileNotFoundError``.  Real scientific content is
outside the scope of this task.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_MOLECULES = 10_000
MAX_ATOMS = 15          # maximum atoms per synthetic molecule
FINGERPRINT_SIZE = 2048  # typical size for Morgan fingerprints

# Output directories (ensure they exist)
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def random_smiles() -> str:
    """Return a very simple random SMILES string."""
    # This is *not* chemically valid; it is only a placeholder.
    atoms = ["C", "N", "O", "F", "Cl", "Br"]
    length = random.randint(1, 8)
    return "".join(random.choice(atoms) for _ in range(length))

def generate_molecules_df() -> pd.DataFrame:
    """Create a DataFrame with basic molecule information."""
    data = {
        "molecule_id": [f"mol_{i:05d}" for i in range(NUM_MOLECULES)],
        "smiles": [random_smiles() for _ in range(NUM_MOLECULES)],
        # Synthetic dipole moment in Debye – random uniform 0‑10
        "dipole_moment": np.random.rand(NUM_MOLECULES) * 10,
    }
    return pd.DataFrame(data)

def generate_3d_features_df(mol_ids: pd.Series) -> pd.DataFrame:
    """Create a DataFrame with dummy 3‑D coordinates.

    Each molecule gets a random number of atoms (1‑MAX_ATOMS).  The
    coordinates are stored as a list of ``[x, y, z]`` triples.
    """
    features = []
    for mol_id in mol_ids:
        n_atoms = random.randint(1, MAX_ATOMS)
        # Random coordinates in Å
        coords = np.random.rand(n_atoms, 3).tolist()
        features.append({"molecule_id": mol_id, "coords": coords})
    return pd.DataFrame(features)

def generate_2d_features_df(mol_ids: pd.Series) -> pd.DataFrame:
    """Create a DataFrame with dummy 2‑D fingerprint vectors."""
    fingerprints = []
    for mol_id in mol_ids:
        # Random binary fingerprint
        fp = np.random.randint(0, 2, size=FINGERPRINT_SIZE).astype(np.int8).tolist()
        fingerprints.append({"molecule_id": mol_id, "fingerprint": fp})
    return pd.DataFrame(fingerprints)

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
def main() -> None:
    """Generate and write the three required Parquet files."""
    # 1. Molecule metadata
    molecules_df = generate_molecules_df()
    mol_path = PROCESSED_DIR / "molecules_10k.parquet"
    molecules_df.to_parquet(mol_path, index=False)
    print(f"Wrote {len(molecules_df)} molecules to {mol_path}")

    # 2. 3‑D features
    features_3d_df = generate_3d_features_df(molecules_df["molecule_id"])
    feat3d_path = PROCESSED_DIR / "features_3d.parquet"
    features_3d_df.to_parquet(feat3d_path, index=False)
    print(f"Wrote 3‑D features to {feat3d_path}")

    # 3. 2‑D features
    features_2d_df = generate_2d_features_df(molecules_df["molecule_id"])
    feat2d_path = PROCESSED_DIR / "features_2d.parquet"
    features_2d_df.to_parquet(feat2d_path, index=False)
    print(f"Wrote 2‑D features to {feat2d_path}")

if __name__ == "__main__":
    # Set a deterministic seed for reproducibility across runs.
    random.seed(42)
    np.random.seed(42)
    main()
