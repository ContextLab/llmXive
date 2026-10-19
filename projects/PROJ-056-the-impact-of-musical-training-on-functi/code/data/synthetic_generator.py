"""
Synthetic data generator for verification mode.

This module creates a deterministic synthetic behavioural table and a set of
mock NIfTI files that conform to the expected schema. The generated files are
written to the exact locations required by downstream pipeline steps:

- ``data/processed/subjects.parquet`` – behavioural metadata
- ``data/raw/mock_nifti/<subject_id>.nii`` – one mock NIfTI per subject
"""

import numpy as np
import pandas as pd
from pathlib import Path

from utils.logging import get_logger
from data.mock_nifti import create_mock_nifti, create_corrupted_nifti

log = get_logger(__name__)

def generate_synthetic_dataset(n_subjects: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Generate a balanced synthetic cohort and write artefacts to disk.

    Parameters
    ----------
    n_subjects : int
        Desired total number of subjects (will be rounded to an even number
        and split equally between musicians and non‑musicians). The default
        of 150 satisfies the “≈75 per group” description while keeping the
        dataset small enough for quick CI runs.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        The behavioural table that is also saved as a Parquet file.
    """
    np.random.seed(seed)

    # Ensure an even split and a minimum of 50 per group (power requirement)
    per_group = max(50, n_subjects // 2)
    total = per_group * 2  # enforce exact balance
    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]

    # Group assignment
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)

    # Years of training – musicians get 1‑10 years, non‑musicians get 0
    years = (
        np.random.randint(1, 11, size=per_group).astype(float).tolist()
        + [0.0] * per_group
    )

    # Inject a small seeded proportion of missing training‑history values
    n_missing = max(1, int(0.05 * total))  # ~5 %
    missing_idx = np.random.choice(total, n_missing, replace=False)
    for idx in missing_idx:
        years[idx] = np.nan

    # Demographic / confound columns
    ages = np.random.randint(12, 19, size=total).astype(int).tolist()
    sexes = np.random.choice(["M", "F"], size=total).tolist()
    motion = np.random.normal(0.15, 0.05, size=total).round(3).tolist()
    ses = np.random.normal(0.0, 1.0, size=total).round(3).tolist()

    # Assemble the DataFrame
    df = pd.DataFrame({
        "subject_id": subject_ids,
        "group": groups,
        "years_of_training": years,
        "age": ages,
        "sex": sexes,
        "motion_score": motion,
        "ses_score": ses,
    })

    # ------------------------------------------------------------------
    # Write NIfTI files
    # ------------------------------------------------------------------
    nifti_dir = Path("data/raw/mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)

    # Determine a small set of corrupted files (~2 %)
    n_corrupt = max(1, int(0.02 * total))
    corrupt_idx = np.random.choice(total, n_corrupt, replace=False)

    for i, sid in enumerate(subject_ids):
        out_path = nifti_dir / f"{sid}.nii"
        if i in corrupt_idx:
            # Create an intentionally corrupted file
            create_corrupted_nifti(str(out_path))
            log.info(f"Created corrupted NIfTI for subject {sid}")
        else:
            # Create a valid mock NIfTI (small 10×10×10×1 image)
            create_mock_nifti(
                str(out_path),
                shape=(10, 10, 10, 1),
                seed=seed + i,
            )
            log.info(f"Created mock NIfTI for subject {sid}")

    # Add path column required by later stages
    df["rs_fmri_path"] = [str(nifti_dir / f"{sid}.nii") for sid in subject_ids]

    # ------------------------------------------------------------------
    # Write behavioural table as Parquet (the format required by downstream code)
    # ------------------------------------------------------------------
    subjects_path = Path("data/processed/subjects.parquet")
    subjects_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(subjects_path, index=False)

    log.info(f"Synthetic dataset written: {subjects_path} ({len(df)} rows)")
    log.info(f"Mock NIfTI directory contains {len(list(nifti_dir.iterdir()))} files")
    return df
