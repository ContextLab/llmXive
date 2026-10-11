"""
Statistical utilities for the Neural Entropy and Cognitive Flexibility project.

Provides:
* OLS (ordinary least squares) regression wrappers around statsmodels,
  including partial-correlation-style effect sizes derived from the OLS fit.
* Benjamini-Hochberg False Discovery Rate (FDR) correction.

Task T006.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm


# ---------------------------------------------------------------------------
# Benjamini-Hochberg FDR
# ---------------------------------------------------------------------------

def fdr_adjusted_pvalues(
    p_values: Union[Sequence[float], np.ndarray, pd.Series],
) -> np.ndarray:
    """
    Compute Benjamini-Hochberg FDR-adjusted p-values.

    Adjusted p_i = min over k >= rank(i) of ( n / k ) * p_(k), capped at 1,
    where p_(k) is the k-th smallest p-value.

    Parameters
    ----------
    p_values : array-like of p-values.

    Returns
    -------
    np.ndarray
        Adjusted p-values in the ORIGINAL input order.
    """
    p = np.asarray(p_values, dtype=float)
    n = p.size
    if n == 0:
        return np.array([], dtype=float)

    order = np.argsort(p, kind="mergesort")
    ranked = p[order]
    adjusted = (n / np.arange(1, n + 1)) * ranked
    # enforce monotonicity from the largest p-value downward
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)

    out = np.empty(n, dtype=float)
    out[order] = adjusted
    return out

def fdr_benjamini_hochberg(
    p_values: Union[Sequence[float], np.ndarray, pd.Series],
    alpha: float = 0.05,
) -> Union[np.ndarray, pd.Series]:
    """
    Benjamini-Hochberg FDR procedure: return a boolean rejection mask.

    Step-up algorithm: find the largest k such that p_(k) <= (k / n) * alpha,
    then reject all hypotheses with p-value <= p_(k).

    Parameters
    ----------
    p_values : array-like or pandas Series of raw p-values (any order).
    alpha : significance level (default 0.05).

    Returns
    -------
    np.ndarray (or pd.Series if a Series was passed)
        Boolean mask of the same length/order as the input; True = reject.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    is_series = isinstance(p_values, pd.Series)
    p = np.asarray(p_values, dtype=float)
    n = p.size

    if n == 0:
        mask = np.array([], dtype=bool)
        return pd.Series(mask, index=p_values.index) if is_series else mask

    if np.any(np.isnan(p)):
        raise ValueError("p_values contain NaN; clean them before FDR correction")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("p_values must lie in [0, 1]")

    order = np.argsort(p, kind="mergesort")
    sorted_p = p[order]
    critical = (np.arange(1, n + 1) / n) * alpha

    # Largest k with p_(k) <= critical_k (k is 1-based)
    below = sorted_p <= critical
    if not np.any(below):
        mask = np.zeros(n, dtype=bool)
    else:
        k = int(np.max(np.nonzero(below)[0]))  # 0-based index of largest k
        threshold = sorted_p[k]
        mask = p <= threshold

    if is_series:
        return pd.Series(mask, index=p_values.index)
    return mask


# ---------------------------------------------------------------------------
# OLS regression
# ---------------------------------------------------------------------------

def ols_regression(
    y: Union[np.ndarray, pd.Series, List[float]],
    X: Union[np.ndarray, pd.DataFrame, pd.Series, List[List[float]]],
    add_intercept: bool = True,
    feature_names: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Fit an OLS regression via statsmodels and return a summary dict.

    Parameters
    ----------
    y : dependent variable (length n).
    X : predictor matrix (n x p). A 1-D X is treated as a single predictor.
    add_intercept : whether to prepend a constant column.
    feature_names : optional names for the predictors.

    Returns
    -------
    dict with keys:
        'coefficients' (np.ndarray), 'std_errors', 't_values', 'p_values',
        'r_squared', 'adj_r_squared', 'f_pvalue', 'n_obs', 'df_resid',
        'residuals', 'fitted_values', 'model' (the statsmodels result),
        'feature_names' (list of str, excluding intercept).
    """
    y_arr = np.asarray(y, dtype=float).ravel()
    X_arr = np.asarray(X, dtype=float)
    if X_arr.ndim == 1:
        X_arr = X_arr.reshape(-1, 1)

    if X_arr.shape[0] != y_arr.size:
        raise ValueError(
            f"Shape mismatch: X has {X_arr.shape[0]} rows, y has {y_arr.size}"
        )

    valid = ~(np.isnan(y_arr) | np.isnan(X_arr).any(axis=1))
    if not np.all(valid):
        y_arr = y_arr[valid]
        X_arr = X_arr[valid]

    if y_arr.size <= X_arr.shape[1] + (1 if add_intercept else 0):
        raise ValueError("Not enough observations to fit the OLS model")

    if feature_names is None:
        if isinstance(X, pd.DataFrame):
            feature_names = list(X.columns)
        else:
            feature_names = [f"x{i + 1}" for i in range(X_arr.shape[1])]

    X_design = sm.add_constant(X_arr) if add_intercept else X_arr
    model = sm.OLS(y_arr, X_design).fit()

    coefs = np.asarray(model.params)
    offset = 1 if add_intercept else 0
    return {
        "coefficients": coefs,
        "std_errors": np.asarray(model.bse),
        "t_values": np.asarray(model.tvalues),
        "p_values": np.asarray(model.pvalues),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "f_pvalue": float(model.f_pvalue),
        "n_obs": int(model.nobs),
        "df_resid": int(model.df_resid),
        "residuals": np.asarray(model.resid),
        "fitted_values": np.asarray(model.fittedvalues),
        "model": model,
        "feature_names": list(feature_names),
    }


def ols_partial_r(
    result: Optional[Dict[str, Any]] = None,
    predictor_index: int = 1,
    y: Optional[np.ndarray] = None,
    X: Optional[np.ndarray] = None,
) -> float:
    """
    Derive a partial correlation coefficient (partial r) for a predictor
    from an OLS fit: partial_r = t * sqrt(df_resid) / sqrt(t^2 + df_resid).
    """
    if result is None:
        if y is None or X is None:
            raise ValueError("Provide either an OLS result dict or y and X")
        result = ols_regression(y, X)
    t = float(result["t_values"][predictor_index])
    df = float(result["df_resid"])
    denom = np.sqrt(t * t + df)
    if denom == 0:
        return 0.0
    return float(t * np.sqrt(df) / denom)


def run_ols_with_fdr(
    data: pd.DataFrame,
    target_col: str,
    predictor_cols: Sequence[str],
    covariate_cols: Sequence[str] = (),
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Run one OLS per predictor (controlling for covariates), then apply
    Benjamini-Hochberg FDR across the resulting p-values.

    Returns a DataFrame with columns:
    predictor, coefficient, std_error, t_value, p_raw, p_fdr, partial_r,
    r_squared, significant_fdr.
    """
    rows: List[Dict[str, Any]] = []
    for pred in predictor_cols:
        X_cols = [pred] + [c for c in covariate_cols if c != pred]
        sub = data[[target_col] + X_cols].dropna()
        if len(sub) <= len(X_cols) + 1:
            continue
        res = ols_regression(sub[target_col], sub[X_cols],
                             feature_names=X_cols)
        idx = X_cols.index(pred) + 1  # +1 for intercept
        rows.append({
            "predictor": pred,
            "coefficient": float(res["coefficients"][idx]),
            "std_error": float(res["std_errors"][idx]),
            "t_value": float(res["t_values"][idx]),
            "p_raw": float(res["p_values"][idx]),
            "partial_r": ols_partial_r(res, predictor_index=idx),
            "r_squared": res["r_squared"],
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_fdr"] = fdr_adjusted_pvalues(out["p_raw"].to_numpy())
    out["significant_fdr"] = fdr_benjamini_hochberg(
        out["p_raw"].to_numpy(), alpha=alpha
    )
    return out
