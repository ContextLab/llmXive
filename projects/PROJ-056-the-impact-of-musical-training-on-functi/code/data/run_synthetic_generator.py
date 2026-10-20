"""
Entry‑point script for synthetic data generation.
Generates a realistic synthetic adolescent rs‑fMRI cohort with
optional missing values and corrupted NIfTI files to exercise the
exclusion logic of the pipeline.
"""

import sys
import os
from pathlib import Path
from argparse import ArgumentParser
import numpy as np
import pandas as pd
import nibabel as nib

# Ensure project root is importable so that ``utils.logging`` can be found
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import get_logger
from data.mock_nifti import create_corrupted_nifti

log = get_logger(__name__)

def _create_subjects_dataframe(n_subjects: int, seed: int) -> pd.DataFrame:
    """Create a synthetic subject table with balanced groups."""
    np.random.seed(seed)
    per_group = n_subjects // 2
    total = per_group * 2
    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)

    # Years of training: musicians get 1‑10 years, non‑musicians get 0
    years_of_training = (
        np.random.randint(1, 11, size=per_group).tolist() + [0] * per_group
    )

    ages = np.random.randint(12, 19, size=total).tolist()
    sexes = np.random.choice(["M", "F"], size=total).tolist()
    motion_score = np.random.uniform(0.0, 0.5, size=total).round(3).tolist()
    ses_score = np.random.uniform(0.0, 1.0, size=total).round(3).tolist()

    df = pd.DataFrame({
        "subject_id": subject_ids,
        "group": groups,
        "years_of_training": years_of_training,
        "age": ages,
        "sex": sexes,
        "motion_score": motion_score,
        "ses_score": ses_score,
    })

    # ------------------------------------------------------------------
    # 5 % missing ``years_of_training`` to test exclusion logic
    # ------------------------------------------------------------------
    n_missing = max(1, int(0.05 * len(df)))
    missing_idx = np.random.choice(df.index, size=n_missing, replace=False)
    df.loc[missing_idx, "years_of_training"] = np.nan

    return df

def _write_mock_nifti(subject_id: str, out_dir: Path, seed: int, corrupt: bool = False):
    """Write a tiny (64³) Gaussian‑noise NIfTI file, optionally corrupted."""
    np.random.seed(seed)
    shape = (64, 64, 64, 1)
    if corrupt:
        # Create an invalid file that nibabel cannot read
        corrupt_path = out_dir / f"{subject_id}.nii.gz"
        create_corrupted_nifti(str(corrupt_path))
        log.debug(f"Written corrupted NIfTI for {subject_id}")
        return

    data = np.random.randn(*shape).astype(np.float32) * 0.1
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    out_path = out_dir / f"{subject_id}.nii.gz"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(out_path))
    log.debug(f"Wrote mock NIfTI for {subject_id}")

def main() -> int:
    parser = ArgumentParser(
        description="Generate synthetic dataset for verification."
    )
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=100,
        help="Total number of synthetic subjects (balanced across groups).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--inject-effect",
        type=str,
        default=None,
        help="Optional effect size injection flag (e.g., d=0.4). Not used in verification mode.",
    )
    args = parser.parse_args()

    log.info(
        f"Generating synthetic dataset: n_subjects={args.n_subjects}, seed={args.seed}"
    )

    # ------------------------------------------------------------------
    # 1️⃣ Create and write the subject table
    # ------------------------------------------------------------------
    subjects_df = _create_subjects_dataframe(args.n_subjects, args.seed)
    subjects_path = Path("data/processed/subjects.parquet")
    subjects_path.parent.mkdir(parents=True, exist_ok=True)
    subjects_df.to_parquet(subjects_path, index=False)
    log.info(f"Wrote subject table to {subjects_path}")

    # ------------------------------------------------------------------
    # 2️⃣ Create mock NIfTI files (3 % corrupted)
    # ------------------------------------------------------------------
    nifti_dir = Path("data/raw/mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)

    n_corrupt = max(1, int(0.03 * len(subjects_df)))
    corrupt_indices = set(
        np.random.choice(subjects_df.index, size=n_corrupt, replace=False)
    )

    for idx, row in subjects_df.iterrows():
        subject_id = row["subject_id"]
        seed = args.seed + idx
        corrupt = idx in corrupt_indices
        _write_mock_nifti(subject_id, nifti_dir, seed=seed, corrupt=corrupt)

    # Verify artefacts
    if not subjects_path.is_file() or not nifti_dir.is_dir():
        print(
            "ERROR: Expected synthetic artefacts not found.", file=sys.stderr
        )
        return 1

    print("Synthetic dataset generated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
