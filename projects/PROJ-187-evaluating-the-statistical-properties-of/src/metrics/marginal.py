from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

log = logging.getLogger(__name__)

def detect_column_types(
    df: pd.DataFrame,
    continuous_cols: Optional[Sequence[str]] = None,
    categorical_cols: Optional[Sequence[str]] = None,
) -> Tuple[List[str], List[str]]:
    """Split columns into continuous and categorical."""
    if continuous_cols is not None and categorical_cols is not None:
        return list(continuous_cols), list(categorical_cols)

    continuous = []
    categorical = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continuous.append(col)
        else:
            categorical.append(col)
    return continuous, categorical

def kde_estimate(values: np.ndarray, grid_size: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """Gaussian-KDE PDF estimate."""
    kde = stats.gaussian_kde(values)
    grid = np.linspace(values.min(), values.max(), grid_size)
    return grid, kde(grid)

def ks_test(real_col: pd.Series, synth_col: pd.Series) -> Tuple[float, float]:
    """Two‑sample Kolmogorov‑Smirnov test."""
    stat, p = stats.ks_2samp(real_col, synth_col)
    return stat, p

def chi_square_test(real_col: pd.Series, synth_col: pd.Series) -> Tuple[float, float]:
    """Chi‑square goodness‑of‑fit test."""
    real_counts = real_col.value_counts().sort_index()
    synth_counts = synth_col.value_counts().reindex(real_counts.index, fill_value=0)
    # Add a small floor to avoid zero expected counts.
    expected = real_counts * (len(synth_col) / len(real_col))
    expected = expected.clip(lower=1e-6)
    chi2, p = stats.chisquare(f_obs=synth_counts, f_exp=expected)
    return chi2, p

def _safe_var(values: np.ndarray) -> float:
    """Return variance, handling empty arrays."""
    return np.var(values) if values.size > 0 else float("nan")

def compute_marginal_metrics(
    real_df: pd.DataFrame,
    synth_df: pd.DataFrame,
    continuous_cols: Optional[Sequence[str]] = None,
    categorical_cols: Optional[Sequence[str]] = None,
    kde_grid_size: int = 100,
) -> List[Dict]:
    """Compute marginal fidelity metrics."""
    cont, cat = detect_column_types(real_df, continuous_cols, categorical_cols)
    rows = []
    for col in cont:
        real_series = real_df[col]
        synth_series = synth_df[col]
        zero_var = _safe_var(real_series.values) == 0 and _safe_var(synth_series.values) > 0
        ks_stat, ks_p = ks_test(real_series, synth_series) if not zero_var else (float("nan"), float("nan"))
        grid, pdf = kde_estimate(real_series.values, kde_grid_size)
        rows.append(
            {
                "column": col,
                "column_type": "continuous",
                "real_mean": real_series.mean(),
                "synth_mean": synth_series.mean(),
                "mean_diff": abs(real_series.mean() - synth_series.mean()),
                "real_var": real_series.var(),
                "synth_var": synth_series.var(),
                "var_diff": abs(real_series.var() - synth_series.var()),
                "ks_stat": ks_stat,
                "ks_pvalue": ks_p,
                "kde_grid": grid.tolist(),
                "kde_pdf": pdf.tolist(),
                "zero_variance_flag": zero_var,
            }
        )
    for col in cat:
        real_series = real_df[col]
        synth_series = synth_df[col]
        chi2, chi2_p = chi_square_test(real_series, synth_series)
        rows.append(
            {
                "column": col,
                "column_type": "categorical",
                "real_mean": None,
                "synth_mean": None,
                "mean_diff": None,
                "real_var": None,
                "synth_var": None,
                "var_diff": None,
                "chi2_stat": chi2,
                "chi2_pvalue": chi2_p,
            }
        )
    return rows