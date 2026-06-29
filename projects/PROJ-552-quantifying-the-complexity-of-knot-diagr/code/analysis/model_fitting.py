"""Model fitting and regression analysis utilities.

This module provides functions to fit linear, polynomial, and logarithmic
regression models to predict hyperbolic volume from crossing number and
braid index. It also computes goodness-of-fit metrics (R², AIC, BIC, MAE),
performs residual analysis, and identifies knot families with large residuals.

All output is written to ``data/analysis/regression_metrics.json`` and
``docs/reproducibility/residual_analysis.md``.
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
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import PolynomialFeatures

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation


@dataclass
class RegressionMetrics:
    """Goodness-of-fit metrics for a regression model."""
    model_type: str
    r_squared: float
    aic: float
    bic: float
    mae: float
    coefficients: Dict[str, float]
    intercept: float


@dataclass
class LinearModelResult:
    """Result of fitting a linear model."""
    model: LinearRegression
    metrics: RegressionMetrics
    residuals: np.ndarray
    predictions: np.ndarray


@dataclass
class ResidualEntry:
    """Entry for residual analysis output."""
    knot_id: str
    crossing_number: float
    braid_index: float
    hyperbolic_volume: float
    predicted_volume: float
    residual: float
    residual_std: float
    is_outlier: bool
    family: Optional[str]


@log_operation
def fit_linear_model(
    df: pd.DataFrame,
    features: List[str],
    target: str = "hyperbolic_volume"
) -> LinearModelResult:
    """
    Fit a linear regression model to predict the target variable.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    features : List[str]
        List of column names to use as features.
    target : str
        Column name of the target variable.

    Returns
    -------
    LinearModelResult
        Result containing the fitted model, metrics, residuals, and predictions.
    """
    logger = get_logger(__name__)
    logger.info("Fitting linear model with features: %s", features)

    # Prepare data
    X = df[features].dropna().values
    y = df.loc[X.index, target].values

    if len(X) == 0:
        raise ValueError("No data available after dropping NaN values.")

    # Fit model
    model = LinearRegression()
    model.fit(X, y)

    # Predictions and residuals
    predictions = model.predict(X)
    residuals = y - predictions

    # Metrics
    r2 = r2_score(y, predictions)
    mae = mean_absolute_error(y, predictions)

    # AIC and BIC calculation
    n = len(y)
    k = len(features)
    rss = np.sum(residuals ** 2)
    sigma2 = rss / (n - k - 1) if (n - k - 1) > 0 else 1e-10

    # AIC = n * ln(RSS/n) + 2k (simplified for linear regression)
    aic = n * np.log(rss / n) + 2 * (k + 1)
    # BIC = n * ln(RSS/n) + k * ln(n)
    bic = n * np.log(rss / n) + (k + 1) * np.log(n)

    # Coefficients
    coeff_dict = {feat: float(coef) for feat, coef in zip(features, model.coef_)}

    metrics = RegressionMetrics(
        model_type="linear",
        r_squared=float(r2),
        aic=float(aic),
        bic=float(bic),
        mae=float(mae),
        coefficients=coeff_dict,
        intercept=float(model.intercept_)
    )

    logger.debug("Model fitted: R²=%.4f, MAE=%.4f", r2, mae)

    return LinearModelResult(
        model=model,
        metrics=metrics,
        residuals=residuals,
        predictions=predictions
    )


@log_operation
def fit_polynomial_model(
    df: pd.DataFrame,
    feature: str,
    degree: int = 2,
    target: str = "hyperbolic_volume"
) -> LinearModelResult:
    """
    Fit a polynomial regression model.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    feature : str
        Column name of the single feature to use.
    degree : int
        Degree of the polynomial.
    target : str
        Column name of the target variable.

    Returns
    -------
    LinearModelResult
        Result containing the fitted model and metrics.
    """
    logger = get_logger(__name__)
    logger.info("Fitting polynomial model (degree=%d) for feature: %s", degree, feature)

    # Prepare data
    X = df[[feature]].dropna()
    y = df.loc[X.index, target]

    if len(X) == 0:
        raise ValueError("No data available after dropping NaN values.")

    X_values = X.values
    y_values = y.values

    # Polynomial features
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X_values)

    # Fit model
    model = LinearRegression()
    model.fit(X_poly, y_values)

    # Predictions and residuals
    predictions = model.predict(X_poly)
    residuals = y_values - predictions

    # Metrics
    r2 = r2_score(y_values, predictions)
    mae = mean_absolute_error(y_values, predictions)

    # AIC and BIC
    n = len(y_values)
    k = degree  # number of polynomial terms (excluding bias)
    rss = np.sum(residuals ** 2)
    sigma2 = rss / (n - k - 1) if (n - k - 1) > 0 else 1e-10

    aic = n * np.log(rss / n) + 2 * (k + 1)
    bic = n * np.log(rss / n) + (k + 1) * np.log(n)

    # Coefficients (map to polynomial terms)
    coeff_dict = {}
    for i, coef in enumerate(model.coef_):
        if i == 0:
            coeff_dict[f"{feature}^1"] = float(coef)
        else:
            coeff_dict[f"{feature}^{i+1}"] = float(coef)

    metrics = RegressionMetrics(
        model_type=f"polynomial_degree_{degree}",
        r_squared=float(r2),
        aic=float(aic),
        bic=float(bic),
        mae=float(mae),
        coefficients=coeff_dict,
        intercept=float(model.intercept_)
    )

    logger.debug("Polynomial model fitted: R²=%.4f, MAE=%.4f", r2, mae)

    return LinearModelResult(
        model=model,
        metrics=metrics,
        residuals=residuals,
        predictions=predictions
    )


@log_operation
def fit_logarithmic_model(
    df: pd.DataFrame,
    feature: str,
    target: str = "hyperbolic_volume"
) -> LinearModelResult:
    """
    Fit a logarithmic regression model (y = a + b * ln(x)).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    feature : str
        Column name of the feature to use.
    target : str
        Column name of the target variable.

    Returns
    -------
    LinearModelResult
        Result containing the fitted model and metrics.
    """
    logger = get_logger(__name__)
    logger.info("Fitting logarithmic model for feature: %s", feature)

    # Prepare data (filter out non-positive values for log)
    mask = df[feature] > 0
    X = df.loc[mask, [feature]]
    y = df.loc[mask, target]

    if len(X) == 0:
        raise ValueError("No data available with positive feature values.")

    X_values = np.log(X.values)
    y_values = y.values

    # Fit model
    model = LinearRegression()
    model.fit(X_values, y_values)

    # Predictions and residuals
    predictions = model.predict(X_values)
    residuals = y_values - predictions

    # Metrics
    r2 = r2_score(y_values, predictions)
    mae = mean_absolute_error(y_values, predictions)

    # AIC and BIC
    n = len(y_values)
    k = 1
    rss = np.sum(residuals ** 2)

    aic = n * np.log(rss / n) + 2 * (k + 1)
    bic = n * np.log(rss / n) + (k + 1) * np.log(n)

    coeff_dict = {f"ln({feature})": float(model.coef_[0])}

    metrics = RegressionMetrics(
        model_type="logarithmic",
        r_squared=float(r2),
        aic=float(aic),
        bic=float(bic),
        mae=float(mae),
        coefficients=coeff_dict,
        intercept=float(model.intercept_)
    )

    logger.debug("Logarithmic model fitted: R²=%.4f, MAE=%.4f", r2, mae)

    return LinearModelResult(
        model=model,
        metrics=metrics,
        residuals=residuals,
        predictions=predictions
    )


@log_operation
def identify_residual_families(
    df: pd.DataFrame,
    result: LinearModelResult,
    threshold_std: float = 2.0
) -> Tuple[List[ResidualEntry], Dict[str, int]]:
    """
    Identify knot families with large residuals and categorize them.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing knot data.
    result : LinearModelResult
        Result from a fitted model.
    threshold_std : float
        Number of standard deviations to consider an outlier.

    Returns
    -------
    tuple[List[ResidualEntry], Dict[str, int]]
        List of outlier entries and a count of families.
    """
    logger = get_logger(__name__)
    logger.info("Identifying residual families with threshold=%.2f std", threshold_std)

    # Align indices
    valid_indices = df.dropna(subset=["hyperbolic_volume"]).index
    df_valid = df.loc[valid_indices]

    # Ensure residuals align
    residuals = result.residuals[:len(df_valid)]
    predictions = result.predictions[:len(df_valid)]

    # Calculate mean and std of residuals
    mean_res = np.mean(residuals)
    std_res = np.std(residuals)

    outlier_entries = []
    family_counts: Dict[str, int] = {}

    for idx, row in df_valid.iterrows():
        res_idx = list(df_valid.index).index(idx)
        residual = residuals[res_idx]
        pred = predictions[res_idx]

        is_outlier = abs(residual - mean_res) > threshold_std * std_res

        # Heuristic family classification based on knot ID or properties
        # This is a simplified heuristic; real classification would use knot family info
        knot_id = str(row.get("knot_id", "unknown"))
        family = "unknown"

        if "pretzel" in knot_id.lower() or row.get("family", "").lower() == "pretzel":
            family = "pretzel"
        elif row.get("hyperbolic_volume", 0) > 0 and not row.get("alternating", False):
            family = "hyperbolic_non_alternating"
        else:
            family = "other"

        family_counts[family] = family_counts.get(family, 0) + 1

        if is_outlier:
            entry = ResidualEntry(
                knot_id=knot_id,
                crossing_number=float(row["crossing_number"]),
                braid_index=float(row["braid_index"]),
                hyperbolic_volume=float(row["hyperbolic_volume"]),
                predicted_volume=float(pred),
                residual=float(residual),
                residual_std=float(std_res),
                is_outlier=True,
                family=family
            )
            outlier_entries.append(entry)

    logger.debug("Found %d outliers", len(outlier_entries))
    return outlier_entries, family_counts


@log_operation
def write_regression_metrics_report(
    output_path: Path,
    metrics_list: List[RegressionMetrics]
) -> None:
    """
    Serialize regression metrics to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = [asdict(m) for m in metrics_list]
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger = get_logger(__name__)
    logger.info("Regression metrics report written to %s", output_path)


@log_operation
def write_residual_analysis_report(
    output_path: Path,
    outlier_entries: List[ResidualEntry],
    family_counts: Dict[str, int]
) -> None:
    """
    Write residual analysis report to Markdown.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Residual Analysis Report\n\n")
        f.write("## Outlier Knots\n\n")
        f.write("| Knot ID | Crossing | Braid | Volume | Predicted | Residual | Family |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for entry in outlier_entries:
            f.write(f"| {entry.knot_id} | {entry.crossing_number} | "
                    f"{entry.braid_index} | {entry.hyperbolic_volume:.4f} | "
                    f"{entry.predicted_volume:.4f} | {entry.residual:.4f} | "
                    f"{entry.family} |\n")

        f.write("\n## Family Distribution\n\n")
        for family, count in family_counts.items():
            f.write(f"- {family}: {count}\n")

    logger = get_logger(__name__)
    logger.info("Residual analysis report written to %s", output_path)


@log_operation
def main() -> None:
    """
    Entry-point for regression analysis.
    """
    logger = get_logger(__name__)
    logger.info("Starting regression analysis pipeline")

    df = load_cleaned_knots()

    # Filter for hyperbolic knots (volume > 0)
    df_hyper = df[df["hyperbolic_volume"] > 0].copy()

    if len(df_hyper) == 0:
        logger.error("No hyperbolic knots found in dataset.")
        return

    # Fit models
    metrics_list: List[RegressionMetrics] = []

    # 1. Linear model: Volume ~ Crossing + Braid
    try:
        result_linear = fit_linear_model(
            df_hyper,
            features=["crossing_number", "braid_index"],
            target="hyperbolic_volume"
        )
        metrics_list.append(result_linear.metrics)

        # Identify outliers
        outliers, families = identify_residual_families(df_hyper, result_linear)
        out_path = Path("docs/reproducibility/residual_analysis.md")
        write_residual_analysis_report(out_path, outliers, families)

    except Exception as e:
        logger.error("Linear model failed: %s", str(e))

    # 2. Polynomial model: Volume ~ Crossing^2
    try:
        result_poly = fit_polynomial_model(
            df_hyper,
            feature="crossing_number",
            degree=2,
            target="hyperbolic_volume"
        )
        metrics_list.append(result_poly.metrics)
    except Exception as e:
        logger.error("Polynomial model failed: %s", str(e))

    # 3. Logarithmic model: Volume ~ ln(Crossing)
    try:
        result_log = fit_logarithmic_model(
            df_hyper,
            feature="crossing_number",
            target="hyperbolic_volume"
        )
        metrics_list.append(result_log.metrics)
    except Exception as e:
        logger.error("Logarithmic model failed: %s", str(e))

    # Write metrics report
    metrics_path = Path("data/analysis/regression_metrics.json")
    write_regression_metrics_report(metrics_path, metrics_list)

    print(f"Regression analysis complete. Metrics saved to {metrics_path}")
    print(f"Residual analysis saved to docs/reproducibility/residual_analysis.md")
