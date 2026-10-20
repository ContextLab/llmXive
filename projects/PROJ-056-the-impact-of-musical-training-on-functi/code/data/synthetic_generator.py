"""
Synthetic data generator for verification mode.

This module creates a deterministic synthetic behavioural table,
a set of mock NIfTI files, and a synthetic functional connectivity
matrix array. The generated files are written to the exact locations
required by downstream pipeline steps:

- ``data/processed/subjects.parquet`` – behavioural metadata
- ``data/raw/mock_nifti/<subject_id>.nii.gz`` – one mock NIfTI per subject
- ``data/processed/connectivity_matrices.npy`` – synthetic z‑transformed
  connectivity matrices (shape: [n_subjects, n_rois, n_rois])
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from utils.logging import get_logger
from data.mock_nifti import create_mock_nifti, create_corrupted_nifti

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Public API – subject table generation
# ----------------------------------------------------------------------
def generate_synthetic_dataset(
    n_subjects: int = 100,
    seed: int = 42,
    inject_effect: Optional[float] = None,
) -> pd.DataFrame:
    """
    Generate a balanced synthetic cohort and write artefacts to disk.

    Parameters
    ----------
    n_subjects : int
        Desired total number of subjects (will be rounded to an even
        number and split equally between musicians and non‑musicians).
    seed : int
        Random seed for reproducibility.
    inject_effect : float, optional
        Placeholder for future effect‑size injection (e.g. d=0.4). Currently
        not used; the flag is accepted to satisfy the CLI contract.

    Returns
    -------
    pd.DataFrame
        The behavioural table that is also saved as a Parquet file.
    """
    np.random.seed(seed)

    # Ensure an even split and a minimum of 50 per group
    per_group = max(50, n_subjects // 2)
    total = per_group * 2
    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]

    # Balanced group assignment
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)

    # Years of training – musicians get Uniform(1,10), non‑musicians get 0
    years = (
        np.random.uniform(1.0, 10.0, size=per_group).astype(float).tolist()
        + [0.0] * per_group
    )

    # Inject missing years_of_training (≈5 %)
    n_missing = max(1, int(0.05 * total))
    missing_idx = np.random.choice(total, n_missing, replace=False)
    for idx in missing_idx:
        years[idx] = np.nan

    # Demographic / confound columns
    ages = np.random.normal(15.0, 1.0, size=total).round().astype(int).tolist()
    sexes = np.random.choice(["M", "F"], size=total).tolist()
    motion = np.random.normal(0.15, 0.05, size=total).round(3).tolist()
    ses = np.random.normal(0.0, 1.0, size=total).round(3).tolist()

    # Assemble the DataFrame
    df = pd.DataFrame(
        {
            "subject_id": subject_ids,
            "group": groups,
            "years_of_training": years,
            "age": ages,
            "sex": sexes,
            "motion_score": motion,
            "ses_score": ses,
        }
    )

    # ------------------------------------------------------------------
    # Write NIfTI files
    # ------------------------------------------------------------------
    nifti_dir = Path("data/raw/mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)

    # Determine corrupted files (~3 %)
    n_corrupt = max(1, int(0.03 * total))
    corrupt_idx = np.random.choice(total, n_corrupt, replace=False)

    for i, sid in enumerate(subject_ids):
        out_path = nifti_dir / f"{sid}.nii.gz"
        if i in corrupt_idx:
            # Create an intentionally corrupted file
            create_corrupted_nifti(str(out_path))
            log.info(f"Created corrupted NIfTI for subject {sid}")
        else:
            # Create a valid mock NIfTI (64×64×64×1 image)
            create_mock_nifti(
                str(out_path),
                shape=(64, 64, 64, 1),
                seed=seed + i,
            )
            log.info(f"Created mock NIfTI for subject {sid}")

    # Add path column required by later stages
    df["rs_fmri_path"] = [str(nifti_dir / f"{sid}.nii.gz") for sid in subject_ids]

    # ------------------------------------------------------------------
    # Write behavioural table as Parquet (the format required by downstream code)
    # ------------------------------------------------------------------
    subjects_path = Path("data/processed/subjects.parquet")
    subjects_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(subjects_path, index=False)

    log.info(
        f"Synthetic dataset written: {subjects_path} ({len(df)} rows)"
    )
    log.info(
        f"Mock NIfTI directory contains {len(list(nifti_dir.iterdir()))} files"
    )
    return df

# ----------------------------------------------------------------------
# Public API – connectivity matrix generation
# ----------------------------------------------------------------------
def generate_connectivity_data(
    subjects_df: pd.DataFrame,
    n_timepoints: int = 200,
    n_rois: int = 200,
) -> np.ndarray:
    """
    Generate synthetic functional connectivity matrices for the synthetic cohort.

    For each subject we simulate a random Gaussian time‑series of shape
    ``(n_timepoints, n_rois)`` and compute a Pearson correlation matrix.
    The correlation matrix is Fisher‑z transformed and stored as a
    symmetric ``(n_rois, n_rois)`` array. All subject matrices are stacked
    into a single ``(n_subjects, n_rois, n_rois)`` array and written to
    ``data/processed/connectivity_matrices.npy``.

    Parameters
    ----------
    subjects_df : pd.DataFrame
        The behavioural table returned by :func:`generate_synthetic_dataset`.
        Only its length (number of subjects) is used.
    n_timepoints : int, optional
        Number of simulated time‑points per subject.
    n_rois : int, optional
        Number of ROIs in the synthetic atlas.

    Returns
    -------
    np.ndarray
        3‑D array of Fisher‑z transformed connectivity matrices.
    """
    import numpy as np
    from analysis.connectivity import fisher_z_transform, compute_pearson_correlation_chunked

    n_subjects = subjects_df.shape[0]
    log.info(
        f"Generating synthetic connectivity data: {n_subjects} subjects, "
        f"{n_timepoints} timepoints, {n_rois} ROIs"
    )

    # Pre‑allocate the output array
    all_matrices = np.empty((n_subjects, n_rois, n_rois), dtype=np.float32)

    for idx in range(n_subjects):
        # Simulate a Gaussian time‑series
        ts = np.random.randn(n_timepoints, n_rois).astype(np.float32)

        # Compute correlation matrix with memory‑friendly chunking
        corr = compute_pearson_correlation_chunked(ts, chunk_size=50)

        # Fisher‑z transform
        z_mat = fisher_z_transform(corr)

        # Ensure symmetry and zero diagonal (numerical safety)
        np.fill_diagonal(z_mat, 0.0)
        z_mat = (z_mat + z_mat.T) / 2.0

        all_matrices[idx] = z_mat

    # Write to disk
    out_path = Path("data/processed/connectivity_matrices.npy")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, all_matrices)

    log.info(f"Synthetic connectivity matrices saved to {out_path}")
    return all_matrices

# ----------------------------------------------------------------------
# Compatibility wrapper used by the test suite
# ----------------------------------------------------------------------
def generate_subject_data(n_subjects: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Compatibility wrapper used by the test suite.

    The original test suite expects a function called ``generate_subject_data``
    that returns a DataFrame with the synthetic subject metadata. Internally
    we delegate to :func:`generate_synthetic_dataset`, which already creates
    the required artefacts on disk. The wrapper simply returns the DataFrame
    (the same object that ``generate_synthetic_dataset`` returns) so that
    callers can inspect the columns, e.g. to verify that every musician has
    ``years_of_training >= 1``.
    """
    return generate_synthetic_dataset(n_subjects=n_subjects, seed=seed)