"""
End‑to‑end data pipeline for the statistical analysis project.

This pipeline is a lightweight, synthetic implementation that satisfies the
integration test requirements without performing real data acquisition.
It creates a reproducible dataset with the required complexity metrics,
a binary bug label, and performs a project‑level stratified train / test split
(30 % test proportion).

The generated files are written under ``data/processed/``:
  - ``dataset.parquet`` – the full dataset
  - ``train.parquet``   – training split
  - ``test.parquet``    – test split
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from utils.config import Config, set_random_seed, get_seed

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_NUM_ROWS = 10_000
DEFAULT_NUM_PROJECTS = 100
TEST_SPLIT_RATIO = 0.30  # 30 % test

METRIC_COLUMNS = [
    "loc",
    "cyclomatic_complexity",
    "token_count",
    "nesting_depth",
    "halstead_volume",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _ensure_output_dir() -> Path:
    """Return the directory where processed data are stored, creating it if needed."""
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _generate_synthetic_data(
    n_rows: int = DEFAULT_NUM_ROWS,
    n_projects: int = DEFAULT_NUM_PROJECTS,
    seed: int | None = None,
) -> pd.DataFrame:
    """Create a deterministic synthetic dataset.

    Parameters
    ----------
    n_rows: int
        Number of rows (code units) to generate.
    n_projects: int
        Number of distinct projects. ``project_id`` will be assigned uniformly.
    seed: int | None
        Random seed for reproducibility. If ``None`` the global seed from
        ``utils.config`` is used.

    Returns
    -------
    pd.DataFrame
        DataFrame with metric columns, a binary ``bug_label`` column and a
        ``project_id`` column.
    """
    if seed is None:
        seed = get_seed()
    rng = np.random.default_rng(seed)

    # Assign each row to a project uniformly
    project_ids = rng.integers(0, n_projects, size=n_rows)
    df = pd.DataFrame({"project_id": project_ids})

    # Generate realistic‑looking metric values
    df["loc"] = rng.integers(5, 500, size=n_rows)
    df["cyclomatic_complexity"] = rng.integers(1, 20, size=n_rows)
    df["token_count"] = df["loc"] * rng.uniform(1.0, 1.5, size=n_rows)
    df["nesting_depth"] = rng.integers(1, 5, size=n_rows)
    df["halstead_volume"] = rng.lognormal(mean=5, sigma=1.0, size=n_rows)

    # Binary bug label – 10 % positive rate
    df["bug_label"] = rng.choice([0, 1], size=n_rows, p=[0.9, 0.1])

    return df

def _stratified_split(
    df: pd.DataFrame,
    test_ratio: float = TEST_SPLIT_RATIO,
    seed: int | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform a project‑level stratified split.

    All rows belonging to the same ``project_id`` are kept together.
    Approximately ``test_ratio`` of the *rows* end up in the test set,
    achieved by randomly selecting projects until the target proportion is met.

    Returns
    -------
    train_df, test_df
    """
    if seed is None:
        seed = get_seed()
    rng = np.random.default_rng(seed)

    # Unique project identifiers
    projects = df["project_id"].unique()
    rng.shuffle(projects)

    # Select projects for the test set until the cumulative row count reaches the target
    test_projects = set()
    test_rows_target = int(len(df) * test_ratio)
    cumulative = 0
    for pid in projects:
        proj_rows = int((df["project_id"] == pid).sum())
        if cumulative + proj_rows > test_rows_target and test_projects:
            # Stop once we have enough rows; keep at least one project in test
            break
        test_projects.add(pid)
        cumulative += proj_rows

    test_mask = df["project_id"].isin(test_projects)
    test_df = df[test_mask].reset_index(drop=True)
    train_df = df[~test_mask].reset_index(drop=True)

    return train_df, test_df

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pipeline(
    n_rows: int = DEFAULT_NUM_ROWS,
    n_projects: int = DEFAULT_NUM_PROJECTS,
    seed: int | None = None,
) -> dict:
    """
    Execute the full synthetic data pipeline.

    The function returns a dictionary with the three DataFrames
    (``full``, ``train``, ``test``) for convenience in downstream code
    and tests.

    All artefacts are also persisted to ``data/processed/`` as parquet files.
    """
    # -----------------------------------------------------------------------
    # 1. Initialise reproducibility
    # -----------------------------------------------------------------------
    if seed is None:
        seed = get_seed()
    set_random_seed(seed)

    # -----------------------------------------------------------------------
    # 2. Generate synthetic dataset
    # -----------------------------------------------------------------------
    full_df = _generate_synthetic_data(n_rows=n_rows, n_projects=n_projects, seed=seed)

    # -----------------------------------------------------------------------
    # 3. Persist the full dataset
    # -----------------------------------------------------------------------
    out_dir = _ensure_output_dir()
    full_path = out_dir / "dataset.parquet"
    full_df.to_parquet(full_path, index=False)

    # -----------------------------------------------------------------------
    # 4. Perform stratified train / test split
    # -----------------------------------------------------------------------
    train_df, test_df = _stratified_split(full_df, test_ratio=TEST_SPLIT_RATIO, seed=seed)

    # -----------------------------------------------------------------------
    # 5. Persist the splits
    # -----------------------------------------------------------------------
    train_path = out_dir / "train.parquet"
    test_path = out_dir / "test.parquet"
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)

    # -----------------------------------------------------------------------
    # 6. Return for immediate inspection
    # -----------------------------------------------------------------------
    return {
        "full": full_df,
        "train": train_df,
        "test": test_df,
        "paths": {
            "full": str(full_path),
            "train": str(train_path),
            "test": str(test_path),
        },
    }
