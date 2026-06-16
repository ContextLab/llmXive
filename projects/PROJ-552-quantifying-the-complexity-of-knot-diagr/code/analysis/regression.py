"""
Regression analysis module for the knot complexity project.

This module provides utilities to:
- Load the cleaned knot dataset.
- Fit linear, polynomial, and logarithmic regression models.
- Compute goodness‑of‑fit metrics (R², MAE, AIC, BIC).
- Compute variance inflation factors (VIF) for multicollinearity assessment.
- Produce a short report of the fitted models.
- Compute descriptive comparison metrics (mean difference, variance ratio,
  Cohen's d) between alternating and non‑alternating knots (T039).

The implementation is deliberately lightweight and relies only on the
project's existing dependencies (pandas, numpy, statsmodels, json,
pathlib, and the project's reproducibility logger).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ----------------------------------------------------------------------
# Data loading utilities
# ----------------------------------------------------------------------
@dataclass
class RegressionMetrics:
    """Container for regression model performance metrics."""

    model_name: str
    r_squared: float
    mae: float
    aic: float
    bic: float

def load_cleaned_knots(data_path: Path = Path("data/processed/knots_cleaned.csv")) -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    Parameters
    ----------
    data_path : Path
        Path to the CSV file containing cleaned knot records.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least the columns:
        - ``crossing_number`` (int)
        - ``braid_index`` (int)
        - ``hyperbolic_volume`` (float)
        - ``alternating`` (bool or str)
    """
    if not data_path.is_file():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    df = pd.read_csv(data_path)
    return df

# ----------------------------------------------------------------------
# Model fitting helpers
# ----------------------------------------------------------------------
def _prepare_features(df: pd.DataFrame, predictor: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Helper to extract predictor and response arrays.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    predictor : str
        Column name of the predictor variable.

    Returns
    -------
    X, y : tuple of ndarrays
        ``X`` is a 2‑D array with an intercept column added.
        ``y`` is the response variable.
    """
    if predictor not in df.columns:
        raise KeyError(f"Predictor column '{predictor}' not found in data.")
    if "hyperbolic_volume" not in df.columns:
        raise KeyError("Response column 'hyperbolic_volume' not found in data.")

    X_raw = df[predictor].to_numpy(dtype=float).reshape(-1, 1)
    # Add intercept
    X = np.hstack([np.ones_like(X_raw), X_raw])
    y = df["hyperbolic_volume"].to_numpy(dtype=float)
    return X, y

def fit_linear_model(df: pd.DataFrame, predictor: str = "crossing_number") -> Tuple[np.ndarray, float]:
    """
    Fit a simple linear regression model: volume = b0 + b1 * predictor.

    Returns
    -------
    coeffs : ndarray
        Coefficients [b0, b1].
    sigma : float
        Estimated standard deviation of residuals.
    """
    X, y = _prepare_features(df, predictor)
    coeffs, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
    # Compute residual standard deviation
    residuals = y - X @ coeffs
    sigma = np.sqrt(np.mean(residuals ** 2))
    return coeffs, sigma

def fit_polynomial_model(df: pd.DataFrame, degree: int = 2, predictor: str = "crossing_number") -> Tuple[np.ndarray, float]:
    """
    Fit a polynomial regression model of specified degree.

    Returns
    -------
    coeffs : ndarray
        Polynomial coefficients ordered from highest degree to constant term.
    sigma : float
        Estimated standard deviation of residuals.
    """
    x = df[predictor].to_numpy(dtype=float)
    y = df["hyperbolic_volume"].to_numpy(dtype=float)
    coeffs = np.polyfit(x, y, deg=degree)
    # Compute residuals
    y_pred = np.polyval(coeffs, x)
    residuals = y - y_pred
    sigma = np.sqrt(np.mean(residuals ** 2))
    return coeffs, sigma

def fit_logarithmic_model(df: pd.DataFrame, predictor: str = "crossing_number") -> Tuple[np.ndarray, float]:
    """
    Fit a model of the form: volume = b0 + b1 * log(predictor).

    Returns
    -------
    coeffs : ndarray
        Coefficients [b0, b1].
    sigma : float
        Estimated standard deviation of residuals.
    """
    x = df[predictor].to_numpy(dtype=float)
    # Guard against non‑positive values for log
    if np.any(x <= 0):
        raise ValueError("Predictor values must be positive for logarithmic model.")
    X = np.column_stack([np.ones_like(x), np.log(x)])
    y = df["hyperbolic_volume"].to_numpy(dtype=float)
    coeffs, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ coeffs
    sigma = np.sqrt(np.mean(residuals ** 2))
    return coeffs, sigma

# ----------------------------------------------------------------------
# Metric calculations
# ----------------------------------------------------------------------
def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of determination."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else float("nan")

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean absolute error."""
    return np.mean(np.abs(y_true - y_pred))

def calculate_aic(n: int, rss: float, k: int) -> float:
    """Akaike Information Criterion."""
    return n * np.log(rss / n) + 2 * k

def calculate_bic(n: int, rss: float, k: int) -> float:
    """Bayesian Information Criterion."""
    return n * np.log(rss / n) + k * np.log(n)

# ----------------------------------------------------------------------
# VIF computation
# ----------------------------------------------------------------------
def compute_vif(df: pd.DataFrame, predictors: List[str]) -> pd.DataFrame:
    """
    Compute variance inflation factors for a set of predictors.

    Parameters
    ----------
    df : pd.DataFrame
        Data containing the predictor columns.
    predictors : list of str
        Column names to assess.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``variable`` and ``VIF``.
    """
    X = df[predictors].assign(const=1)
    vif_data = []
    for i, var in enumerate(predictors):
        vif = variance_inflation_factor(X.values, i)
        vif_data.append({"variable": var, "VIF": vif})
    return pd.DataFrame(vif_data)

# ----------------------------------------------------------------------
# Reporting utilities
# ----------------------------------------------------------------------
def write_metrics_report(metrics: List[RegressionMetrics], output_path: Path = Path("data/processed/regression_metrics.json")) -> None:
    """
    Serialize a list of ``RegressionMetrics`` to JSON.

    The JSON structure is a list of dictionaries, each corresponding to a model.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(m) for m in metrics], f, indent=2)

def write_vif_report(vif_df: pd.DataFrame, output_path: Path = Path("data/processed/vif_report.json")) -> None:
    """Write VIF results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(vif_df.to_dict(orient="records"), f, indent=2)

# ----------------------------------------------------------------------
# Descriptive comparison metrics (T039)
# ----------------------------------------------------------------------
@dataclass
class GroupComparisonMetric:
    """Metrics comparing two groups for a single numeric field."""

    field: str
    mean_difference: float
    variance_ratio: float
    cohens_d: float

def compute_descriptive_comparison(
    df: pd.DataFrame,
    group_col: str = "alternating",
    fields: List[str] = None,
) -> List[GroupComparisonMetric]:
    """
    Compute mean difference, variance ratio, and Cohen's d between the two
    groups defined by ``group_col``.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset containing the fields of interest and a binary grouping column.
    group_col : str
        Column indicating group membership. Expected values are truthy/falsy or
        ``'alternating'`` / ``'non-alternating'``.
    fields : list of str, optional
        Numeric columns for which the comparison should be performed. If ``None``,
        defaults to ``['crossing_number', 'braid_index']``.

    Returns
    -------
    List[GroupComparisonMetric]
        One entry per field.
    """
    if fields is None:
        fields = ["crossing_number", "braid_index"]

    # Normalise the grouping column to boolean
    group_series = df[group_col].astype(bool)

    metrics: List[GroupComparisonMetric] = []
    for field in fields:
        if field not in df.columns:
            raise KeyError(f"Field '{field}' not found in DataFrame.")
        alt_vals = df.loc[group_series, field].dropna().astype(float)
        non_alt_vals = df.loc[~group_series, field].dropna().astype(float)

        # Mean difference (alternating - non‑alternating)
        mean_diff = alt_vals.mean() - non_alt_vals.mean()

        # Variance ratio (alternating / non‑alternating)
        var_ratio = alt_vals.var(ddof=1) / non_alt_vals.var(ddof=1) if non_alt_vals.var(ddof=1) != 0 else float("inf")

        # Pooled standard deviation for Cohen's d
        n1, n2 = len(alt_vals), len(non_alt_vals)
        s1_sq, s2_sq = alt_vals.var(ddof=1), non_alt_vals.var(ddof=1)
        pooled_sd = np.sqrt(((n1 - 1) * s1_sq + (n2 - 1) * s2_sq) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else float("nan")
        cohens_d = mean_diff / pooled_sd if pooled_sd != 0 else float("inf")

        metrics.append(
            GroupComparisonMetric(
                field=field,
                mean_difference=mean_diff,
                variance_ratio=var_ratio,
                cohens_d=cohens_d,
            )
        )
    return metrics

def write_group_comparison_report(
    metrics: List[GroupComparisonMetric],
    output_path: Path = Path("data/processed/group_comparison_metrics.json"),
) -> None:
    """Write the descriptive comparison metrics to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(m) for m in metrics], f, indent=2)

# ----------------------------------------------------------------------
# End‑to‑end regression pipeline
# ----------------------------------------------------------------------
def run_regression_analysis(df: pd.DataFrame) -> List[RegressionMetrics]:
    """
    Fit three regression models (linear, polynomial degree 2, logarithmic) and
    return a list of ``RegressionMetrics`` objects.
    """
    models: List[RegressionMetrics] = []

    # Linear
    coeffs_lin, sigma_lin = fit_linear_model(df)
    X_lin, y = _prepare_features(df, "crossing_number")
    y_pred_lin = X_lin @ coeffs_lin
    rss_lin = np.sum((y - y_pred_lin) ** 2)
    n = len(y)
    models.append(
        RegressionMetrics(
            model_name="linear",
            r_squared=calculate_r_squared(y, y_pred_lin),
            mae=calculate_mae(y, y_pred_lin),
            aic=calculate_aic(n, rss_lin, k=2),
            bic=calculate_bic(n, rss_lin, k=2),
        )
    )

    # Polynomial (degree 2)
    coeffs_poly, sigma_poly = fit_polynomial_model(df, degree=2)
    y_pred_poly = np.polyval(coeffs_poly, df["crossing_number"])
    rss_poly = np.sum((y - y_pred_poly) ** 2)
    models.append(
        RegressionMetrics(
            model_name="polynomial_degree_2",
            r_squared=calculate_r_squared(y, y_pred_poly),
            mae=calculate_mae(y, y_pred_poly),
            aic=calculate_aic(n, rss_poly, k=3),
            bic=calculate_bic(n, rss_poly, k=3),
        )
    )

    # Logarithmic
    coeffs_log, sigma_log = fit_logarithmic_model(df)
    X_log = np.column_stack([np.ones_like(df["crossing_number"]), np.log(df["crossing_number"])])
    y_pred_log = X_log @ coeffs_log
    rss_log = np.sum((y - y_pred_log) ** 2)
    models.append(
        RegressionMetrics(
            model_name="logarithmic",
            r_squared=calculate_r_squared(y, y_pred_log),
            mae=calculate_mae(y, y_pred_log),
            aic=calculate_aic(n, rss_log, k=2),
            bic=calculate_bic(n, rss_log, k=2),
        )
    )
    return models

def main() -> None:
    """
    Entry point for the regression analysis pipeline.

    The function:
    1. Loads the cleaned knot dataset.
    2. Runs regression fitting and writes the model metrics.
    3. Computes VIF for the two core predictors.
    4. Computes descriptive comparison metrics for alternating vs.
       non‑alternating knots (T039) and writes the result.
    """
    try:
        df = load_cleaned_knots()
    except Exception as exc:
        sys.stderr.write(f"Failed to load cleaned data: {exc}\\n")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Regression models
    # ------------------------------------------------------------------
    metrics = run_regression_analysis(df)
    write_metrics_report(metrics)

    # ------------------------------------------------------------------
    # VIF assessment (core invariants)
    # ------------------------------------------------------------------
    try:
        vif_df = compute_vif(df, predictors=["crossing_number", "braid_index"])
        write_vif_report(vif_df)
    except Exception as exc:
        sys.stderr.write(f"VIF computation failed: {exc}\\n")

    # ------------------------------------------------------------------
    # Descriptive group comparison (T039)
    # ------------------------------------------------------------------
    try:
        group_metrics = compute_descriptive_comparison(df)
        write_group_comparison_report(group_metrics)
    except Exception as exc:
        sys.stderr.write(f"Group comparison computation failed: {exc}\\n")

    # Successful completion
    sys.exit(0)

if __name__ == "__main__":
    main()
