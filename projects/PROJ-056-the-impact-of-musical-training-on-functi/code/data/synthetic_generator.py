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

log = get_logger(__name__)

__all__ = ["generate_synthetic_dataset", "save_synthetic_data"]

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
