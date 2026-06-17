"""
Regression analysis module (extended for Task T036).

In addition to the existing regression‑model fitting utilities, this file now
provides functions to compute Pearson and Spearman correlation coefficients
together with their effect‑size measures (Cohen's *d* and the correlation
coefficient *r*).  All p‑values are deliberately omitted and replaced with the
sentinel string ``"not applicable for census data"`` as required by FR‑006 and
Constitution Principle VII.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation

# ----------------------------------------------------------------------
# Helper functions (unchanged from the original implementation)
# ----------------------------------------------------------------------
def _prepare_design_matrix(
    df: pd.DataFrame, predictor: str, degree: int = 1
) -> Tuple[pd.DataFrame, pd.Series]:
    # Coerce predictor + response to numeric and drop non-finite rows
    # (complete-case regression): some knots have non-numeric/absent invariants
    # (e.g. volume == "Not Hyperbolic"), which become NaN and would otherwise
    # raise statsmodels MissingDataError ("exog contains inf or nans").
    work = df[[predictor, "volume"]].apply(pd.to_numeric, errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna()
    y = work["volume"]
    if degree == 1:
        X = sm.add_constant(work[[predictor]])
    else:
        poly_terms = {
            f"{predictor}^{i}": work[predictor] ** i for i in range(1, degree + 1)
        }
        X = sm.add_constant(pd.DataFrame(poly_terms, index=work.index))
    return X, y

def _fit_model(
    X: pd.DataFrame, y: pd.Series
) -> sm.regression.linear_model.RegressionResultsWrapper:
    model = sm.OLS(y, X)
    return model.fit()

def _compute_goodness_of_fit(
    result: sm.regression.linear_model.RegressionResultsWrapper, y: pd.Series
) -> Dict[str, float]:
    predictions = result.predict()
    residuals = y - predictions
    ss_res = (residuals ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else float("nan")
    mae = residuals.abs().mean()
    aic = result.aic
    bic = result.bic
    return {"R2": r2, "AIC": aic, "BIC": bic, "MAE": mae}

# ----------------------------------------------------------------------
# New correlation utilities (Task T036)
# ----------------------------------------------------------------------
def _cohens_d_from_r(r: float) -> float:
    """
    Convert a Pearson correlation coefficient ``r`` to Cohen's d.
    The formula d = 2r / sqrt(1 - r^2) is standard for effect size conversion.
    """
    if abs(r) >= 1.0:
        # Avoid division by zero; return an arbitrarily large effect size.
        return float("inf")
    return 2 * r / math.sqrt(1 - r ** 2)

def compute_correlations() -> Dict[str, Dict[str, str | float]]:
    """
    Compute Pearson and Spearman correlation coefficients between
    ``crossing_number`` and ``volume`` (the primary invariants used in the
    regression analysis).  For each correlation we also calculate Cohen's d
    (derived from Pearson's r) and report the correlation coefficient itself.
    P‑values are deliberately omitted and replaced with a fixed string.

    Returns
    -------
    dict
        Mapping of correlation type to a dictionary containing:
        * ``r`` – Pearson’s correlation coefficient (float)
        * ``spearman`` – Spearman’s rho (float)
        * ``cohens_d`` – Effect size derived from Pearson’s r (float)
        * ``p_value`` – Fixed sentinel string.
    """
    logger = get_logger(__name__)
    logger.info("Computing Pearson and Spearman correlations")
    df = load_cleaned_knots()

    # Ensure required columns exist
    required = {"crossing_number", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for correlation analysis: {missing}")

    x = df["crossing_number"]
    y = df["volume"]

    # Pearson
    pearson_r, _ = stats.pearsonr(x, y)
    # Spearman
    spearman_rho, _ = stats.spearmanr(x, y)

    # Effect size
    cohens_d = _cohens_d_from_r(pearson_r)

    result = {
        "pearson": {
            "r": pearson_r,
            "cohens_d": cohens_d,
            "p_value": "not applicable for census data",
        },
        "spearman": {
            "rho": spearman_rho,
            "p_value": "not applicable for census data",
        },
    }
    logger.debug("Correlation results", result)
    return result

# ----------------------------------------------------------------------
# Core regression analysis (unchanged)
# ----------------------------------------------------------------------
def run_regression_analysis() -> Dict[str, Dict[str, float]]:
    logger = get_logger(__name__)
    logger.info("Loading cleaned knot data for regression analysis")
    df = load_cleaned_knots()

    required = {"crossing_number", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for regression: {missing}")

    # Linear model
    X_lin, y = _prepare_design_matrix(df, "crossing_number", degree=1)
    lin_res = _fit_model(X_lin, y)
    lin_metrics = _compute_goodness_of_fit(lin_res, y)

    # Quadratic model
    X_quad, _ = _prepare_design_matrix(df, "crossing_number", degree=2)
    quad_res = _fit_model(X_quad, y)
    quad_metrics = _compute_goodness_of_fit(quad_res, y)

    # Log‑linear model
    df = df.copy()
    df["log_crossing"] = df["crossing_number"].apply(
        lambda x: math.log(x) if x > 0 else 0
    )
    X_log, _ = _prepare_design_matrix(df, "log_crossing", degree=1)
    log_res = _fit_model(X_log, y)
    log_metrics = _compute_goodness_of_fit(log_res, y)

    all_metrics = {
        "linear": lin_metrics,
        "quadratic": quad_metrics,
        "log_linear": log_metrics,
    }

    logger.info("Regression analysis completed")
    return all_metrics

# ----------------------------------------------------------------------
# Reporting utilities
# ----------------------------------------------------------------------
def generate_report(metrics: Dict[str, Dict[str, float]]) -> str:
    lines = ["Regression Goodness‑of‑Fit Summary", "=" * 35, ""]
    for name, vals in metrics.items():
        lines.append(f"Model: {name}")
        for metric, value in vals.items():
            lines.append(f"  {metric}: {value:.4f}")
        lines.append("")
    return "\n".join(lines)

def generate_correlation_report(corr: Dict[str, Dict[str, str | float]]) -> str:
    """
    Produce a short, human‑readable report of the correlation analysis.
    """
    lines = ["Correlation Summary", "=" * 20, ""]
    pearson = corr["pearson"]
    spearman = corr["spearman"]
    lines.append("Pearson correlation:")
    lines.append(f"  r = {pearson['r']:.4f}")
    lines.append(f"  Cohen's d = {pearson['cohens_d']:.4f}")
    lines.append(f"  p‑value = {pearson['p_value']}")
    lines.append("")
    lines.append("Spearman correlation:")
    lines.append(f"  rho = {spearman['rho']:.4f}")
    lines.append(f"  p‑value = {spearman['p_value']}")
    return "\n".join(lines)

# ----------------------------------------------------------------------
# Main entry point (used by quick‑start)
# ----------------------------------------------------------------------
def main() -> None:
    logger = get_logger(__name__)
    log_operation("regression_start", parameters={})

    # 1. Regression analysis
    reg_metrics = run_regression_analysis()
    reg_output_path = Path("data/plots/regression_metrics.json")
    reg_output_path.parent.mkdir(parents=True, exist_ok=True)
    with reg_output_path.open("w", encoding="utf-8") as f:
        json.dump(reg_metrics, f, indent=2)

    # 2. Correlation analysis (Task T036)
    corr_metrics = compute_correlations()
    corr_output_path = Path("data/plots/correlation_metrics.json")
    corr_output_path.parent.mkdir(parents=True, exist_ok=True)
    with corr_output_path.open("w", encoding="utf-8") as f:
        json.dump(corr_metrics, f, indent=2)

    # Print human‑readable reports
    print(generate_report(reg_metrics))
    print()
    print(generate_correlation_report(corr_metrics))

    log_operation(
        "regression_complete",
        output_file=str(reg_output_path),
        parameters={"metrics": reg_metrics},
        status="completed",
    )
    log_operation(
        "correlation_complete",
        output_file=str(corr_output_path),
        parameters={"metrics": corr_metrics},
        status="completed",
    )

if __name__ == "__main__":
    main()
