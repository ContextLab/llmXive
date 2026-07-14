"""
Generate processed data artifacts for the QM9 subset.

This script orchestrates the creation of three parquet files required by
downstream pipelines:

1. ``data/processed/molecules_10k.parquet`` – the full molecule table
   (IDs, atom types, 3‑D coordinates, dipole moments, etc.).
2. ``features_3d.parquet`` – a table containing 3‑D‑derived features for each
   molecule (e.g., Coulomb matrix, distance matrix).
3. ``features_2d.parquet`` – a table containing 2‑D descriptors (e.g., Morgan
   fingerprints, graph‑level statistics).

The heavy‑lifting is delegated to helper functions defined in
``code/data/generate_processed_data.py`` (the original module).  Those
helpers already implement robust loading, feature extraction and output
handling; this script merely wires them together and ensures that the
expected files are written to disk.

The script is safe to run multiple times – existing files are overwritten
only after successful generation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import the public helpers from the original module.  They are part of the
# project's API surface and therefore must be used rather than re‑implemented.
from data.generate_processed_data import (
    ensure_output_dir,
    load_molecule_subset,
    extract_3d_features_wrapper,
    extract_2d_features_wrapper,
    generate_processed_data,
)

def parse_args() -> argparse.Namespace:
    """Parse command‑line arguments.

    The script accepts an optional ``--subset-size`` argument for debugging
    purposes; the default matches the US1 requirement of 10 000 molecules.
    """
    parser = argparse.ArgumentParser(
        description="Generate processed QM9 subset and feature parquet files."
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10_000,
        help="Number of molecules to include in the processed subset.",
    )
    return parser.parse_args()

def main() -> None:
    """Entry point for the script."""
    args = parse_args()

    # Ensure the output directory exists.
    output_dir = Path("data/processed")
    ensure_output_dir(output_dir)

    # Load the reproducible subset (the underlying function knows how to
    # locate the raw QM9 files and apply the fixed random seed).
    try:
        molecules_df = load_molecule_subset(size=args.subset_size)
    except Exception as exc:
        print(f"Failed to load molecule subset: {exc}", file=sys.stderr)
        sys.exit(1)

    # Generate 3‑D and 2‑D feature tables.
    try:
        features_3d_df = extract_3d_features_wrapper(molecules_df)
        features_2d_df = extract_2d_features_wrapper(molecules_df)
    except Exception as exc:
        print(f"Feature extraction failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Persist all three tables as parquet files.
    try:
        generate_processed_data(
            molecules=molecules_df,
            features_3d=features_3d_df,
            features_2d=features_2d_df,
            output_dir=output_dir,
        )
    except Exception as exc:
        print(f"Failed to write parquet files: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Successfully wrote:\n"
        f"  - {output_dir / 'molecules_10k.parquet'}\n"
        f"  - {output_dir / 'features_3d.parquet'}\n"
        f"  - {output_dir / 'features_2d.parquet'}"
    )

if __name__ == "__main__":
    main()
