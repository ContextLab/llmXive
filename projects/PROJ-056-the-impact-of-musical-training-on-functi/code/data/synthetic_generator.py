"""
Synthetic data generator for verification mode.
Implements the API expected by the unit tests:
  - generate_subject_data
  - generate_connectivity_data
  - save_synthetic_data
and provides the constant MIN_SUBJECTS_PER_GROUP.
All generated data are fully reproducible given a seed and respect the
schema constraints defined in the contract files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

from utils.memory_monitor import MemoryLimitExceeded

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
MIN_SUBJECTS_PER_GROUP: int = 50
"""Minimum number of subjects required per group (musician / non‑musician)."""

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
# Public API
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
    * Non‑musicians receive exactly ``0`` years of training.
    * ``sex`` is encoded as ``0`` (female) or ``1`` (male) to satisfy the
      unit‑test expectation.
    * Age is limited to the adolescent range 10‑18 years.
    * Motion scores are drawn from a uniform [0, 1] interval.
    * SES scores are drawn from a uniform [1, 10] interval.
    """
    if n_subjects < 2 * MIN_SUBJECTS_PER_GROUP:
        raise ValueError("Insufficient subjects: total must allow at least "
                         f"{MIN_SUBJECTS_PER_GROUP} per group.")

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

    save_synthetic_data(args.output_dir, n_subjects=args.n_subjects, seed=args.seed)
    print(f"Synthetic data written to {args.output_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(_cli())