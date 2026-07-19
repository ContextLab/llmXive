"""
Model Fitting Module for Knot Complexity Analysis.

This module handles the fitting of regression models (Linear, Polynomial, Logarithmic)
to assess the relationship between hyperbolic volume, crossing number, and braid index.
It calculates metrics (R², AIC, BIC, MAE) and identifies outlier families.

Note: Per FR-005, Ridge regression is explicitly excluded.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from code.reproducibility.logs import get_logger, log_operation

logger = get_logger(__name__)


@dataclass
class RegressionMetrics:
    """Container for regression model metrics."""
    model_type: str
    r_squared: float
    aic: float
    bic: float
    mae: float
    rmse: float
    n_params: int
    n_obs: int
    coefficients: Dict[str, float]
    variance_explained: float

@dataclass
class LinearModelResult:
    """Result of a linear model fit."""
    model_type: str
    formula: str
    metrics: RegressionMetrics
    fitted_values: List[float]
    residuals: List[float]
    summary_text: str

@dataclass
class ResidualEntry:
    """Entry for residual analysis."""
    knot_id: str
    family: str
    crossing_number: float
    braid_index: float
    hyperbolic_volume: float
    predicted_volume: float
    residual: float
    standardized_residual: float


@log_operation
def fit_linear_model(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    model_name: str = "Linear"
) -> LinearModelResult:
    """
    Fit a simple linear regression model.

    Args:
        df: DataFrame containing the data.
        x_col: Name of the independent variable column.
        y_col: Name of the dependent variable column.
        model_name: Name for the model in reports.

    Returns:
        LinearModelResult object containing metrics and fit data.
    """
    x = df[x_col].dropna().values
    y = df[y_col].dropna().values

    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Insufficient data for linear regression.")

    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    fitted = slope * x + intercept
    residuals = y - fitted

    # Calculate metrics
    r_squared = r_value ** 2
    n = len(x)
    n_params = 2  # slope, intercept

    # AIC and BIC calculation
    # SSE = Sum of Squared Errors
    sse = np.sum(residuals ** 2)
    mse = sse / n
    # Log-likelihood approximation for linear regression with Gaussian errors
    # LL = -n/2 * (log(2*pi) + log(SSE/n) + 1)
    # AIC = 2k - 2LL
    # BIC = k*log(n) - 2LL
    # Simplified for comparison:
    aic = n * np.log(sse / n) + 2 * n_params
    bic = n * np.log(sse / n) + n_params * np.log(n)

    mae = np.mean(np.abs(residuals))
    rmse = np.sqrt(mse)

    # Variance explained (R^2)
    variance_explained = r_squared

    coefficients = {"intercept": float(intercept), "slope": float(slope)}

    metrics = RegressionMetrics(
        model_type=model_name,
        r_squared=float(r_squared),
        aic=float(aic),
        bic=float(bic),
        mae=float(mae),
        rmse=float(rmse),
        n_params=n_params,
        n_obs=n,
        coefficients=coefficients,
        variance_explained=variance_explained
    )

    summary = (
        f"{model_name} Model: {y_col} = {intercept:.4f} + {slope:.4f} * {x_col}\n"
        f"R² = {r_squared:.4f}, MAE = {mae:.4f}, RMSE = {rmse:.4f}"
    )

    return LinearModelResult(
        model_type=model_name,
        formula=f"{y_col} = {intercept:.4f} + {slope:.4f} * {x_col}",
        metrics=metrics,
        fitted_values=fitted.tolist(),
        residuals=residuals.tolist(),
        summary_text=summary
    )


@log_operation
def fit_polynomial_model(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    degree: int = 2,
    model_name: str = "Polynomial"
) -> LinearModelResult:
    """
    Fit a polynomial regression model.

    Args:
        df: DataFrame containing the data.
        x_col: Name of the independent variable column.
        y_col: Name of the dependent variable column.
        degree: Degree of the polynomial.
        model_name: Name for the model in reports.

    Returns:
        LinearModelResult object.
    """
    x = df[x_col].dropna().values
    y = df[y_col].dropna().values

    if len(x) != len(y) or len(x) <= degree:
        raise ValueError(f"Insufficient data for polynomial degree {degree}.")

    # Fit polynomial
    coeffs = np.polyfit(x, y, degree)
    poly_func = np.poly1d(coeffs)

    fitted = poly_func(x)
    residuals = y - fitted

    # Metrics
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    n = len(x)
    n_params = degree + 1

    sse = ss_res
    aic = n * np.log(sse / n) + 2 * n_params
    bic = n * np.log(sse / n) + n_params * np.log(n)

    mae = np.mean(np.abs(residuals))
    rmse = np.sqrt(sse / n)

    coeffs_dict = {f"coeff_{i}": float(c) for i, c in enumerate(reversed(coeffs))}

    metrics = RegressionMetrics(
        model_type=model_name,
        r_squared=float(r_squared),
        aic=float(aic),
        bic=float(bic),
        mae=float(mae),
        rmse=float(rmse),
        n_params=n_params,
        n_obs=n,
        coefficients=coeffs_dict,
        variance_explained=float(r_squared)
    )

    formula = f"{y_col} = " + " + ".join([f"{c:.4f}*{x_col}^{i}" if i > 0 else f"{c:.4f}" for i, c in enumerate(reversed(coeffs))])

    summary = f"{model_name} (deg={degree}): R² = {r_squared:.4f}, MAE = {mae:.4f}"

    return LinearModelResult(
        model_type=model_name,
        formula=formula,
        metrics=metrics,
        fitted_values=fitted.tolist(),
        residuals=residuals.tolist(),
        summary_text=summary
    )


@log_operation
def fit_logarithmic_model(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    model_name: str = "Logarithmic"
) -> LinearModelResult:
    """
    Fit a logarithmic regression model: y = a + b * log(x).

    Args:
        df: DataFrame containing the data.
        x_col: Name of the independent variable column.
        y_col: Name of the dependent variable column.
        model_name: Name for the model in reports.

    Returns:
        LinearModelResult object.
    """
    x = df[x_col].dropna().values
    y = df[y_col].dropna().values

    # Filter out non-positive x values for log
    mask = x > 0
    x_valid = x[mask]
    y_valid = y[mask]

    if len(x_valid) < 2:
        raise ValueError("Insufficient positive data for logarithmic regression.")

    log_x = np.log(x_valid)

    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, y_valid)

    fitted = slope * log_x + intercept
    residuals = y_valid - fitted

    r_squared = r_value ** 2
    n = len(x_valid)
    n_params = 2

    sse = np.sum(residuals ** 2)
    aic = n * np.log(sse / n) + 2 * n_params
    bic = n * np.log(sse / n) + n_params * np.log(n)

    mae = np.mean(np.abs(residuals))
    rmse = np.sqrt(sse / n)

    coefficients = {"intercept": float(intercept), "log_slope": float(slope)}

    metrics = RegressionMetrics(
        model_type=model_name,
        r_squared=float(r_squared),
        aic=float(aic),
        bic=float(bic),
        mae=float(mae),
        rmse=float(rmse),
        n_params=n_params,
        n_obs=n,
        coefficients=coefficients,
        variance_explained=float(r_squared)
    )

    summary = f"{model_name} Model: R² = {r_squared:.4f}, MAE = {mae:.4f}"

    return LinearModelResult(
        model_type=model_name,
        formula=f"{y_col} = {intercept:.4f} + {slope:.4f} * log({x_col})",
        metrics=metrics,
        fitted_values=fitted.tolist(),
        residuals=residuals.tolist(),
        summary_text=summary
    )


@log_operation
def identify_residual_families(
    df: pd.DataFrame,
    residuals: List[float],
    family_col: str = "family",
    threshold_sd: float = 2.0
) -> List[ResidualEntry]:
    """
    Identify knot families with residuals deviating >= threshold_sd standard deviations.

    Args:
        df: DataFrame with knot data.
        residuals: List of residuals corresponding to the DataFrame rows.
        family_col: Column name for knot families.
        threshold_sd: Number of standard deviations for outlier detection.

    Returns:
        List of ResidualEntry objects for outliers.
    """
    if len(residuals) == 0:
        return []

    mean_res = np.mean(residuals)
    std_res = np.std(residuals)

    if std_res == 0:
        return []

    outliers = []
    for idx, res in enumerate(residuals):
        std_res_val = (res - mean_res) / std_res
        if abs(std_res_val) >= threshold_sd:
            row = df.iloc[idx]
            entry = ResidualEntry(
                knot_id=str(row.get("knot_id", f"idx_{idx}")),
                family=str(row.get(family_col, "Unknown")),
                crossing_number=float(row.get("crossing_number", 0)),
                braid_index=float(row.get("braid_index", 0)),
                hyperbolic_volume=float(row.get("hyperbolic_volume", 0)),
                predicted_volume=float(row.get("predicted_volume", 0)),
                residual=float(res),
                standardized_residual=float(std_res_val)
            )
            outliers.append(entry)

    logger.log("residual_outliers_identified", parameters={"count": len(outliers), "threshold": threshold_sd})
    return outliers


@log_operation
def write_regression_metrics_report(
    results: List[LinearModelResult],
    output_path: Path
) -> None:
    """
    Write regression metrics to a JSON report file.

    Args:
        results: List of LinearModelResult objects.
        output_path: Path to the output JSON file.
    """
    report_data = []
    for res in results:
        report_data.append({
            "model_type": res.model_type,
            "formula": res.formula,
            "metrics": asdict(res.metrics),
            "summary": res.summary_text
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    logger.log("regression_metrics_report_written", parameters={"path": str(output_path), "models": len(results)})


@log_operation
def write_residual_analysis_report(
    outliers: List[ResidualEntry],
    output_path: Path
) -> None:
    """
    Write residual analysis outliers to a JSON file.

    Args:
        outliers: List of ResidualEntry objects.
        output_path: Path to the output JSON file.
    """
    data = [asdict(o) for o in outliers]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.log("residual_analysis_report_written", parameters={"path": str(output_path), "outliers": len(outliers)})


def main() -> None:
    """
    Main entry point for model fitting analysis.
    Loads cleaned data, fits models, and generates reports.
    """
    logger.log("model_fitting_start", parameters={})

    # Load data
    data_path = Path("data/processed/knots_cleaned.csv")
    if not data_path.exists():
        logger.log("model_fitting_error", parameters={"error": "Data file not found", "path": str(data_path)})
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Filter for required columns
    required_cols = ["crossing_number", "braid_index", "hyperbolic_volume", "family"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Drop rows with NaN in key columns
    df_clean = df.dropna(subset=required_cols)

    # Fit models
    x_col = "crossing_number"
    y_col = "hyperbolic_volume"

    models = []

    # 1. Linear
    try:
        linear_res = fit_linear_model(df_clean, x_col, y_col)
        models.append(linear_res)
    except Exception as e:
        logger.log("model_fit_error", parameters={"model": "Linear", "error": str(e)})

    # 2. Polynomial (degree 2)
    try:
        poly_res = fit_polynomial_model(df_clean, x_col, y_col, degree=2)
        models.append(poly_res)
    except Exception as e:
        logger.log("model_fit_error", parameters={"model": "Polynomial", "error": str(e)})

    # 3. Logarithmic
    try:
        log_res = fit_logarithmic_model(df_clean, x_col, y_col)
        models.append(log_res)
    except Exception as e:
        logger.log("model_fit_error", parameters={"model": "Logarithmic", "error": str(e)})

    # Write metrics report
    metrics_path = Path("data/reports/regression_metrics.json")
    write_regression_metrics_report(models, metrics_path)

    # Residual analysis for best model (highest R^2)
    best_model = max(models, key=lambda m: m.metrics.r_squared)
    outliers = identify_residual_families(df_clean, best_model.residuals)

    outliers_path = Path("data/reports/residual_outliers.json")
    write_residual_analysis_report(outliers, outliers_path)

    logger.log("model_fitting_complete", parameters={"models_fitted": len(models), "outliers_found": len(outliers)})


if __name__ == "__main__":
    main()
