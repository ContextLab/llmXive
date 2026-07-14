from __future__ import annotations

import argparse
import os
import random
import string
import uuid
from pathlib import Path

import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_output_dir(output_dir: Path) -> None:
    """Create the output directory if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)

def random_smiles(length: int = 10) -> str:
    """Generate a pseudo‑random SMILES‑like string.

    This is **not** chemically valid – it is only used to populate the
    synthetic dataset required for the pipeline to run end‑to‑end.
    """
    atoms = ["C", "N", "O", "F", "Cl", "Br", "I"]
    bonds = ["", "=", "#"]
    smiles = []
    for _ in range(length):
        atom = random.choice(atoms)
        bond = random.choice(bonds)
        smiles.append(atom + bond)
    return "".join(smiles)

def generate_molecules_df(num_molecules: int = 10_000) -> pd.DataFrame:
    """Create a DataFrame with synthetic molecule identifiers and a target dipole."""
    data = {
        "molecule_id": [str(uuid.uuid4()) for _ in range(num_molecules)],
        "smiles": [random_smiles(random.randint(5, 15)) for _ in range(num_molecules)],
        # Dipole moments are drawn from a normal distribution centred around 2.0 D
        "dipole": np.random.normal(loc=2.0, scale=0.5, size=num_molecules).clip(min=0.0),
    }
    return pd.DataFrame(data)

def generate_2d_features_df(molecules_df: pd.DataFrame, n_features: int = 128) -> pd.DataFrame:
    """Generate a synthetic 2‑D feature matrix (e.g., Morgan fingerprints)."""
    num = len(molecules_df)
    features = np.random.randint(0, 2, size=(num, n_features)).astype(np.int8)
    feature_cols = [f"fp_{i}" for i in range(n_features)]
    df = pd.DataFrame(features, columns=feature_cols)
    df["dipole"] = molecules_df["dipole"].values
    return df

def generate_3d_features_df(molecules_df: pd.DataFrame, n_features: int = 64) -> pd.DataFrame:
    """Generate a synthetic 3‑D feature matrix (e.g., Coulomb matrix flattening)."""
    num = len(molecules_df)
    features = np.random.rand(num, n_features).astype(np.float32)
    feature_cols = [f"coulomb_{i}" for i in range(n_features)]
    df = pd.DataFrame(features, columns=feature_cols)
    df["dipole"] = molecules_df["dipole"].values
    return df

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic processed data for the dipole‑moment pipeline."
    )
    parser.add_argument(
        "--num-molecules",
        type=int,
        default=10_000,
        help="Number of synthetic molecules to generate (default: 10,000).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "processed",
        help="Directory where parquet files will be written.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)

    # 1. Molecules table
    molecules_df = generate_molecules_df(num_molecules=args.num_molecules)
    molecules_path = output_dir / "molecules_10k.parquet"
    molecules_df.to_parquet(molecules_path, engine="pyarrow")
    print(f"✅ Wrote {len(molecules_df)} molecules to {molecules_path}")

    # 2. 2‑D features
    features_2d_df = generate_2d_features_df(molecules_df)
    features_2d_path = output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(features_2d_path, engine="pyarrow")
    print(f"✅ Wrote 2‑D features to {features_2d_path}")

    # 3. 3‑D features
    features_3d_df = generate_3d_features_df(molecules_df)
    features_3d_path = output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(features_3d_path, engine="pyarrow")
    print(f"✅ Wrote 3‑D features to {features_3d_path}")

if __name__ == "__main__":
    main()
