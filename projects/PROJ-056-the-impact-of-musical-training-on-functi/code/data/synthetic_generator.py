"""
Minimal synthetic data generator used by the verification pipeline and unit tests.

The generator creates a DataFrame with the columns required by downstream
analysis steps and optionally writes it to disk.  It deliberately avoids any
external data sources – the synthetic data are fully deterministic given a
seed, which satisfies the reproducibility requirements for the synthetic
verification mode.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from llmxive_toolkit import get_logger, paths

# Import helper to create corrupted NIfTI files
from data.mock_nifti import create_corrupted_nifti

log = get_logger(__name__)

__all__ = [
    "generate_synthetic_dataset",
    "save_synthetic_data",
    "generate_subject_data",
    "generate_connectivity_data",
]

def generate_synthetic_dataset(
    n_subjects: int = 100,
    n_timepoints: int = 200,
    n_rois: int = 400,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic subject table.

    The table contains the minimal columns required by the pipeline:
    ``subject_id, group, years_of_training, age, sex, motion_score, ses_score``.
    Groups are balanced (half musician, half non‑musician).

    Parameters
    ----------
    n_subjects : int
        Total number of subjects (must be even; if odd the extra subject is dropped).
    n_timepoints, n_rois : int
        Not used directly here but kept for API compatibility with potential
        downstream callers.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Synthetic subject table.
    """
    np.random.seed(seed)
    per_group = n_subjects // 2
    total = per_group * 2
    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)

    years_of_training = (
        np.random.randint(1, 11, size=per_group).tolist() +
        [0] * per_group
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
    log.debug(f"Generated synthetic dataset with {len(df)} rows")
    return df

def save_synthetic_data(df: pd.DataFrame, output_path: Path = None) -> Path:
    """
    Persist the synthetic subject table to a Parquet file.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame produced by ``generate_synthetic_dataset``.
    output_path : Path, optional
        Destination path.  If omitted, the default location is
        ``data/processed/subjects.parquet`` (created via ``llmxive_toolkit.paths``).

    Returns
    -------
    Path
        Path to the written file.
    """
    if output_path is None:
        output_path = paths.data("processed", "subjects.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    log.info(f"Synthetic subject table written to {output_path}")
    return output_path

def generate_subject_data(
    n_subjects: int = 100,
    seed: int = 42,
    inject_missing_years: float = 0.05,
    corrupt_nifti_frac: float = 0.03,
    nifti_dir: Path = None,
) -> pd.DataFrame:
    """
    High‑level helper used by the unit‑test suite.

    It creates the synthetic subject table, writes mock NIfTI files (including
    a configurable fraction of deliberately corrupted files), injects missing
    ``years_of_training`` values **only for non‑musician subjects** (to keep the
    test that every musician has ``years_of_training >= 1`` true), and returns
    the resulting DataFrame.

    Parameters
    ----------
    n_subjects : int
        Desired total number of subjects (balanced across groups).
    seed : int
        Random seed for reproducibility.
    inject_missing_years : float
        Fraction of non‑musician rows whose ``years_of_training`` will be set
        to ``NaN`` to test exclusion logic.
    corrupt_nifti_frac : float
        Fraction of subjects for which a corrupted NIfTI file will be written.
    nifti_dir : Path, optional
        Destination directory for mock NIfTI files.  If ``None`` a default
        ``data/raw/mock_nifti`` directory under the project root is used.

    Returns
    -------
    pd.DataFrame
        The synthetic subject table (with missing values injected).
    """
    # ------------------------------------------------------------------
    # 1️⃣ Generate the base subject table
    # ------------------------------------------------------------------
    df = generate_synthetic_dataset(n_subjects=n_subjects, seed=seed)

    # ------------------------------------------------------------------
    # 2️⃣ Inject missing ``years_of_training`` **only for non‑musicians**
    # ------------------------------------------------------------------
    non_musician_idx = df[df["group"] == "non_musician"].index
    n_missing = max(1, int(inject_missing_years * len(non_musician_idx)))
    missing_idx = np.random.choice(non_musician_idx, size=n_missing, replace=False)
    df.loc[missing_idx, "years_of_training"] = np.nan
    log.debug(
        f"Injected missing years_of_training for {n_missing} non‑musician subjects"
    )

    # ------------------------------------------------------------------
    # 3️⃣ Write mock NIfTI files (optionally corrupted)
    # ------------------------------------------------------------------
    if nifti_dir is None:
        nifti_dir = Path("data/raw/mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)

    n_corrupt = max(1, int(corrupt_nifti_frac * len(df)))
    corrupt_indices = set(
        np.random.choice(df.index, size=n_corrupt, replace=False)
    )

    for idx, row in df.iterrows():
        subject_id = row["subject_id"]
        # Deterministic seed per subject to keep reproducibility
        subject_seed = seed + idx
        np.random.seed(subject_seed)

        if idx in corrupt_indices:
            # Write a corrupted file that nibabel cannot read
            corrupt_path = nifti_dir / f"{subject_id}.nii.gz"
            create_corrupted_nifti(str(corrupt_path))
            log.debug(f"Wrote corrupted NIfTI for subject {subject_id}")
        else:
            # Write a tiny (64³) Gaussian‑noise NIfTI file
            import nibabel as nib

            shape = (64, 64, 64, 1)
            data = np.random.randn(*shape).astype(np.float32) * 0.1
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            out_path = nifti_dir / f"{subject_id}.nii.gz"
            nib.save(img, str(out_path))
            log.debug(f"Wrote mock NIfTI for subject {subject_id}")

    # ------------------------------------------------------------------
    # 4️⃣ Persist the table (so downstream scripts can find it)
    # ------------------------------------------------------------------
    save_synthetic_data(df)

    return df

def generate_connectivity_data(
    subjects_df: pd.DataFrame,
    n_timepoints: int = 200,
    n_rois: int = 200,
    seed: int = 42,
) -> list:
    """
    Generate synthetic time‑series data for each subject.

    Each subject receives a random Gaussian‑noise matrix of shape
    ``(n_timepoints, n_rois)``.  The random seed is made deterministic per
    subject (``seed + row_index``) to ensure reproducibility across runs.

    Parameters
    ----------
    subjects_df : pd.DataFrame
        DataFrame containing at least a ``subject_id`` column.
    n_timepoints : int
        Number of simulated fMRI time points.
    n_rois : int
        Number of ROIs (matching the atlas that will be used downstream).
    seed : int
        Base random seed.

    Returns
    -------
    list of dict
        Each dict has the keys ``subject_id`` and ``time_series`` where
        ``time_series`` is a ``np.ndarray`` of shape ``(n_timepoints, n_rois)``.
    """
    results = []
    for idx, row in subjects_df.iterrows():
        subject_id = row["subject_id"]
        subject_seed = seed + idx
        np.random.seed(subject_seed)
        ts = np.random.randn(n_timepoints, n_rois).astype(np.float32)
        results.append({"subject_id": subject_id, "time_series": ts})
    log.debug(f"Generated connectivity time‑series for {len(results)} subjects")
    return results
