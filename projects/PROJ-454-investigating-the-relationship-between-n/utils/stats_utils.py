"""
utils.stats_utils
-----------------
Utility functions for statistical analysis used across the project.

This module provides:
- Ordinary Least Squares (OLS) regression fitting helper.
- Benjamini‑Hochberg False Discovery Rate (FDR) correction.
- Variance Inflation Factor (VIF) calculation for multicollinearity diagnostics.
- Partial correlation (partial r) extraction from an OLS model.
- Simple effect‑size classification based on partial r.

All functions are deliberately lightweight and avoid any side‑effects; they operate purely on
NumPy/Pandas/Statsmodels objects and return plain Python data structures suitable for
downstream pipelines and unit‑testing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Iterable, Union, Dict, Any

__all__ = [
    "fit_ols_model",
    "calculate_partial_r",
    "calculate_vif",
    "fdr_benjamini_hochberg",
    "classify_effect_size",
]


def fit_ols_model(
    X: Union[pd.DataFrame, np.ndarray],
    y: Union[pd.Series, np.ndarray],
    add_const: bool = True,
) -> sm.regression.linear_model.RegressionResultsWrapper:
    """
    Fit an OLS regression model.

    Parameters
    ----------
    X : DataFrame or ndarray
        Predictor variables.
    y : Series or ndarray
        Dependent variable.
    add_const : bool, default True
        Whether to prepend an intercept column.

    Returns
    -------
    RegressionResultsWrapper
        The fitted Statsmodels OLS result object.
    """
    if isinstance(X, pd.DataFrame):
        X_used = X.copy()
    else:
        X_used = pd.DataFrame(X)

    if add_const:
        X_used = sm.add_constant(X_used, has_constant="add")

    model = sm.OLS(y, X_used)
    result = model.fit()
    return result


def calculate_partial_r(
    model: sm.regression.linear_model.RegressionResultsWrapper,
    predictor_name: str,
) -> float:
    """
    Compute the partial correlation (partial r) for a given predictor
    from a fitted OLS model.

    The formula derives from the t‑statistic of the coefficient:

        partial_r = sign(t) * sqrt( t^2 / (t^2 + df_resid) )

    Parameters
    ----------
    model : RegressionResultsWrapper
        Fitted OLS model.
    predictor_name : str
        Column name of the predictor whose partial r is desired.

    Returns
    -------
    float
        Partial correlation coefficient.
    """
    if predictor_name not in model.params.index:
        raise KeyError(f"Predictor '{predictor_name}' not found in model coefficients.")

    t_val = model.tvalues[predictor_name]
    df_resid = model.df_resid
    # Guard against division by zero (should never happen with a valid model)
    if df_resid <= 0:
        raise ValueError("Model residual degrees of freedom must be > 0.")

    partial_r = np.sign(t_val) * np.sqrt(t_val ** 2 / (t_val ** 2 + df_resid))
    return float(partial_r)


def calculate_vif(X: Union[pd.DataFrame, np.ndarray]) -> Dict[str, float]:
    """
    Compute Variance Inflation Factors for each column in ``X``.

    Parameters
    ----------
    X : DataFrame or ndarray
        Design matrix. If a constant column is present it will be ignored
        in the VIF calculation (as VIF is undefined for a constant).

    Returns
    -------
    dict
        Mapping from column name (or integer index for ndarray) to VIF value.
    """
    if isinstance(X, np.ndarray):
        X = pd.DataFrame(X)

    # Ensure there is an intercept column; statsmodels' VIF routine expects it.
    if "const" not in X.columns and "Intercept" not in X.columns:
        X = sm.add_constant(X, has_constant="add")

    vif_dict: Dict[str, float] = {}
    for i, col in enumerate(X.columns):
        # Skip the constant term – VIF is not defined for it.
        if col in ("const", "Intercept"):
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_dict[col] = float(vif)
        except Exception as exc:
            # In pathological cases (e.g., singular matrix) we return np.inf
            vif_dict[col] = float("inf")
    return vif_dict


def fdr_benjamini_hochberg(
    p_values: Union[np.ndarray, pd.Series, Iterable[float]],
    alpha: float = 0.05,
) -> Union[np.ndarray, pd.Series]:
    """
    Perform Benjamini‑Hochberg FDR correction.

    The function accepts unsorted p‑values; it internally sorts them,
    determines the largest index ``k`` such that

        p_(k) <= (k / m) * alpha

    where ``m`` is the total number of tests. All hypotheses with
    p‑values less than or equal to ``p_(k)`` are declared significant.

    Parameters
    ----------
    p_values : array‑like
        Collection of p‑values (list, np.ndarray, pd.Series, etc.).
    alpha : float, default 0.05
        Desired FDR level.

    Returns
    -------
    np.ndarray or pd.Series
        Boolean mask of the same shape as ``p_values`` indicating which
        hypotheses are rejected (True) after correction. The return type
        matches the input type when possible (Series → Series, otherwise
        ndarray).
    """
    # Convert to a NumPy array for numeric work while preserving original type
    is_series = isinstance(p_values, pd.Series)
    p_arr = np.asarray(p_values, dtype=float)

    if p_arr.ndim != 1:
        raise ValueError("p_values must be a one‑dimensional array-like object.")

    m = p_arr.size
    if m == 0:
        # Empty input – return an empty boolean array/Series
        return np.array([], dtype=bool) if not is_series else pd.Series([], dtype=bool)

    # Sort p‑values and keep original indices
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    # Compute BH critical values
    crit_vals = (np.arange(1, m + 1) / m) * alpha

    # Find the last index where p <= crit
    below = sorted_p <= crit_vals
    if not np.any(below):
        # No rejections
        reject = np.zeros(m, dtype=bool)
    else:
        max_k = np.max(np.where(below)[0])  # zero‑based index
        # All p‑values up to max_k are significant
        reject = np.arange(m) <= max_k

    # Map back to original order
    unsorted_reject = np.empty(m, dtype=bool)
    unsorted_reject[sorted_indices] = reject

    if is_series:
        return pd.Series(unsorted_reject, index=p_values.index)
    else:
        return unsorted_reject


def classify_effect_size(partial_r: float, threshold: float = 0.3) -> bool:
    """
    Classify whether a partial correlation effect size is clinically meaningful.

    Parameters
    ----------
    partial_r : float
        Partial correlation coefficient.
    threshold : float, default 0.3
        Absolute value threshold defining a "meaningful" effect.

    Returns
    -------
    bool
        ``True`` if ``abs(partial_r) >= threshold``, else ``False``.
    """
    return bool(abs(partial_r) >= threshold)