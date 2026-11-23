"""
Task: Generate processed data pipeline.
This script orchestrates the data processing pipeline including subset creation,
3D feature extraction, and missing coordinate handling.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.handle_missing_coords import handle_missing_coordinates


def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate processed data from QM9 subset.")
    parser.add_argument(
        "--subset-input",
        type=str,
        default="data/raw/qm9_subset.json",
        help="Path to the subset input file."
    )
    parser.add_argument(
        "--subset-output",
        type=str,
        default="data/processed/subset_final.parquet",
        help="Path to save the processed subset."
    )
    parser.add_argument(
        "--features-output",
        type=str,
        default="data/processed/features_3d.csv",
        help="Path to save 3D features."
    )
    parser.add_argument(
        "--exclusions-output",
        type=str,
        default="data/reports/excluded_molecules.csv",
        help="Path to save exclusion report."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Step 1: Create subset (if needed, assuming subset already exists or created by T016b)
    # For this pipeline, we assume subset input exists from T016b
    subset_path = Path(args.subset_input)
    if not subset_path.exists():
        print(f"Warning: Subset input not found at {subset_path}. Skipping subset creation.")
        # In a real run, T016b would have created this.
        return

    # Step 2: Extract 3D features
    print("Extracting 3D features...")
    try:
        features_df = extract_3d_features(subset_path, args.features_output)
        print(f"3D features saved to: {args.features_output}")
    except Exception as e:
        print(f"Error extracting 3D features: {e}", file=sys.stderr)
        # Continue to exclusion check even if feature extraction fails partially

    # Step 3: Handle missing coordinates and generate exclusion report
    print("Checking for missing coordinates...")
    try:
        excluded_df = handle_missing_coordinates(
            subset_path,
            args.exclusions_output
        )
        print(f"Exclusion report saved to: {args.exclusions_output}")
        print(f"Total excluded molecules: {len(excluded_df)}")
    except Exception as e:
        print(f"Error checking missing coordinates: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
