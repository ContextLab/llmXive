"""
Synthetic data generator for verification mode.
Implements the API expected by the unit tests:
  - generate_subject_data
  - generate_connectivity_data
  - save_synthetic_data
and provides additional helpers required by the rest of the pipeline:
  - generate_synthetic_dataset (creates NIfTI files and a Parquet behavioural table)
All generated data are fully reproducible given a seed and respect the
schema constraints defined in ``contracts/subject.schema.yaml``.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

from utils.memory_monitor import MemoryLimitExceeded
from llmxive_toolkit import paths, get_logger
from data.mock_nifti import create_mock_nifti, create_corrupted_nifti

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
MIN_SUBJECTS_PER_GROUP: int = 50
"""Minimum number of subjects required per group (musician / non‑musician)."""

# Proportion of non‑musician subjects that will have missing training history
MISSING_TRAINING_RATE: float = 0.05  # 5 %

# Proportion of subjects that will receive a corrupted NIfTI file
CORRUPTED_NIFTI_RATE: float = 0.05  # 5 %

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _validate_subject_counts(df: pd.DataFrame) -> None:
    """Raise a ValueError if either group does not meet the minimum size."""
    musician_cnt = (df["group"] == "musician").sum()
    non_musician_cnt = (df["group"] == "non_musician").sum()
    if musician_cnt < MIN_SUBJECTS_PER_GROUP or non_musician_cnt < MIN_SUBJECTS_PER_GROUP:
        raise ValueError(
            f"Insufficient subjects: musician={musician_cnt}, non_musician={non_musician_cnt}"
        )

# ----------------------------------------------------------------------
# Public API required by the unit tests
# ----------------------------------------------------------------------
def generate_subject_data(
    n_subjects: int,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Generate a synthetic subject table.

    Parameters
    ----------
    n_subjects : int
        Total number of subjects to generate. Must be at least
        ``2 * MIN_SUBJECTS_PER_GROUP``; otherwise a ``ValueError`` is raised.
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Columns: subject_id, group, years_of_training, age, sex,
        motion_score, ses_score

    Notes
    -----
    * Musicians receive ``years_of_training >= 1`` (uniform 1‑15 years).
    * Non‑musicians receive exactly ``0`` years of training, but a small
      seeded subset will have missing values (NaN) to test exclusion handling.
    * ``sex`` is encoded as ``0`` (female) or ``1`` (male) to satisfy the
      unit‑test expectation.
    * Age is limited to the adolescent range 10‑18 years.
    * Motion scores are drawn from a uniform [0, 1] interval.
    * SES scores are drawn from a uniform [1, 10] interval.
    """
    if n_subjects < 2 * MIN_SUBJECTS_PER_GROUP:
        raise ValueError(
            "Insufficient subjects: total must allow at least "
            f"{MIN_SUBJECTS_PER_GROUP} per group."
        )

    if seed is not None:
        np.random.seed(seed)

    # Balanced groups
    n_musician = n_subjects // 2
    n_non_musician = n_subjects - n_musician

    subject_ids = [f"SUBJ-{i:04d}" for i in range(n_subjects)]
    groups = ["musician"] * n_musician + ["non_musician"] * n_non_musician

    # Years of training
    years_of_training = []
    for g in groups:
        if g == "musician":
            years_of_training.append(np.random.uniform(1.0, 15.0))
        else:
            years_of_training.append(0.0)  # strict NULL‑FIRST for non‑musicians

    # Demographics
    ages = np.random.uniform(10, 18, size=n_subjects)
    sexes = np.random.choice([0, 1], size=n_subjects)  # 0 = female, 1 = male
    motion_scores = np.random.uniform(0.0, 1.0, size=n_subjects)
    ses_scores = np.random.uniform(1.0, 10.0, size=n_subjects)

    df = pd.DataFrame(
        {
            "subject_id": subject_ids,
            "group": groups,
            "years_of_training": years_of_training,
            "age": ages,
            "sex": sexes,
            "motion_score": motion_scores,
            "ses_score": ses_scores,
        }
    )

    # Inject missing training history for a small fraction of non‑musicians
    if seed is not None:
        np.random.seed(seed + 999)  # deterministic offset
    non_musician_mask = df["group"] == "non_musician"
    non_musician_indices = df[non_musician_mask].index.to_numpy()
    n_missing = int(len(non_musician_indices) * MISSING_TRAINING_RATE)
    if n_missing > 0:
        missing_idxs = np.random.choice(non_musician_indices, size=n_missing, replace=False)
        df.loc[missing_idxs, "years_of_training"] = np.nan
        log.info(f"Injected missing training history for {n_missing} non‑musician subjects.")

    # Final validation – ensure group balance
    _validate_subject_counts(df)

    return df

def generate_connectivity_data(
    subject_df: pd.DataFrame,
    n_rois: int = 20,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Generate synthetic functional connectivity data for a set of subjects.

    Each subject receives a random time‑series matrix (n_timepoints × n_rois)
    which is converted to a Pearson correlation matrix.  The upper‑triangle
    (excluding the diagonal) is flattened into long‑format rows.

    Parameters
    ----------
    subject_df : pd.DataFrame
        Output of ``generate_subject_data``; must contain a ``subject_id`` column.
    n_rois : int
        Number of ROIs (parcels) for which to simulate time‑series.
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Columns: ``subject_id``, ``roi_i``, ``roi_j``, ``correlation``.
    """
    if seed is not None:
        np.random.seed(seed)

    if "subject_id" not in subject_df.columns:
        raise ValueError("subject_df must contain a 'subject_id' column")

    n_timepoints = 50  # modest length sufficient for a realistic correlation estimate
    rows = []

    for subj_id in subject_df["subject_id"]:
        # Random Gaussian time‑series for each ROI
        ts = np.random.randn(n_timepoints, n_rois)
        # Pearson correlation matrix
        corr = np.corrcoef(ts, rowvar=False)
        # Ensure numerical stability
        corr = np.nan_to_num(corr, nan=0.0)

        # Extract upper triangle (i < j)
        for i in range(n_rois):
            for j in range(i + 1, n_rois):
                rows.append(
                    {
                        "subject_id": subj_id,
                        "roi_i": i,
                        "roi_j": j,
                        "correlation": float(corr[i, j]),
                    }
                )

    conn_df = pd.DataFrame(rows)
    return conn_df

def save_synthetic_data(
    output_dir: str | Path,
    n_subjects: int = 100,
    seed: int | None = None,
) -> Dict[str, str]:
    """
    Create the full synthetic data package required by the verification pipeline.

    The function writes three files into ``output_dir``:
      * ``subjects.csv`` – the behavioural table,
      * ``connectivity.csv`` – long‑format edge list,
      * ``metadata.json`` – a tiny manifest describing the generation parameters.

    Parameters
    ----------
    output_dir : str | Path
        Destination directory (will be created if missing).
    n_subjects : int
        Number of subjects to generate (default 100, which satisfies the
        MIN_SUBJECTS_PER_GROUP requirement).
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    dict
        Mapping with keys ``subjects``, ``connectivity``, ``metadata`` pointing
        to the absolute file paths of the written artefacts.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Generate behavioural table
    # ------------------------------------------------------------------
    subjects_df = generate_subject_data(n_subjects, seed=seed)

    subjects_path = out_path / "subjects.csv"
    subjects_df.to_csv(subjects_path, index=False)

    # ------------------------------------------------------------------
    # 2. Generate connectivity edge list
    # ------------------------------------------------------------------
    connectivity_df = generate_connectivity_data(subjects_df, n_rois=20, seed=seed)

    connectivity_path = out_path / "connectivity.csv"
    connectivity_df.to_csv(connectivity_path, index=False)

    # ------------------------------------------------------------------
    # 3. Write a simple JSON manifest
    # ------------------------------------------------------------------
    metadata = {
        "n_subjects": n_subjects,
        "seed": seed,
        "mode": "verification",
        "note": "NULL-FIRST synthetic dataset for pipeline verification",
    }
    metadata_path = out_path / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "subjects": str(subjects_path),
        "connectivity": str(connectivity_path),
        "metadata": str(metadata_path),
    }

# ----------------------------------------------------------------------
# Additional helper required by the rest of the pipeline
# ----------------------------------------------------------------------
def generate_synthetic_dataset(
    n_subjects: int = 100,
    n_timepoints: int = 200,
    n_rois: int = 400,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Generate a synthetic dataset that mimics the layout expected for
    verification mode throughout the pipeline.

    * Creates a behavioural table and writes it as ``data/processed/subjects.parquet``.
    * Generates a mock NIfTI file for each subject under ``data/raw/mock_nifti/``.
    * Injects a small seeded rate of missing training‑history values (non‑musicians only)
      and a small seeded rate of corrupted NIfTI files.
    * Returns the behavioural ``DataFrame`` for downstream consumption.

    Parameters
    ----------
    n_subjects : int, default 100
        Total number of subjects to generate.
    n_timepoints : int, default 200
        Number of time‑points per mock fMRI run (used only for the NIfTI shape).
    n_rois : int, default 400
        Number of ROIs – does not affect the NIfTI shape but is retained for
        consistency with downstream code that expects 400 parcels.
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Behavioural table with the required columns.
    """
    log.info(
        f"Generating synthetic dataset: subjects={n_subjects}, "
        f"timepoints={n_timepoints}, rois={n_rois}, seed={seed}"
    )

    # 1. Generate behavioural table
    subjects_df = generate_subject_data(n_subjects, seed=seed)

    # 2. Write behavioural table as Parquet (required by downstream scripts)
    subjects_parquet_path = paths.data("processed", "subjects.parquet")
    subjects_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    subjects_df.to_parquet(subjects_parquet_path, index=False)
    log.info(f"Wrote behavioural table to {subjects_parquet_path}")

    # 3. Create mock NIfTI files for each subject
    nifti_dir = paths.data("raw", "mock_nifti")
    nifti_dir.mkdir(parents=True, exist_ok=True)

    # Use a simple 4‑D shape: (10, 10, 10, n_timepoints)
    nifti_shape = (10, 10, 10, n_timepoints)

    # Determine which subjects will receive corrupted files
    if seed is not None:
        np.random.seed(seed + 555)  # deterministic offset for corruption selection
    subject_ids = subjects_df["subject_id"].tolist()
    n_corrupt = int(len(subject_ids) * CORRUPTED_NIFTI_RATE)
    corrupt_ids = set()
    if n_corrupt > 0:
        corrupt_ids = set(np.random.choice(subject_ids, size=n_corrupt, replace=False))
        log.info(f"Injecting corrupted NIfTI files for {n_corrupt} subjects.")

    for subj_id in subject_ids:
        nifti_path = nifti_dir / f"{subj_id}.nii.gz"
        if subj_id in corrupt_ids:
            # Create a deliberately corrupted file
            create_corrupted_nifti(str(nifti_path))
        else:
            # ``create_mock_nifti`` will ensure the file is a valid NIfTI‑1 image.
            create_mock_nifti(
                output_path=str(nifti_path),
                shape=nifti_shape,
                dtype=np.float32,
                seed=seed,
            )
    log.info(f"Created {len(subject_ids)} mock NIfTI files in {nifti_dir}")

    return subjects_df

# ----------------------------------------------------------------------
# Command‑line entry point (optional, useful for manual debugging)
# ----------------------------------------------------------------------
def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate synthetic verification data for the musical‑training pipeline."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory where the synthetic artefacts will be written.",
    )
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=100,
        help="Total number of synthetic subjects to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    # The CLI mirrors ``save_synthetic_data`` for backward compatibility.
    save_synthetic_data(args.output_dir, n_subjects=args.n_subjects, seed=args.seed)
    print(f"Synthetic data written to {args.output_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(_cli())
