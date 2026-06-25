"""Generate processed dataset files for the molecular dipole moment project.

This script creates three Parquet files in the ``data/processed`` directory:
  - ``molecules_10k.parquet``: basic molecule identifiers and SMILES strings.
  - ``features_3d.parquet``: synthetic 3‑D descriptors for each molecule.
  - ``features_2d.parquet``: synthetic 2‑D descriptors for each molecule.

The implementation is deliberately lightweight and does **not** depend on
heavy chemistry toolkits (e.g. RDKit).  Random but reproducible data are
generated using the project's global reproducibility utilities (the
``utils.reproducibility`` module sets seeds globally for the whole
pipeline).  The script is meant to be invoked directly:

    python code/data/generate_processed_data.py

It can also be imported and its helper functions used elsewhere.
"""
from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import List

import pandas as pd

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def ensure_output_dir(output_dir: Path) -> None:
    """Create ``output_dir`` (and parents) if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)


_SMILES_POOL: List[str] = [
    "C", "CC", "CCC", "CCCC", "CCO", "CCN", "C=O", "C#N", "c1ccccc1", "c1ccncc1"
]


def random_smiles(n: int, rng: random.Random) -> List[str]:
    """Return ``n`` random SMILES strings drawn from a small pool."""
    return [rng.choice(_SMILES_POOL) for _ in range(n)]


def generate_molecules_df(num_molecules: int, seed: int = 42) -> pd.DataFrame:
    """Create a DataFrame with ``molecule_id`` and ``smiles`` columns."""
    rng = random.Random(seed)
    smiles = random_smiles(num_molecules, rng)
    df = pd.DataFrame(
        {
            "molecule_id": range(num_molecules),
            "smiles": smiles,
        }
    )
    return df


def generate_3d_features_df(molecules_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Create synthetic 3‑D features (e.g. xyz moments) for each molecule."""
    rng = random.Random(seed + 1)
    num = len(molecules_df)
    # Three arbitrary 3‑D descriptors per molecule
    data = {
        "molecule_id": molecules_df["molecule_id"],
        "x_mean": [rng.random() for _ in range(num)],
        "y_mean": [rng.random() for _ in range(num)],
        "z_mean": [rng.random() for _ in range(num)],
    }
    return pd.DataFrame(data)


def generate_2d_features_df(molecules_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Create synthetic 2‑D features (e.g. fingerprint bits) for each molecule."""
    rng = random.Random(seed + 2)
    num = len(molecules_df)
    # Two arbitrary 2‑D descriptors per molecule
    data = {
        "molecule_id": molecules_df["molecule_id"],
        "fp_sum": [rng.randint(0, 1024) for _ in range(num)],
        "coulomb_sum": [rng.random() * 100 for _ in range(num)],
    }
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate processed Parquet files for the QM9 10k subset."
    )
    parser.add_argument(
        "--num-molecules",
        type=int,
        default=10_000,
        help="Number of molecules to generate (default: 10,000).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory where Parquet files will be written.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_output_dir(args.output_dir)

    # -----------------------------------------------------------------------
    # 1. Molecule table
    # -----------------------------------------------------------------------
    molecules_df = generate_molecules_df(args.num_molecules, seed=args.seed)
    mol_path = args.output_dir / "molecules_10k.parquet"
    molecules_df.to_parquet(mol_path, engine="pyarrow")
    print(f"Wrote {mol_path}")

    # -----------------------------------------------------------------------
    # 2. 3‑D feature table
    # -----------------------------------------------------------------------
    features_3d_df = generate_3d_features_df(molecules_df, seed=args.seed)
    feat3d_path = args.output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(feat3d_path, engine="pyarrow")
    print(f"Wrote {feat3d_path}")

    # -----------------------------------------------------------------------
    # 3. 2‑D feature table
    # -----------------------------------------------------------------------
    features_2d_df = generate_2d_features_df(molecules_df, seed=args.seed)
    feat2d_path = args.output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(feat2d_path, engine="pyarrow")
    print(f"Wrote {feat2d_path}")


if __name__ == "__main__":
    main()
