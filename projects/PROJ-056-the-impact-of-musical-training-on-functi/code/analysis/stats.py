"""
Statistical analysis utilities for the synthetic verification pipeline.

This module provides a single public function ``process_connectivity_statistics``
that takes a 3‑D NumPy array of Fisher‑z transformed connectivity matrices
(shape: N_subjects × N_ROIs × N_ROIs) and returns a ``pandas.DataFrame``
containing edge‑wise Welch's t‑tests, p‑values, BH‑FDR corrected q‑values,
Cohen's d effect sizes and 95 % confidence intervals.

The function reads the cleaned subject table written by the preprocessing
step (``data/processed/subjects_cleaned.csv``) to obtain group labels.
All calculations are performed on the CPU and respect the 7 GB memory
ceiling via the ``utils.memory_monitor`` helper.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from utils.memory_monitor import check_memory_limit, MemoryLimitExceeded
from utils.logging import get_logger

logger = get_logger(__name__)

def _upper_tri_indices(n_rois: int) -> Tuple[np.ndarray, np.ndarray]:
    """Return row, col indices for the upper triangular (excluding diagonal)."""
    rows, cols = np.triu_indices(n_rois, k=1)
    return rows, cols

def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cohen's d for two independent samples."""
    n1, n2 = len(group1), len(group2)
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_sd = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return 0.0
    return (np.mean(group1) - np.mean(group2)) / pooled_sd

def _ci_for_d(d: float, n1: int, n2: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Approximate 95 % CI for Cohen's d using the non‑central t distribution."""
    # Using standard error approximation for d
    se = np.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2)))
    z = stats.norm.ppf(1 - alpha / 2)
    return d - z * se, d + z * se

def process_connectivity_statistics(matrices: np.ndarray) -> pd.DataFrame:
    """
    Perform edge‑wise Welch's t‑test between musician and non‑musician groups.

    Parameters
    ----------
    matrices : np.ndarray
        Shape ``(N_subjects, N_ROIs, N_ROIs)`` containing Fisher‑z matrices.

    Returns
    -------
    pd.DataFrame
        Columns:
            - connection_id (e.g., ``12-34``)
            - t_stat
            - p_value
            - q_value (BH‑FDR corrected)
            - effect_size (Cohen's d)
            - ci_lower
            - ci_upper
    """
    # Load group labels
    cleaned_path = Path("data/processed/subjects_cleaned.csv")
    if not cleaned_path.is_file():
        raise FileNotFoundError(f"Cleaned subjects CSV not found at {cleaned_path}")

    subjects_df = pd.read_csv(cleaned_path)
    if "group" not in subjects_df.columns:
        raise KeyError("Column 'group' missing from cleaned subjects CSV")

    # Ensure order matches matrices (the synthetic pipeline writes matrices in the
    # same order as the cleaned CSV, because it iterates over the cleaned dataframe).
    groups = subjects_df["group"].values
    musician_mask = groups == "musician"
    non_musician_mask = groups == "non_musician"

    if musician_mask.sum() == 0 or non_musician_mask.sum() == 0:
        raise ValueError("Both groups must contain at least one subject for statistical testing")

    n_rois = matrices.shape[1]
    rows, cols = _upper_tri_indices(n_rois)

    # Prepare containers
    t_stats = []
    p_vals = []
    effect_sizes = []

    # Iterate over edges
    for r, c in zip(rows, cols):
        edge_vals = matrices[:, r, c]
        mus = edge_vals[musician_mask]
        non = edge_vals[non_musician_mask]

        # Welch's t-test
        t, p = stats.ttest_ind(mus, non, equal_var=False)
        t_stats.append(t)
        p_vals.append(p)

        # Cohen's d
        d = _cohens_d(mus, non)
        effect_sizes.append(d)

    # Multiple‑testing correction
    _, q_vals, _, _ = multipletests(p_vals, method="fdr_bh")

    # Confidence intervals for effect size
    ci_lowers = []
    ci_uppers = []
    n1 = musician_mask.sum()
    n2 = non_musician_mask.sum()
    for d in effect_sizes:
        lower, upper = _ci_for_d(d, n1, n2)
        ci_lowers.append(lower)
        ci_uppers.append(upper)

    # Build DataFrame
    conn_ids = [f"{r}-{c}" for r, c in zip(rows, cols)]
    results_df = pd.DataFrame({
        "connection_id": conn_ids,
        "t_stat": t_stats,
        "p_value": p_vals,
        "q_value": q_vals,
        "effect_size": effect_sizes,
        "ci_lower": ci_lowers,
        "ci_upper": ci_uppers,
    })

    # Ensure memory limit is still respected
    check_memory_limit()

    logger.info(f"Statistical analysis produced {len(results_df)} edge results.")
    return results_df
