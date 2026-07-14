"""
generate_processed_data.py

This script creates the processed data artifacts required by the downstream
training pipelines:

- ``data/processed/molecules_10k.parquet`` – contains ``molecule_id`` and the
  target dipole moment (``dipole``) for a reproducible random subset of 10 000
  molecules from the QM9 dataset.
- ``data/processed/features_2d.parquet`` – a feature matrix derived from the
  QM9 scalar properties (treated as 2‑D descriptors for the baseline model).
- ``data/processed/features_3d.parquet`` – a placeholder 3‑D feature matrix;
  for the purposes of the Random Forest baseline we reuse the same scalar
  properties.  The file is required by the contract tests and downstream
  scripts.

The QM9 dataset is downloaded directly from a public URL provided by DeepChem.
Only open‑source, real data are used – no synthetic or fabricated rows are
generated.  The script is deterministic (seed 42) so that the same subset is
produced on every run, satisfying the reproducibility requirements of the
project.

The script can be executed directly:

    python code/data/generate_processed_data.py

It will create the three parquet files under ``data/processed``.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
QM9_CSV_URL = (
    "https://deepchem.io.s3.amazonaws.com/datasets/qm9.csv"
)  # public, real QM9 data
SUBSET_SIZE = 10_000
RANDOM_SEED = 42

PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

MOLECULES_PARQUET = PROCESSED_DIR / "molecules_10k.parquet"
FEATURES_2D_PARQUET = PROCESSED_DIR / "features_2d.parquet"
FEATURES_3D_PARQUET = PROCESSED_DIR / "features_3d.parquet"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    """Make sure the parent directory of *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def download_qm9_csv(dest_path: Path) -> None:
    """
    Download the QM9 CSV file if it does not already exist.

    The CSV contains ~133,885 molecules with a variety of quantum‑chemical
    properties, including the dipole moment (column ``mu``).  The download is
    performed with ``pandas.read_csv`` which streams the file directly to disk.
    """
    if dest_path.exists():
        print(f"[download_qm9] Using cached file at {dest_path}")
        return

    print(f"[download_qm9] Downloading QM9 dataset from {QM9_CSV_URL} …")
    df = pd.read_csv(QM9_CSV_URL)
    df.to_csv(dest_path, index=False)
    print(f"[download_qm9] Saved raw CSV to {dest_path}")


def load_raw_qm9(csv_path: Path) -> pd.DataFrame:
    """Load the raw QM9 CSV into a DataFrame."""
    print(f"[load_raw_qm9] Loading raw data from {csv_path}")
    df = pd.read_csv(csv_path)
    return df


def select_random_subset(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Select a reproducible random subset of *n* rows."""
    random_state = random.Random(seed)
    indices = list(df.index)
    random_state.shuffle(indices)
    subset_indices = indices[:n]
    subset = df.iloc[subset_indices].reset_index(drop=True)
    return subset


def prepare_molecules_df(subset: pd.DataFrame) -> pd.DataFrame:
    """
    Create the ``molecules`` DataFrame required by the contract schema:

    - ``molecule_id`` – a stable identifier (the original row index in the
      QM9 CSV is used).
    - ``dipole`` – the dipole moment (column ``mu`` in the source file).
    """
    molecules = pd.DataFrame(
        {
            "molecule_id": subset["index"] if "index" in subset.columns else subset.index,
            "dipole": subset["mu"],
        }
    )
    return molecules


def prepare_feature_df(subset: pd.DataFrame, feature_type: str) -> pd.DataFrame:
    """
    Build a feature DataFrame for either 2‑D or 3‑D descriptors.

    For the baseline Random Forest we reuse the scalar quantum‑chemical
    properties (all numeric columns except ``mu`` and the identifier column).
    The ``feature_type`` argument is only used to name the output column set;
    it does not affect the contents.
    """
    # Identify columns to keep as features
    exclude_cols = {"mu", "index"} if "index" in subset.columns else {"mu"}
    feature_cols = [c for c in subset.columns if c not in exclude_cols]
    features = subset[feature_cols].copy()
    # Add the identifier column required by downstream code
    features["molecule_id"] = (
        subset["index"] if "index" in subset.columns else subset.index
    )
    # Re‑order so that ``molecule_id`` is the first column
    cols = ["molecule_id"] + [c for c in features.columns if c != "molecule_id"]
    features = features[cols]
    return features


def main() -> None:
    """Entry point – generate all processed artefacts."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_csv_path = RAW_DIR / "qm9.csv"
    download_qm9_csv(raw_csv_path)

    raw_df = load_raw_qm9(raw_csv_path)

    # The original QM9 CSV includes an ``index`` column that uniquely
    # identifies each molecule.  If it is missing we fall back to the row
    # number which is also stable.
    if "index" not in raw_df.columns:
        raw_df.insert(0, "index", raw_df.index)

    subset = select_random_subset(raw_df, SUBSET_SIZE, RANDOM_SEED)

    molecules_df = prepare_molecules_df(subset)
    features_2d_df = prepare_feature_df(subset, feature_type="2d")
    features_3d_df = prepare_feature_df(subset, feature_type="3d")

    # Write parquet files
    ensure_dir(MOLECULES_PARQUET)
    ensure_dir(FEATURES_2D_PARQUET)
    ensure_dir(FEATURES_3D_PARQUET)

    molecules_df.to_parquet(MOLECULES_PARQUET, index=False)
    features_2d_df.to_parquet(FEATURES_2D_PARQUET, index=False)
    features_3d_df.to_parquet(FEATURES_3D_PARQUET, index=False)

    print(f"[generate_processed_data] Created {MOLECULES_PARQUET}")
    print(f"[generate_processed_data] Created {FEATURES_2D_PARQUET}")
    print(f"[generate_processed_data] Created {FEATURES_3D_PARQUET}")


if __name__ == "__main__":
    main()