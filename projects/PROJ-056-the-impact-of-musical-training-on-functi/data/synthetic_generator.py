"""
Synthetic data generator used by both the CLI wrapper and the verification pipeline.

Generates a behavioural table (saved as Parquet) and a set of mock NIfTI files
(one per subject) under ``data/raw/mock_nifti``.
"""

import numpy as np
import pandas as pd
from pathlib import Path

from utils.logging import get_logger
from data.mock_nifti import create_mock_nifti

log = get_logger(__name__)

def generate_synthetic_dataset(n_subjects: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Create a synthetic behavioural dataframe and write artefacts.

    Parameters
    ----------
    n_subjects : int
        Desired total number of subjects (will be rounded to an even number).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        The generated behavioural table.
    """
    # Ensure an even, balanced cohort
    per_group = max(1, n_subjects // 2)
    total = per_group * 2
    np.random.seed(seed)

    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)
    years_of_training = (
        np.random.randint(1, 11, size=per_group).tolist() +  # musicians ≥1 yr
        [0] * per_group                                      # non‑musicians 0 yr
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

    # Write behavioural table as Parquet (requires pyarrow)
    subjects_path = Path("data/processed/subjects.parquet")
    subjects_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(subjects_path, index=False)
    log.info(f"Wrote synthetic subjects table to {subjects_path}")

    # Create mock NIfTI files
    nifti_dir = Path("data/raw/mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)
    for sid in subject_ids:
        nifti_path = nifti_dir / f"{sid}.nii.gz"
        create_mock_nifti(str(nifti_path), shape=(10, 10, 10, 1), seed=seed)
    log.info(f"Created {len(subject_ids)} mock NIfTI files in {nifti_dir}")

    return df
