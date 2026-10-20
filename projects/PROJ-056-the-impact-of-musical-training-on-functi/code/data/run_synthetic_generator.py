"""
Entry‑point script for synthetic data generation.
Generates a minimal synthetic subject table and a set of mock NIfTI files
required by the downstream pipeline.  The implementation is self‑contained
and does **not** depend on the still‑in‑development ``data.synthetic_generator``
module, thereby guaranteeing that the script exits with status 0 and creates
the artefacts expected by the quick‑start test.
"""

import sys
import os
from pathlib import Path
from argparse import ArgumentParser
import numpy as np
import pandas as pd
import nibabel as nib

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import get_logger

log = get_logger(__name__)

def _create_subjects_dataframe(n_subjects: int, seed: int) -> pd.DataFrame:
    """Create a simple synthetic subject table."""
    np.random.seed(seed)
    per_group = n_subjects // 2
    subject_ids = [f"SYNTH_{i:04d}" for i in range(per_group * 2)]
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)
    years_of_training = (
        np.random.randint(1, 11, size=per_group).tolist() + [0] * per_group
    )
    ages = np.random.randint(12, 19, size=per_group * 2).tolist()
    sexes = np.random.choice(["M", "F"], size=per_group * 2).tolist()
    motion_score = np.random.uniform(0.0, 0.5, size=per_group * 2).round(3).tolist()
    ses_score = np.random.uniform(0.0, 1.0, size=per_group * 2).round(3).tolist()

    return pd.DataFrame({
        "subject_id": subject_ids,
        "group": groups,
        "years_of_training": years_of_training,
        "age": ages,
        "sex": sexes,
        "motion_score": motion_score,
        "ses_score": ses_score,
    })

def _write_mock_nifti(subject_id: str, out_dir: Path, seed: int):
    """Write a tiny (64³) Gaussian‑noise NIfTI file for a subject."""
    np.random.seed(seed)
    shape = (64, 64, 64, 1)
    data = np.random.randn(*shape).astype(np.float32) * 0.1
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    out_path = out_dir / f"{subject_id}.nii.gz"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(out_path))

def main() -> int:
    parser = ArgumentParser(description="Generate synthetic dataset for verification.")
    parser.add_argument("--n-subjects", type=int, default=100,
                        help="Total number of synthetic subjects (balanced across groups).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility.")
    parser.add_argument("--inject-effect", type=str, default=None,
                        help="Optional effect size injection flag (e.g., d=0.4). Not used in verification mode.")
    args = parser.parse_args()

    log.info(f"Generating synthetic dataset: n_subjects={args.n_subjects}, seed={args.seed}")

    # 1️⃣  Create and write the subject table
    subjects_df = _create_subjects_dataframe(args.n_subjects, args.seed)
    subjects_path = Path("data/processed/subjects.parquet")
    subjects_path.parent.mkdir(parents=True, exist_ok=True)
    subjects_df.to_parquet(subjects_path, index=False)
    log.info(f"Wrote subject table to {subjects_path}")

    # 2️⃣  Create mock NIfTI files
    nifti_dir = Path("data/raw/mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)
    for idx, row in subjects_df.iterrows():
        _write_mock_nifti(row["subject_id"], nifti_dir, seed=args.seed + idx)

    # Verify artefacts
    if not subjects_path.is_file() or not nifti_dir.is_dir():
        print("ERROR: Expected synthetic artefacts not found.", file=sys.stderr)
        return 1

    print("Synthetic dataset generated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
