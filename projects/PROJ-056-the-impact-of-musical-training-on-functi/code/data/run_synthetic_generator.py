"""
Entry‑point script for synthetic data generation.

Generates:
  * data/processed/subjects.parquet
  * data/raw/mock_nifti/ (one mock NIfTI per subject)
"""

import sys
from pathlib import Path
from argparse import ArgumentParser

from data.synthetic_generator import generate_synthetic_dataset
from utils.logging import get_logger

log = get_logger(__name__)

def main() -> int:
    parser = ArgumentParser(description="Generate synthetic dataset for verification.")
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=150,
        help="Total number of synthetic subjects (rounded to even, balanced).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    log.info(f"Generating synthetic dataset: n_subjects={args.n_subjects}, seed={args.seed}")
    generate_synthetic_dataset(n_subjects=args.n_subjects, seed=args.seed)

    subjects_path = Path("data/processed/subjects.parquet")
    nifti_dir = Path("data/raw/mock_nifti")
    missing = []
    if not subjects_path.is_file():
        missing.append(str(subjects_path))
    if not nifti_dir.is_dir() or not any(nifti_dir.iterdir()):
        missing.append(str(nifti_dir))

    if missing:
        print(f"ERROR: Expected synthetic artefacts not found: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("Synthetic dataset generated successfully.")
    print(f"  - Behavioural table: {subjects_path}")
    print(f"  - Mock NIfTI directory: {nifti_dir} (contains {len(list(nifti_dir.iterdir()))} files)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
