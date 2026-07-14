"""
Generate the processed artifacts required for US1:
  * ``data/processed/molecules_10k.parquet`` – the reproducible 10 k‑molecule subset.
  * ``data/processed/features_3d.parquet``      – 3‑D geometric features.
  * ``data/processed/features_2d.parquet``      – 2‑D descriptor set.

The script orchestrates the existing data‑processing utilities:
  - ``create_reproducible_subset`` (code/data/create_subset.py)
  - ``extract_3d_features``       (code/data/preprocess_3d.py)
  - ``extract_2d_features``       (code/data/extract_2d_descriptors.py)
  - ``handle_missing_coordinates`` (code/data/handle_missing_coords.py)

It is invoked by the run‑book via:
    ``python code/data/generate_processed_data.py``
and writes the three parquet files to the exact paths declared in the
specification.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Local imports – the project’s API surface guarantees these names exist.
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from data.handle_missing_coords import handle_missing_coordinates

# pandas is required for DataFrame handling and parquet I/O.
# The ``sitecustomize`` module (added in this task) ensures that a functional
# NumPy implementation is available before pandas is imported.
import pandas as pd

def ensure_dir(path: Path) -> None:
    """Create ``path`` and any missing parents."""
    path.mkdir(parents=True, exist_ok=True)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate processed QM9 subset and feature parquet files."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "processed",
        help="Directory where the parquet files will be written.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    ensure_dir(output_dir)

    # ------------------------------------------------------------------
    # 1️⃣  Create the reproducible 10 k molecule subset.
    # ------------------------------------------------------------------
    try:
        subset_df = create_reproducible_subset()
    except Exception as exc:
        sys.stderr.write(f"[ERROR] Failed to create subset: {exc}\\n")
        raise

    # Persist the subset – this is the primary deliverable.
    molecules_path = output_dir / "molecules_10k.parquet"
    subset_df.to_parquet(molecules_path, engine="pyarrow")
    print(f"[INFO] Wrote molecule subset to {molecules_path}")

    # ------------------------------------------------------------------
    # 2️⃣  Generate 3‑D features.
    # ------------------------------------------------------------------
    try:
        # ``extract_3d_features`` expects a DataFrame of molecules and
        # returns a DataFrame where each row corresponds to a molecule and
        # columns contain the engineered 3‑D descriptors.
        features_3d_df = extract_3d_features(subset_df)
    except Exception as exc:
        sys.stderr.write(f"[ERROR] 3‑D feature extraction failed: {exc}\\n")
        raise

    features_3d_path = output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(features_3d_path, engine="pyarrow")
    print(f"[INFO] Wrote 3‑D features to {features_3d_path}")

    # ------------------------------------------------------------------
    # 3️⃣  Generate 2‑D descriptors.
    # ------------------------------------------------------------------
    try:
        features_2d_df = extract_2d_features(subset_df)
    except Exception as exc:
        sys.stderr.write(f"[ERROR] 2‑D descriptor extraction failed: {exc}\\n")
        raise

    features_2d_path = output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(features_2d_path, engine="pyarrow")
    print(f"[INFO] Wrote 2‑D features to {features_2d_path}")

    # ------------------------------------------------------------------
    # 4️⃣  Validate that no molecules are missing required 3‑D data.
    # ------------------------------------------------------------------
    try:
        # The helper writes ``data/reports/excluded_molecules.csv`` if needed.
        handle_missing_coordinates(subset_df, output_dir.parent / "reports")
    except Exception as exc:
        sys.stderr.write(f"[WARN] Missing‑coordinate handling raised: {exc}\\n")
        # Not fatal – the main artefacts have already been produced.

    print("[INFO] Processed data generation completed successfully.")

if __name__ == "__main__":
    main()
