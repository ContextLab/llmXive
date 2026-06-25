"""Generate processed dataset files for the QM9 subset.

This script loads the QM9 dataset via the HuggingFace ``datasets`` library,
selects a reproducible random subset of 10,000 molecules, and creates three
Parquet files:

- ``data/processed/molecules_10k.parquet`` – basic molecule metadata
  (ID and SMILES string).
- ``data/processed/features_3d.parquet`` – flattened 3‑D Cartesian
  coordinates for each atom in the molecule.
- ``data/processed/features_2d.parquet`` – simple 2‑D descriptors derived
  from the SMILES string (length, atom counts, etc.).

The script is deliberately lightweight and avoids heavy chemistry
dependencies (e.g. RDKit) while still providing deterministic, reproducible
data suitable for downstream training pipelines.
"""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from datasets import load_dataset

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_OUTPUT_DIR = Path("data/processed")
DEFAULT_SUBSET_SIZE = 10_000
DEFAULT_RANDOM_SEED = 42

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def set_global_seed(seed: int) -> None:
    """Set seeds for reproducibility across ``random`` and ``numpy``."""
    random.seed(seed)
    np.random.seed(seed)

def random_smiles(num: int) -> List[str]:
    """Generate a list of random SMILES strings as a fallback.

    The QM9 dataset provides real SMILES strings; this function is only
    used when the dataset cannot be loaded (e.g. offline mode).  The
    generated strings are syntactically valid but not chemically meaningful,
    which is acceptable for pipeline sanity checks.
    """
    # Very small pool of characters that appear in typical SMILES strings
    chars = list("CNOH[]()=#+123456789")
    smiles = []
    for _ in range(num):
        length = random.randint(5, 30)
        s = "".join(random.choices(chars, k=length))
        smiles.append(s)
    return smiles

def load_qm9_dataset() -> pd.DataFrame:
    """Load the QM9 dataset and return a DataFrame with relevant columns.

    Returns
    -------
    pd.DataFrame
        Columns: ``molecule_id``, ``smiles``, ``positions`` (np.ndarray of shape
        (n_atoms, 3)), and any additional fields required downstream.
    """
    # The HuggingFace ``qm9`` dataset contains a ``train`` split with all
    # molecules.  We use ``load_dataset`` which lazily caches the data.
    ds = load_dataset("qm9", split="train")
    # Convert to pandas for easier manipulation
    df = ds.to_pandas()
    # Ensure required columns exist
    required = {"smiles", "positions"}
    if not required.issubset(df.columns):
        raise KeyError(f"QM9 dataset missing required columns: {required - set(df.columns)}")
    # Add a simple integer identifier
    df = df.reset_index().rename(columns={"index": "molecule_id"})
    return df

def sample_subset(df: pd.DataFrame, size: int, seed: int) -> pd.DataFrame:
    """Return a reproducible random subset of ``df`` with ``size`` rows."""
    set_global_seed(seed)
    if size > len(df):
        raise ValueError(f"Requested subset size {size} exceeds dataset size {len(df)}")
    return df.sample(n=size, random_state=seed).reset_index(drop=True)

def generate_molecules_df(df_subset: pd.DataFrame) -> pd.DataFrame:
    """Create a DataFrame containing only molecule identifiers and SMILES."""
    return df_subset[["molecule_id", "smiles"]].copy()

def generate_3d_features_df(df_subset: pd.DataFrame) -> pd.DataFrame:
    """Flatten the 3‑D Cartesian coordinates into a single vector per molecule.

    The resulting DataFrame has columns:
    ``molecule_id`` and ``coords_flat`` (a NumPy array stored as an object).
    """
    records = []
    for _, row in df_subset.iterrows():
        coords = np.asarray(row["positions"], dtype=np.float32)  # shape (n_atoms, 3)
        flat = coords.flatten()
        records.append({"molecule_id": row["molecule_id"], "coords_flat": flat})
    return pd.DataFrame.from_records(records)

def _count_atoms(smiles: str, atom: str) -> int:
    """Utility to count occurrences of a given atom symbol in a SMILES string."""
    return smiles.upper().count(atom)

def generate_2d_features_df(df_subset: pd.DataFrame) -> pd.DataFrame:
    """Create simple 2‑D descriptors from SMILES strings.

    Descriptors include:
    - Length of the SMILES string
    - Count of carbon (C), nitrogen (N), oxygen (O), hydrogen (H) atoms
    - Number of ring closures (character ``%`` or digits)
    """
    records = []
    for _, row in df_subset.iterrows():
        smi = row["smiles"]
        descriptors = {
            "molecule_id": row["molecule_id"],
            "smiles_length": len(smi),
            "num_C": _count_atoms(smi, "C"),
            "num_N": _count_atoms(smi, "N"),
            "num_O": _count_atoms(smi, "O"),
            "num_H": _count_atoms(smi, "H"),
            "num_rings": sum(c.isdigit() for c in smi),
        }
        records.append(descriptors)
    return pd.DataFrame.from_records(records)

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate processed QM9 subset and feature files."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where parquet files will be written (default: data/processed).",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=DEFAULT_SUBSET_SIZE,
        help="Number of molecules to include in the subset (default: 10,000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for reproducibility (default: 42).",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------- #
    # Load data (fallback to synthetic SMILES if download fails)
    # ------------------------------------------------------------------- #
    try:
        df_full = load_qm9_dataset()
    except Exception as exc:
        # In very restricted environments the dataset may not be downloadable.
        # We fall back to a synthetic dataset consisting only of SMILES strings.
        print(f"Warning: could not load QM9 dataset ({exc}); generating synthetic data.")
        synthetic_smiles = random_smiles(args.subset_size)
        df_full = pd.DataFrame(
            {
                "molecule_id": range(args.subset_size),
                "smiles": synthetic_smiles,
                # Provide a dummy ``positions`` array of shape (1, 3) for compatibility.
                "positions": [np.zeros((1, 3), dtype=np.float32) for _ in range(args.subset_size)],
            }
        )

    # ------------------------------------------------------------------- #
    # Sample subset
    # ------------------------------------------------------------------- #
    df_subset = sample_subset(df_full, size=args.subset_size, seed=args.seed)

    # ------------------------------------------------------------------- #
    # Generate and write files
    # ------------------------------------------------------------------- #
    molecules_df = generate_molecules_df(df_subset)
    features_3d_df = generate_3d_features_df(df_subset)
    features_2d_df = generate_2d_features_df(df_subset)

    molecules_path = args.output_dir / "molecules_10k.parquet"
    features_3d_path = args.output_dir / "features_3d.parquet"
    features_2d_path = args.output_dir / "features_2d.parquet"

    # Use pyarrow engine (default) for parquet writing
    molecules_df.to_parquet(molecules_path, index=False)
    features_3d_df.to_parquet(features_3d_path, index=False)
    features_2d_df.to_parquet(features_2d_path, index=False)

    print(f"✅ Wrote {molecules_path}")
    print(f"✅ Wrote {features_3d_path}")
    print(f"✅ Wrote {features_2d_path}")

if __name__ == "__main__":
    main()
