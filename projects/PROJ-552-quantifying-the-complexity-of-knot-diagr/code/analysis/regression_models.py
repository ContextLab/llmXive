"""Unified regression and model fitting utilities.

This module consolidates logic from `model_fitting.py`, `regression.py`, and
`residual_analysis.py` into a single, well-structured file. It clearly separates:
1. Model fitting (linear, polynomial, logarithmic).
2. Metric calculation (R², AIC, BIC, MAE, correlations).
3. Residual analysis (outlier detection, family grouping).

The file adheres to PEP 8 style and is kept under 2,000 lines.
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
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import PolynomialFeatures

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation


# -----------------------------------------------------------------------------
# Data Classes: Model Fitting & Metrics
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Data Classes: Correlation & Effect Size (from regression.py)
# -----------------------------------------------------------------------------


@dataclass
class CorrelationResult:
    """Pearson and Spearman correlation coefficients."""

    pearson_r: float
    spearman_rho: float


@dataclass
class EffectSizeResult:
    """Effect-size metrics derived from the correlations."""

    cohen_d: float
    r: float  # same as Pearson r for convenience


# -----------------------------------------------------------------------------
# Model Fitting Logic
# -----------------------------------------------------------------------------


@log_operation
@log_operation
def fit_polynomial_model(
    df: pd.DataFrame,
    feature: str,
    target: str = "hyperbolic_volume",
    degree: int = 2
) -> LinearModelResult:
    """
    Fit a polynomial regression model.

    Parameters
    ----------
    df: pd.DataFrame
    feature: str
        Single column name to use as predictor.
    target: str
    degree: int
        Degree of the polynomial.

    Returns
    -------
    LinearModelResult
    """
    logger = get_logger(__name__)
    logger.info("Fitting polynomial model (degree=%d) for feature: %s", degree, feature)

    X_raw = df[[feature]].dropna()
    y = df.loc[X_raw.index, target]

    if len(X_raw) == 0:
        raise ValueError("No valid data points.")

    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X_raw)
    feature_names = [f"{feature}^{i}" for i in range(degree + 1)]

    model = LinearRegression()
    model.fit(X_poly, y)

    predictions = model.predict(X_poly)
    residuals = y - predictions

    r2 = r2_score(y, predictions)
    mae = mean_absolute_error(y, predictions)
    n = len(y)
    k = degree

    rss = np.sum(residuals**2)
    mse = rss / n if n > 0 else 1e-10
    if mse == 0:
        mse = 1e-10
    log_mse = math.log(mse)
    aic = n * log_mse + 2 * k
    bic = n * log_mse + k * math.log(n)

    coeffs = {name: float(coef) for name, coef in zip(feature_names, model.coef_)}

    metrics = RegressionMetrics(
        model_type=f"polynomial_{degree}",
        r_squared=r2,
        aic=aic,
        bic=bic,
        mae=mae,
        coefficients=coeffs,
        intercept=float(model.intercept_)
    )

    return LinearModelResult(
        model=model,
        metrics=metrics,
        residuals=residuals.values,
        predictions=predictions
    )


# -----------------------------------------------------------------------------
# Residual Analysis Logic
# -----------------------------------------------------------------------------


@log_operation
def analyze_residuals(
    df: pd.DataFrame,
    predictions: np.ndarray,
    target: str = "hyperbolic_volume",
    std_threshold: float = 2.0
) -> List[ResidualEntry]:
    """
    Perform residual analysis to identify outliers and group statistics.

    Parameters
    ----------
    df: pd.DataFrame
    predictions: np.ndarray
    target: str
    std_threshold: float
        Number of standard deviations to flag as outlier.

    Returns
    -------
    List[ResidualEntry]
    """
    logger = get_logger(__name__)
    logger.info("Performing residual analysis with threshold=%s", std_threshold)

    residuals = df[target].values - predictions
    mean_res = np.mean(residuals)
    std_res = np.std(residuals)

    if std_res == 0:
        std_res = 1e-10

    entries = []
    for i, (_, row) in enumerate(df.iterrows()):
        res_val = residuals[i]
        is_outlier = abs(res_val) > (std_threshold * std_res)

        entry = ResidualEntry(
            knot_id=str(row.get("knot_id", f"row_{i}")),
            crossing_number=float(row.get("crossing_number", 0)),
            braid_index=float(row.get("braid_index", 0)),
            hyperbolic_volume=float(row.get(target, 0)),
            predicted_volume=float(predictions[i]),
            residual=float(res_val),
            residual_std=float(std_res),
            is_outlier=is_outlier,
            family=row.get("family", None)
        )
        entries.append(entry)

    outlier_count = sum(1 for e in entries if e.is_outlier)
    logger.info("Found %d outliers (%.2f%%)", outlier_count, 100 * outlier_count / len(entries))

    return entries


@log_operation
def write_residual_analysis_report(
    output_path: Path,
    entries: List[ResidualEntry]
) -> None:
    """
    Write residual analysis results to a Markdown file.
    """
    logger = get_logger(__name__)
    logger.info("Writing residual analysis report to %s", output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Residual Analysis Report\n\n")
        f.write(f"Total samples: {len(entries)}\n")
        f.write(f"Outliers (|z| > 2): {sum(1 for e in entries if e.is_outlier)}\n\n")

        f.write("## Top 10 Largest Residuals\n\n")
        f.write("| Knot ID | Crossing | Braid | Actual | Predicted | Residual | |z| |\n")
        f.write("|---|---|---|---|---|---|---|\n")

        sorted_entries = sorted(entries, key=lambda x: abs(x.residual), reverse=True)[:10]
        for e in sorted_entries:
            z_score = abs(e.residual) / e.residual_std
            f.write(
                f"| {e.knot_id} | {e.crossing_number} | {e.braid_index} | "
                f"{e.hyperbolic_volume:.3f} | {e.predicted_volume:.3f} | "
                f"{e.residual:.3f} | {z_score:.2f} |\n"
            )

        f.write("\n## All Entries (JSON)\n\n")
        # Optionally append full JSON if needed, or just summary
        f.write("(Full data available in the associated JSON metrics file.)\n")


# -----------------------------------------------------------------------------
# Correlation & Effect Size Logic (from regression.py)
# -----------------------------------------------------------------------------


@log_operation
def compute_correlations_and_effect_sizes(df: pd.DataFrame) -> Tuple[CorrelationResult, EffectSizeResult]:
    """
    Compute Pearson and Spearman correlations between ``crossing_number`` and
    ``braid_index``. Also compute Cohen's d for the difference between
    *alternating* and *non‑alternating* knots.

    Parameters
    ----------
    df: pd.DataFrame
        Must contain ``crossing_number``, ``braid_index``, and ``alternating``.

    Returns
    -------
    tuple[CorrelationResult, EffectSizeResult]
    """
    logger = get_logger(__name__)
    logger.info("Starting correlation and effect‑size computation")

    # 1. Correlations
    corr_df = df.dropna(subset=["crossing_number", "braid_index"])
    x = corr_df["crossing_number"].astype(float)
    y = corr_df["braid_index"].astype(float)

    if len(x) == 0:
        raise ValueError("No data available for correlation computation.")

    pearson_r, _ = pearsonr(x, y)
    spearman_rho, _ = spearmanr(x, y)

    corr_res = CorrelationResult(pearson_r=pearson_r, spearman_rho=spearman_rho)
    logger.debug("Pearson r=%s, Spearman rho=%s", pearson_r, spearman_rho)

    # 2. Cohen's d
    alt_series = df["alternating"].apply(
        lambda v: True if str(v).lower() in {"alternating", "true", "1"} else False
    )
    group_a = df.loc[alt_series, "crossing_number"].astype(float)
    group_b = df.loc[~alt_series, "crossing_number"].astype(float)

    if len(group_a) == 0 or len(group_b) == 0:
        raise ValueError("Both alternating and non‑alternating groups must be present.")

    mean_a, mean_b = group_a.mean(), group_b.mean()
    var_a, var_b = group_a.var(ddof=1), group_b.var(ddof=1)
    n_a, n_b = len(group_a), len(group_b)

    pooled_sd = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    cohen_d = (mean_a - mean_b) / pooled_sd if pooled_sd != 0 else 0.0

    effect_res = EffectSizeResult(cohen_d=cohen_d, r=pearson_r)
    logger.debug("Cohen's d=%s", cohen_d)

    return corr_res, effect_res


@log_operation
def write_correlation_effects_report(
    output_path: Path,
    corr: CorrelationResult,
    effect: EffectSizeResult,
) -> None:
    """
    Serialize the correlation and effect‑size results to JSON.
    """
    logger = get_logger(__name__)
    report = {
        "pearson_r": corr.pearson_r,
        "spearman_rho": corr.spearman_rho,
        "cohen_d": effect.cohen_d,
        "r_effect_size": effect.r,
        "p_values": "not applicable for census data",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Correlation‑effect report written to %s", output_path)


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------


@log_operation
def main() -> None:
    """
    Run a full pipeline: load data, fit models, analyze residuals, compute correlations.
    """
    logger = get_logger(__name__)
    logger.info("Starting unified regression analysis pipeline")

    df = load_cleaned_knots()

    # 1. Correlations
    corr_res, effect_res = compute_correlations_and_effect_sizes(df)
    write_correlation_effects_report(
        Path("data/analysis/correlation_effects_report.json"),
        corr_res,
        effect_res
    )

    # 2. Model Fitting (Linear Example)
    features = ["crossing_number", "braid_index"]
    if "hyperbolic_volume" in df.columns:
        result = fit_linear_model(df, features)
        
        # 3. Residual Analysis
        residuals = analyze_residuals(df, result.predictions)
        write_residual_analysis_report(
            Path("docs/reproducibility/residual_analysis.md"),
            residuals
        )

        # Save metrics
        metrics_out = Path("data/analysis/regression_metrics.json")
        metrics_out.parent.mkdir(parents=True, exist_ok=True)
        with metrics_out.open("w", encoding="utf-8") as f:
            json.dump(asdict(result.metrics), f, indent=2)
        logger.info("Metrics saved to %s", metrics_out)
    else:
        logger.warning("hyperbolic_volume column not found; skipping model fitting.")

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
