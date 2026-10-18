"""Marginal fidelity metrics: mean, variance, KS, chi-square, KDE (FR-004, FR-005, FR-011, FR-014)."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

log = logging.getLogger(__name__)

ZERO_VARIANCE_FLAG = "zero_variance_synthetic"


def detect_column_types(
    df: pd.DataFrame,
    continuous_cols: Optional[Sequence[str]] = None,
    categorical_cols: Optional[Sequence[str]] = None,
) -> Tuple[List[str], List[str]]:
    """Split columns into continuous and categorical.

    Explicit lists win; otherwise a column is categorical when its dtype is
    object/bool/category or it has few unique non-null values (<= 10) relative
    to its size.
    """
    if continuous_cols is not None and categorical_cols is not None:
        return list(continuous_cols), list(categorical_cols)
    cont: List[str] = []
    cat: List[str] = []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            nuniq = s.nunique(dropna=True)
            if nuniq > 10:
                cont.append(col)
            else:
                cat.append(col)
        else:
            cat.append(col)
    return cont, cat


def kde_estimate(
    values: np.ndarray, grid_size: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """Gaussian-KDE PDF estimate on a regular grid over the data range (FR-014)."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2 or np.all(values == values[0]):
        # Degenerate: a single spike of density 1 at the constant value.
        point = values[0] if values.size else 0.0
        return np.array([point]), np.array([1.0])
    kde = stats.gaussian_kde(values)
    lo, hi = float(values.min()), float(values.max())
    if lo == hi:
        return np.array([lo]), np.array([1.0])
    pad = 0.05 * (hi - lo)
    grid = np.linspace(lo - pad, hi + pad, grid_size)
    return grid, kde(grid)


def ks_test(real_col: pd.Series, synth_col: pd.Series) -> Tuple[float, float]:
    """Two-sample Kolmogorov-Smirnov statistic and p-value (continuous columns)."""
    r = np.asarray(real_col, dtype=float)
    s = np.asarray(synth_col, dtype=float)
    r = r[np.isfinite(r)]
    s = s[np.isfinite(s)]
    if r.size == 0 or s.size == 0:
        raise ValueError("KS test requires non-empty real and synthetic samples")
    result = stats.ks_2samp(r, s)
    return float(result.statistic), float(result.pvalue)


def chi_square_test(real_col: pd.Series, synth_col: pd.Series) -> Tuple[float, float]:
    """Chi-square goodness-of-fit of synthetic category counts against real proportions.

    Expected counts are the real hold-out category proportions scaled to the
    synthetic sample size. Categories present only in one set are handled by
    pooling on the union and adding a small floor to expected counts so the
    test is always defined.
    """
    real_counts = real_col.value_counts()
    synth_counts = synth_col.value_counts()
    categories = sorted(set(real_counts.index) | set(synth_counts.index))
    if len(categories) < 2:
        # Single category in both: no divergence detectable.
        return 0.0, 1.0
    observed = np.array([synth_counts.get(c, 0) for c in categories], dtype=float)
    n_real = real_counts.sum()
    expected_props = np.array(
        [real_counts.get(c, 0) for c in categories], dtype=float
    ) / float(n_real)
    n_synth = observed.sum()
    expected = expected_props * n_synth
    # Floor expected counts so unseen-in-real categories don't produce zeros.
    expected = np.maximum(expected, 1e-9)
    expected = expected * (n_synth / expected.sum())
    result = stats.chisquare(f_obs=observed, f_exp=expected)
    return float(result.statistic), float(result.pvalue)


def _safe_var(values: np.ndarray) -> float:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size < 2:
        return 0.0
    return float(np.var(v, ddof=1))


def compute_marginal_metrics(
    real_df: pd.DataFrame,
    synth_df: pd.DataFrame,
    continuous_cols: Optional[Sequence[str]] = None,
    categorical_cols: Optional[Sequence[str]] = None,
    kde_grid_size: int = 100,
) -> List[Dict]:
    """Per-column marginal fidelity metrics for real hold-out vs synthetic data.

    Returns a list of row dicts with keys:
    column, column_type, real_mean, synth_mean, mean_diff, real_var, synth_var,
    var_diff, and either (ks_stat, ks_pvalue) for continuous columns or
    (chi2_stat, chi2_pvalue) for categorical columns, plus KDE grid/pdf for
    continuous columns and a zero_variance_flag (FR-011).
    """
    if continuous_cols is None or categorical_cols is None:
        c, k = detect_column_types(real_df, continuous_cols, categorical_cols)
    else:
        c, k = list(continuous_cols), list(categorical_cols)
    rows: List[Dict] = []
    for col in real_df.columns:
        if col not in synth_df.columns:
            log.warning("Column %s missing in synthetic data; skipped", col)
            continue
        real_col = real_df[col]
        synth_col = synth_df[col]
        row: Dict = {
            "column": col,
            "column_type": "continuous" if col in c else "categorical",
            "zero_variance_flag": False,
            "fidelity_failure": False,
        }
        if col in c:
            rv = np.asarray(real_col, dtype=float)
            sv = np.asarray(synth_col, dtype=float)
            real_var = _safe_var(rv)
            synth_var = _safe_var(sv)
            row["real_mean"] = float(np.nanmean(rv)) if rv.size else float("nan")
            row["synth_mean"] = float(np.nanmean(sv)) if sv.size else float("nan")
            row["mean_diff"] = abs(row["real_mean"] - row["synth_mean"])
            row["real_var"] = real_var
            row["synth_var"] = synth_var
            row["var_diff"] = abs(real_var - synth_var)
            # FR-011: zero-variance synthetic column with non-zero real variance.
            if synth_var == 0.0 and real_var > 0.0:
                row["zero_variance_flag"] = True
                row["fidelity_failure"] = True
                row["ks_stat"] = None
                row["ks_pvalue"] = None
                log.warning(
                    "FR-011: synthetic column %s has zero variance while real "
                    "variance is %g; flagged as fidelity failure, KS skipped",
                    col,
                    real_var,
                )
            else:
                ks_stat, ks_p = ks_test(real_col, synth_col)
                row["ks_stat"] = ks_stat
                row["ks_pvalue"] = ks_p
                row["ks_effect_size"] = ks_stat
            grid, pdf = kde_estimate(sv, kde_grid_size)
            row["kde_grid"] = grid.tolist()
            row["kde_pdf"] = pdf.tolist()
        else:
            row["real_mean"] = None
            row["synth_mean"] = None
            row["mean_diff"] = None
            row["real_var"] = None
            row["synth_var"] = None
            row["var_diff"] = None
            chi2_stat, chi2_p = chi_square_test(real_col, synth_col)
            row["chi2_stat"] = chi2_stat
            row["chi2_pvalue"] = chi2_p
            row["chi2_effect_size"] = chi2_stat
        rows.append(row)
    return rows