"""
Generate the processed data artefacts required by task T020.

This script reads the QM9 dataset (downloaded by ``download_qm9.py``), selects a
reproducible 10 000‑molecule subset (created by ``create_subset.py``), extracts
the necessary molecular information, builds 3‑D and 2‑D feature tables and writes
them to Parquet files under ``data/processed/``:

- ``molecules_10k.parquet`` – basic molecule information (id, atoms,
  coordinates, dipole moment).
- ``features_3d.parquet`` – 3‑D features such as atomic coordinates and
  connectivity.
- ``features_2d.parquet`` – 2‑D descriptors (Morgan fingerprints,
  Coulomb matrix, etc.).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# Local imports – the API surface is defined in the task description.
from data.create_subset import create_reproducible_subset
from data.download_qm9 import download_qm9  # ensures the raw file exists
from data.generate_processed_data import (
    ensure_dir,
    load_qm9_npz,
    extract_molecule_entries,
    build_3d_features,
    build_2d_features,
)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create processed QM9 parquet files for a 10k random subset."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "processed",
        help="Directory where the parquet files will be written.",
    )
    args = parser.parse_args()

    # ----------------------------------------------------------------------
    # 1. Ensure the output directory exists
    # ----------------------------------------------------------------------
    ensure_dir(args.output_dir)

    # ----------------------------------------------------------------------
    # 2. Download the raw QM9 data if it is not already present.
    # ----------------------------------------------------------------------
    # ``download_qm9`` returns the path to the downloaded ``qm9.npz`` file.
    raw_qm9_path = download_qm9()
    if not raw_qm9_path.is_file():
        raise FileNotFoundError(f"QM9 data not found at {raw_qm9_path}")

    # ----------------------------------------------------------------------
    # 3. Load the raw NumPy archive.
    # ----------------------------------------------------------------------
    qm9_data = load_qm9_npz(raw_qm9_path)

    # ----------------------------------------------------------------------
    # 4. Determine the reproducible 10 k subset.
    # ----------------------------------------------------------------------
    subset_ids = create_reproducible_subset(qm9_data, n_samples=10_000, seed=42)

    # ----------------------------------------------------------------------
    # 5. Extract molecule entries for the selected IDs.
    # ----------------------------------------------------------------------
    molecules = extract_molecule_entries(qm9_data, subset_ids)

    # Convert the list of dicts to a DataFrame.
    df_molecules = pd.DataFrame(molecules)

    # ----------------------------------------------------------------------
    # 6. Build feature tables.
    # ----------------------------------------------------------------------
    df_features_3d = build_3d_features(molecules)
    df_features_2d = build_2d_features(molecules)

    # ----------------------------------------------------------------------
    # 7. Write parquet files.
    # ----------------------------------------------------------------------
    molecules_path = args.output_dir / "molecules_10k.parquet"
    features_3d_path = args.output_dir / "features_3d.parquet"
    features_2d_path = args.output_dir / "features_2d.parquet"

    df_molecules.to_parquet(molecules_path, index=False)
    df_features_3d.to_parquet(features_3d_path, index=False)
    df_features_2d.to_parquet(features_2d_path, index=False)

    print(f"✅ Created:\n  {molecules_path}\n  {features_3d_path}\n  {features_2d_path}")

if __name__ == "__main__":
    main()