"""Generate the processed dataset artifacts for US1.

This script creates three parquet files under ``data/processed``:
- ``molecules_10k.parquet``: the reproducible 10 k molecule subset.
- ``features_3d.parquet``: 3‑D geometric features extracted from the subset.
- ``features_2d.parquet``: 2‑D descriptor matrix (e.g., Morgan fingerprints,
  Coulomb matrices) extracted from the subset.

The script is invoked by the quick‑start run‑book and must exit with
status code 0 while writing the files to the exact paths expected by the
downstream training and analysis pipelines.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features


def ensure_dir(path: Path) -> None:
    """Create the parent directory for *path* if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write *df* to *path* as a parquet file using pyarrow."""
    ensure_dir(path)
    df.to_parquet(path, engine="pyarrow", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate processed QM9 subset and feature matrices."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory where parquet files will be written (default: data/processed).",
    )
    args = parser.parse_args()

    output_dir: Path = args.output_dir

    # 1. Create the reproducible 10 k molecule subset
    molecules_df = create_reproducible_subset()
    molecules_path = output_dir / "molecules_10k.parquet"
    write_parquet(molecules_df, molecules_path)

    # 2. Extract 3‑D features
    features_3d_df = extract_3d_features(molecules_df)
    features_3d_path = output_dir / "features_3d.parquet"
    write_parquet(features_3d_df, features_3d_path)

    # 3. Extract 2‑D descriptors
    features_2d_df = extract_2d_features(molecules_df)
    features_2d_path = output_dir / "features_2d.parquet"
    write_parquet(features_2d_df, features_2d_path)

    print(f"✅ Generated:\n  {molecules_path}\n  {features_3d_path}\n  {features_2d_path}")


if __name__ == "__main__":
    main()
