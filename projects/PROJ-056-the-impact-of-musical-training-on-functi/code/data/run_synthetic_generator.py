"""
Entry‑point script for synthetic data generation.
"""
import sys
import os
from pathlib import Path
from argparse import ArgumentParser

# Ensure project root is in sys.path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.synthetic_generator import generate_synthetic_dataset
from utils.logging import get_logger

log = get_logger(__name__)

def main() -> int:
    parser = ArgumentParser(description="Generate synthetic dataset for verification.")
    parser.add_argument("--n-subjects", type=int, default=100,
                        help="Total number of synthetic subjects (balanced across groups).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility.")
    parser.add_argument("--inject-effect", type=str, default=None,
                        help="Optional effect size injection flag (e.g., d=0.4). Not used in verification mode.")
    args = parser.parse_args()

    # Parse the optional inject-effect flag (currently a no‑op)
    inject_effect = None
    if args.inject_effect:
        try:
            # Expected format: d=<float>
            key, val = args.inject_effect.split("=")
            if key.strip().lower() == "d":
                inject_effect = float(val)
        except Exception:
            log.warning(f"Unable to parse --inject-effect value '{args.inject_effect}'. Ignoring.")

    log.info(f"Generating synthetic dataset: n_subjects={args.n_subjects}, seed={args.seed}, inject_effect={inject_effect}")
    generate_synthetic_dataset(
        n_subjects=args.n_subjects,
        seed=args.seed,
        inject_effect=inject_effect,
    )

    subjects_path = Path("data/processed/subjects.parquet")
    nifti_dir = Path("data/raw/mock_nifti")

    if not subjects_path.is_file() or not nifti_dir.is_dir():
        print("ERROR: Expected synthetic artefacts not found.", file=sys.stderr)
        return 1

    print("Synthetic dataset generated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())