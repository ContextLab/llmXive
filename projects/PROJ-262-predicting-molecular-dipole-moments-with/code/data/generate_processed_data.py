"""
Generate the final processed data artefacts for User Story 1.

This script consolidates the subset of QM9 molecules (10 k entries) and the
extracted 2‑D and 3‑D feature matrices into Parquet files:

- ``data/processed/molecules_10k.parquet``
- ``data/processed/features_3d.parquet``
- ``data/processed/features_2d.parquet``

The script assumes that the upstream preprocessing steps have already been
executed:

* ``code/data/create_subset.py`` – creates ``data/processed/subset_ids.txt``.
* ``code/data/preprocess_3d.py`` – produces ``data/processed/3d_features.csv``.
* ``code/data/extract_2d_descriptors.py`` – produces ``data/processed/2d_features.csv``.

If any of those files are missing, the script raises a clear ``FileNotFoundError``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


def _load_subset_ids(subset_path: Path) -> list[str]:
    """Load the list of molecule IDs that belong to the 10 k subset."""
    if not subset_path.is_file():
        raise FileNotFoundError(f"Subset ID file not found: {subset_path}")
    return [line.strip() for line in subset_path.read_text().splitlines() if line.strip()]


def _filter_dataframe_by_ids(df: pd.DataFrame, id_column: str, ids: set[str]) -> pd.DataFrame:
    """Return rows whose ``id_column`` value is present in ``ids``."""
    return df[df[id_column].isin(ids)].reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate processed Parquet files for the 10k QM9 subset."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory where the Parquet files will be written (default: data/processed).",
    )
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Expected input artefacts
    subset_ids_path = Path("data/processed/subset_ids.txt")
    features_3d_csv = Path("data/processed/3d_features.csv")
    features_2d_csv = Path("data/processed/2d_features.csv")

    # Load IDs for the 10 k random subset
    subset_ids = _load_subset_ids(subset_ids_path)
    subset_id_set = set(subset_ids)

    # Load and filter 3‑D features
    if not features_3d_csv.is_file():
        raise FileNotFoundError(f"3D features file not found: {features_3d_csv}")
    df_3d = pd.read_csv(features_3d_csv)
    df_3d_filtered = _filter_dataframe_by_ids(df_3d, "molecule_id", subset_id_set)

    # Load and filter 2‑D features
    if not features_2d_csv.is_file():
        raise FileNotFoundError(f"2D features file not found: {features_2d_csv}")
    df_2d = pd.read_csv(features_2d_csv)
    df_2d_filtered = _filter_dataframe_by_ids(df_2d, "molecule_id", subset_id_set)

    # The molecule table itself – we reuse the 3‑D dataframe's identifier column
    # because it already contains the required metadata (atom types, coordinates,
    # dipole moment).  Any additional columns present are retained.
    molecules_parquet = output_dir / "molecules_10k.parquet"
    df_molecules = df_3d_filtered.copy()
    df_molecules.to_parquet(molecules_parquet, index=False)

    # Write feature matrices
    features_3d_parquet = output_dir / "features_3d.parquet"
    df_3d_filtered.to_parquet(features_3d_parquet, index=False)

    features_2d_parquet = output_dir / "features_2d.parquet"
    df_2d_filtered.to_parquet(features_2d_parquet, index=False)

    print(f"✅ Generated:\n  {molecules_parquet}\n  {features_3d_parquet}\n  {features_2d_parquet}")


if __name__ == "__main__":
    main()
