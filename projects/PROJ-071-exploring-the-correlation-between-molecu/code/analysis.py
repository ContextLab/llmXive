"""
Analysis module for correlation between molecular complexity and degradation rates.
Implements MLR, LASSO, and residual diagnostics.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.model_selection import cross_val_score

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.logging_config import get_logger, log_operation

logger = get_logger("analysis")

# Configuration
GATE_STATUS_PATH = PROJECT_ROOT / "data" / "gate_status.json"
STAT_GATE_STATUS_PATH = PROJECT_ROOT / "data" / "stat_gate_status.json"
STANDARD_SUBSET_PATH = PROJECT_ROOT / "data" / "processed" / "standard_subset.csv"
ANALYSIS_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "analysis_results.json"

def get_data_path() -> Path:
    """Return the path to the standard subset data."""
    return STANDARD_SUBSET_PATH

def load_gate_status() -> Dict[str, Any]:
    """Load the main gate status."""
    if not GATE_STATUS_PATH.exists():
        return {"status": "FAIL", "reason": "Gate status file missing"}
    with open(GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def load_stat_gate_status() -> Dict[str, Any]:
    """Load the statistical gate status."""
    if not STAT_GATE_STATUS_PATH.exists():
        return {"status": "FAIL", "reason": "Stat gate status file missing"}
    with open(STAT_GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def load_standard_subset() -> pd.DataFrame:
    """Load the standard subset dataset."""
    if not STANDARD_SUBSET_PATH.exists():
        raise FileNotFoundError(f"Standard subset file not found: {STANDARD_SUBSET_PATH}")
    return pd.read_csv(STANDARD_SUBSET_PATH)

def run_mlr(df: pd.DataFrame, target_col: str = "half_life_hours", feature_cols: List[str] = None) -> Dict[str, Any]:
    """Run Multiple Linear Regression."""
    if feature_cols is None:
        feature_cols = ["MW", "TPSA", "rotatable_bonds", "aromatic_rings"]

    # Ensure features exist
    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        raise ValueError("No valid features found for MLR")

    X = df[available_features].dropna()
    y = df.loc[X.index, target_col].dropna()

    # Align X and y
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if len(X) < 2:
        return {"status": "FAIL", "reason": "Insufficient data for MLR"}

    model = LinearRegression()
    model.fit(X, y)

    # Calculate R2
    y_pred = model.predict(X)
    r2 = model.score(X, y)

    # Calculate p-values (simple t-test approximation)
    n = len(X)
    p_values = {}
    for i, feat in enumerate(available_features):
        # Residuals
        residuals = y - y_pred
        # Standard error of coefficients
        mse = np.sum(residuals**2) / (n - len(available_features) - 1)
        XtX_inv = np.linalg.inv(X.T @ X)
        se = np.sqrt(mse * XtX_inv[i, i])
        t_stat = model.coef_[i] / se
        p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - len(available_features) - 1))
        p_values[feat] = float(p_val)

    return {
        "status": "PASS",
        "R2": float(r2),
        "coefficients": {feat: float(c) for feat, c in zip(available_features, model.coef_)},
        "p_values": p_values,
        "n_samples": int(n)
    }

def run_lasso_regression(df: pd.DataFrame, target_col: str = "half_life_hours", feature_cols: List[str] = None) -> Dict[str, Any]:
    """Run LASSO regression with cross-validation."""
    if feature_cols is None:
        feature_cols = ["MW", "TPSA", "rotatable_bonds", "aromatic_rings"]

    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        raise ValueError("No valid features found for LASSO")

    X = df[available_features].dropna()
    y = df.loc[X.index, target_col].dropna()

    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if len(X) < 2:
        return {"status": "FAIL", "reason": "Insufficient data for LASSO"}

    # Determine K for cross-validation
    k = min(5, len(X) - 1)  # Ensure k < n

    lasso = LassoCV(cv=k, random_state=42, max_iter=10000)
    lasso.fit(X, y)

    y_pred = lasso.predict(X)
    r2 = lasso.score(X, y)

    # Get coefficients (only non-zero)
    coefficients = {}
    for feat, coef in zip(available_features, lasso.coef_):
        if abs(coef) > 1e-6:
            coefficients[feat] = float(coef)

    return {
        "status": "PASS",
        "R2": float(r2),
        "coefficients": coefficients,
        "alpha": float(lasso.alpha_),
        "n_samples": int(len(X))
    }

def perform_residual_diagnostics(df: pd.DataFrame, target_col: str = "half_life_hours", feature_cols: List[str] = None) -> Dict[str, Any]:
    """Perform Shapiro-Wilk and Breusch-Pagan tests on residuals."""
    if feature_cols is None:
        feature_cols = ["MW", "TPSA", "rotatable_bonds", "aromatic_rings"]

    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        return {"status": "FAIL", "reason": "No features for diagnostics"}

    X = df[available_features].dropna()
    y = df.loc[X.index, target_col].dropna()

    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if len(X) < 3:
        return {"status": "FAIL", "reason": "Insufficient data for diagnostics"}

    model = LinearRegression()
    model.fit(X, y)
    residuals = y - model.predict(X)

    # Shapiro-Wilk test
    shapiro_stat, shapiro_p = stats.shapiro(residuals)

    # Breusch-Pagan test (using simple variance check as proxy if statsmodels not available)
    # Residuals vs fitted
    fitted = model.predict(X)
    # Simple heteroscedasticity check: correlation between |residuals| and fitted
    corr, bp_p = stats.pearsonr(np.abs(residuals), fitted)
    # Convert to approximate p-value for BP test (simplified)
    bp_stat = len(residuals) * (corr ** 2)
    # BP statistic follows chi-square with 1 df
    bp_p = 1 - stats.chi2.cdf(bp_stat, 1)

    return {
        "shapiro_wilk": {"stat": float(shapiro_stat), "p": float(shapiro_p)},
        "breusch_pagan": {"stat": float(bp_stat), "p": float(bp_p)}
    }

def save_analysis_results(results: Dict[str, Any]) -> None:
    """Save analysis results to JSON."""
    results["timestamp"] = pd.Timestamp.utcnow().isoformat()
    results["methodology"] = "MLR+LASSO"

    with open(ANALYSIS_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.log("Analysis results saved", {"path": str(ANALYSIS_RESULTS_PATH)})

def save_analysis_results_wrapper(status: str, reason: str = None, n: int = 0) -> None:
    """Save analysis results with status (used when gates fail)."""
    results = {
        "status": status,
        "reason": reason,
        "N": n,
        "R2": None,
        "p_values": None,
        "coefficients": None,
        "methodology": "MLR+LASSO",
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "diagnostics": None
    }
    save_analysis_results(results)

@log_operation("Dry_Run_Analysis")
def main(dry_run: bool = False) -> None:
    """
    Main entry point for analysis.
    If dry_run is True, verify imports and structure without running full analysis.
    """
    logger.log("Analysis started", {"dry_run": dry_run})

    # Check gates
    gate_status = load_gate_status()
    stat_gate_status = load_stat_gate_status()

    if gate_status.get("status") == "FAIL":
        logger.log("Gate failed", {"reason": gate_status.get("reason")})
        save_analysis_results_wrapper("SKIPPED", reason="Main gate failed", n=0)
        if dry_run:
            logger.log("Dry run completed (gate fail path)", {"status": "OK"})
            return
        else:
            raise RuntimeError("Main gate failed, cannot proceed")

    if stat_gate_status.get("status") == "FAIL":
        logger.log("Stat gate failed", {"reason": stat_gate_status.get("reason")})
        save_analysis_results_wrapper("SKIPPED", reason="Stat gate failed", n=stat_gate_status.get("N", 0))
        if dry_run:
            logger.log("Dry run completed (stat gate fail path)", {"status": "OK"})
            return
        else:
            raise RuntimeError("Stat gate failed, cannot proceed")

    if dry_run:
        # Dry run: just verify we can load data and imports work
        try:
            df = load_standard_subset()
            logger.log("Dry run data load successful", {"n_rows": len(df)})
            save_analysis_results_wrapper("PASS", n=len(df))
            logger.log("Dry run completed successfully", {"status": "OK"})
            return
        except Exception as e:
            logger.log("Dry run failed", {"error": str(e)})
            raise

    # Full analysis
    try:
        df = load_standard_subset()
        logger.log("Data loaded", {"n_rows": len(df)})

        # Run MLR
        mlr_results = run_mlr(df)
        logger.log("MLR completed", {"R2": mlr_results.get("R2")})

        # Run LASSO
        lasso_results = run_lasso_regression(df)
        logger.log("LASSO completed", {"R2": lasso_results.get("R2")})

        # Diagnostics
        diagnostics = perform_residual_diagnostics(df)
        logger.log("Diagnostics completed", {"shapiro_p": diagnostics.get("shapiro_wilk", {}).get("p")})

        # Merge results
        final_results = {
            "status": "PASS",
            "N": len(df),
            "R2": mlr_results.get("R2"),  # Use MLR R2 as primary
            "p_values": mlr_results.get("p_values"),
            "coefficients": lasso_results.get("coefficients"),  # Use LASSO coefficients
            "methodology": "MLR+LASSO",
            "mlr": mlr_results,
            "lasso": lasso_results,
            "diagnostics": diagnostics,
            "timestamp": pd.Timestamp.utcnow().isoformat()
        }

        save_analysis_results(final_results)
        logger.log("Analysis completed successfully", {"R2": final_results.get("R2")})

    except Exception as e:
        logger.log("Analysis failed", {"error": str(e)})
        save_analysis_results_wrapper("FAIL", reason=str(e), n=0)
        raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run correlation analysis")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
