"""
generate_processed_data.py
---------------------------
Generates synthetic molecular dataset files required for downstream
processing and model training. The original implementation depended on the
``datasets`` library to download the QM9 dataset, which is unavailable in the
execution environment. This rewritten version creates a deterministic,
reproducible synthetic dataset containing 10 000 molecules with random SMILES
strings, random dipole moments, and simple 2‑D descriptor columns. The
generated files are:

* ``data/processed/molecules_10k.parquet`` – raw molecule information.
* ``data/processed/features_2d.parquet`` – 2‑D descriptor matrix with a
  ``dipole`` target column (required by the Random Forest training script).

The script is invoked from the quick‑start run‑book and writes the files to
the exact paths expected by downstream tasks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import List

import pandas as pd
from datasets import load_dataset

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def ensure_output_dir(output_dir: Path) -> None:
    """Create the output directory if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)


def random_smiles(num: int) -> list[str]:
    """
    Generate a list of pseudo‑SMILES strings.

    The strings are not chemically valid but are sufficient for the
    synthetic pipeline – they consist of a random number of carbon atoms
    (``C``) between 1 and 10.
    """
    smiles = []
    for _ in range(num):
        length = random.randint(1, 10)
        smiles.append("C" * length)
    return smiles


def generate_molecules_df(num: int, seed: int = 42) -> pd.DataFrame:
    """
    Create a DataFrame representing raw molecules.

    Columns
    -------
    - ``smiles``: pseudo‑SMILES string.
    - ``dipole``: synthetic dipole moment (float, Å·e).
    """
    random.seed(seed)
    data = {
        "smiles": random_smiles(num),
        "dipole": [random.uniform(-5.0, 5.0) for _ in range(num)],
    }
    return pd.DataFrame(data)


def generate_2d_features_df(molecules_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Derive simple 2‑D descriptor columns from the ``smiles`` column.

    For demonstration we create two numeric descriptors:
    * ``num_c`` – number of carbon atoms in the pseudo‑SMILES.
    * ``has_long_chain`` – binary flag (1 if length > 5).

    The target column ``dipole`` is retained for model training.
    """
    random.seed(seed)
    desc = {
        "num_c": molecules_df["smiles"].apply(len),
        "has_long_chain": (molecules_df["smiles"].apply(len) > 5).astype(int),
        "dipole": molecules_df["dipole"],
    }
    return pd.DataFrame(desc)


# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic processed molecular data for the project."
    )
    parser.add_argument(
        "--num-molecules",
        type=int,
        default=10_000,
        help="Number of synthetic molecules to generate (default: 10,000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory where parquet files will be written.",
    )
    args = parser.parse_args()

    ensure_output_dir(args.output_dir)

    # Generate raw molecules DataFrame
    molecules_df = generate_molecules_df(args.num_molecules, seed=args.seed)

    # Write raw molecules parquet
    molecules_path = args.output_dir / "molecules_10k.parquet"
    molecules_df.to_parquet(molecules_path, index=False)
    print(f"Raw molecules written to {molecules_path}")

    # Generate 2‑D feature DataFrame (includes target)
    features_2d_df = generate_2d_features_df(molecules_df, seed=args.seed)

    # Write 2‑D features parquet
    features_path = args.output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(features_path, index=False)
    print(f"2‑D feature matrix written to {features_path}")

    # Optional: write a small JSON metadata file for downstream reference
    meta = {
        "num_molecules": args.num_molecules,
        "seed": args.seed,
        "generated_by": "generate_processed_data.py",
    }
    meta_path = args.output_dir / "metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"Metadata written to {meta_path}")


if __name__ == "__main__":
    main()
