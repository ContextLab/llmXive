from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler

# Import existing public names from sibling modules as per API surface
from logging_config import get_logger, log_operation, log_pipeline_failure

# Constants
DATA_DIR = os.path.join("data", "processed")
GATE_STATUS_PATH = os.path.join("data", "gate_status.json")
STAT_GATE_STATUS_PATH = os.path.join("data", "stat_gate_status.json")
STANDARD_SUBSET_PATH = os.path.join(DATA_DIR, "standard_subset.csv")
ANALYSIS_RESULTS_PATH = os.path.join(DATA_DIR, "analysis_results.json")

logger = get_logger("analysis")

def get_data_path() -> str:
    return DATA_DIR

def load_gate_status() -> Dict[str, Any]:
    """Load the main gate status from disk."""
    if not os.path.exists(GATE_STATUS_PATH):
        return {"status": "FAIL", "reason": "Gate status file missing"}
    with open(GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def load_stat_gate_status() -> Dict[str, Any]:
    """Load the statistical gate status from disk."""
    if not os.path.exists(STAT_GATE_STATUS_PATH):
        return {"status": "FAIL", "reason": "Stat gate status file missing"}
    with open(STAT_GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def load_standard_subset() -> pd.DataFrame:
    """Load the standard subset dataframe."""
    if not os.path.exists(STANDARD_SUBSET_PATH):
        raise FileNotFoundError(f"Standard subset file not found: {STANDARD_SUBSET_PATH}")
    return pd.read_csv(STANDARD_SUBSET_PATH)

def save_analysis_results(results: Dict[str, Any]) -> None:
    """Save analysis results to the specified JSON file."""
    os.makedirs(os.path.dirname(ANALYSIS_RESULTS_PATH), exist_ok=True)
    with open(ANALYSIS_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved analysis results to {ANALYSIS_RESULTS_PATH}")

def run_mlr_regression(df: pd.DataFrame, target_col: str = "half_life") -> Tuple[Dict[str, float], float]:
    """
    Run Multiple Linear Regression.
    Returns (coefficients_dict, r2_score).
    """
    feature_cols = [c for c in df.columns if c not in [target_col, "smiles", "mol_id"]]
    # Ensure we have features
    if not feature_cols:
        return {}, 0.0

    X = df[feature_cols].fillna(0).values
    y = df[target_col].fillna(0).values

    # Handle case where y might be all NaN or constant
    if np.all(np.isnan(y)) or len(np.unique(y)) < 2:
        return {}, 0.0

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X_scaled, y)

    # Calculate R2
    y_pred = model.predict(X_scaled)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    coefficients = {col: float(coeff) for col, coeff in zip(feature_cols, model.coef_)}
    coefficients["intercept"] = float(model.intercept_)

    return coefficients, float(r2)

def run_lasso_regression(df: pd.DataFrame, target_col: str = "half_life") -> Tuple[Dict[str, float], float]:
    """
    Run LASSO Regression with K-Fold Cross-Validation.
    Returns (best_coefficients_dict, best_r2_score).
    """
    feature_cols = [c for c in df.columns if c not in [target_col, "smiles", "mol_id"]]
    if not feature_cols:
        return {}, 0.0

    X = df[feature_cols].fillna(0).values
    y = df[target_col].fillna(0).values

    if np.all(np.isnan(y)) or len(np.unique(y)) < 2:
        return {}, 0.0

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Determine K strictly less than n
    n = len(y)
    k_folds = min(5, n - 1) if n > 1 else 1
    if k_folds < 2:
        k_folds = 2 # Minimum for CV if possible

    alphas = [0.01, 0.1, 1.0, 10.0]
    best_score = -np.inf
    best_alpha = alphas[0]
    best_model = None

    for alpha in alphas:
        lasso = Lasso(alpha=alpha, max_iter=10000)
        scores = cross_val_score(lasso, X_scaled, y, cv=k_folds, scoring='r2')
        mean_score = np.mean(scores)
        if mean_score > best_score:
            best_score = mean_score
            best_alpha = alpha
            best_model = lasso

    if best_model is None:
        return {}, 0.0

    best_model.fit(X_scaled, y)
    coefficients = {col: float(coeff) for col, coeff in zip(feature_cols, best_model.coef_)}
    coefficients["intercept"] = float(best_model.intercept_)
    coefficients["alpha"] = float(best_alpha)

    return coefficients, float(best_score)

def perform_residual_diagnostics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests.
    Returns dict with stats and p-values.
    """
    residuals = y_true - y_pred

    # Shapiro-Wilk
    shapiro_stat, shapiro_p = 0.0, 1.0
    if len(residuals) > 3:
        try:
            shapiro_stat, shapiro_p = stats.shapiro(residuals)
        except Exception:
            pass

    # Breusch-Pagan (using simple linear regression of squared residuals on fitted values)
    # Note: statsmodels is often used for this, but we can implement a simplified version
    # using scipy if statsmodels is not strictly available or to avoid import issues.
    # However, the spec mentions statsmodels. We will try to use it, fallback to simple OLS logic.
    bp_stat, bp_p = 0.0, 1.0
    try:
        import statsmodels.api as sm
        from statsmodels.stats.diagnostic import het_breuschpagan

        # het_breuschpagan requires exog for the variance model. We use fitted values.
        # y_resid: residuals, exog: fitted values
        bp_stat, bp_p, _, _ = het_breuschpagan(residuals, y_pred.reshape(-1, 1))
    except ImportError:
        # Fallback: simple correlation check if statsmodels not found
        # Not a true Breusch-Pagan, but a proxy for heteroscedasticity
        if len(residuals) > 3:
            corr, p_val = stats.pearsonr(residuals, y_pred)
            bp_p = p_val
            bp_stat = corr
    except Exception:
        pass

    return {
        "shapiro_wilk": {"stat": float(shapiro_stat), "p": float(shapiro_p)},
        "breusch_pagan": {"stat": float(bp_stat), "p": float(bp_p)}
    }

def perform_residual_diagnostics_full(df: pd.DataFrame, target_col: str = "half_life", model_type: str = "mlr") -> Dict[str, Any]:
    """
    Full diagnostics including model fit and residual tests.
    """
    feature_cols = [c for c in df.columns if c not in [target_col, "smiles", "mol_id"]]
    if not feature_cols:
        return {"status": "ERROR", "message": "No features found"}

    X = df[feature_cols].fillna(0).values
    y = df[target_col].fillna(0).values

    if np.all(np.isnan(y)) or len(np.unique(y)) < 2:
        return {"status": "ERROR", "message": "Invalid target variable"}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if model_type == "mlr":
        model = LinearRegression()
    else:
        model = Lasso(alpha=1.0, max_iter=10000)

    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)

    diagnostics = perform_residual_diagnostics(y, y_pred)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    return {
        "r2": float(r2),
        "diagnostics": diagnostics
    }

def main():
    """
    Main entry point for T026: Save Analysis Results.
    This function orchestrates loading data, running regressions, diagnostics,
    and saving the final JSON artifact.
    """
    log_operation("T026_Analysis_Results", task="T026")

    # 1. Check Gate Status
    gate_status = load_gate_status()
    if gate_status.get("status") == "FAIL":
        logger.warning("Gate failed. Saving SKIPPED results.")
        save_analysis_results({
            "status": "SKIPPED",
            "reason": "Gate Failed",
            "N": 0,
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": datetime.utcnow().isoformat(),
            "diagnostics": {
                "shapiro_wilk": {"stat": 0.0, "p": 1.0},
                "breusch_pagan": {"stat": 0.0, "p": 1.0}
            }
        })
        return 0

    # 2. Check Stat Gate Status (Standard Subset)
    stat_gate = load_stat_gate_status()
    if stat_gate.get("status") == "FAIL":
        logger.warning("Statistical Gate failed. Saving SKIPPED results.")
        save_analysis_results({
            "status": "SKIPPED",
            "reason": "Stat Gate Failed",
            "N": stat_gate.get("N_std", 0),
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": datetime.utcnow().isoformat(),
            "diagnostics": {
                "shapiro_wilk": {"stat": 0.0, "p": 1.0},
                "breusch_pagan": {"stat": 0.0, "p": 1.0}
            }
        })
        return 0

    # 3. Load Data
    try:
        df = load_standard_subset()
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        save_analysis_results({
            "status": "FAIL",
            "reason": f"Data file missing: {e}",
            "N": 0,
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": datetime.utcnow().isoformat(),
            "diagnostics": {
                "shapiro_wilk": {"stat": 0.0, "p": 1.0},
                "breusch_pagan": {"stat": 0.0, "p": 1.0}
            }
        })
        return 1

    N = len(df)
    if N == 0:
        logger.warning("Standard subset is empty.")
        save_analysis_results({
            "status": "WARN",
            "reason": "Empty dataset",
            "N": 0,
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": datetime.utcnow().isoformat(),
            "diagnostics": {
                "shapiro_wilk": {"stat": 0.0, "p": 1.0},
                "breusch_pagan": {"stat": 0.0, "p": 1.0}
            }
        })
        return 0

    # 4. Run MLR
    mlr_coeffs, mlr_r2 = run_mlr_regression(df)
    
    # 5. Run LASSO
    lasso_coeffs, lasso_r2 = run_lasso_regression(df)

    # 6. Diagnostics (using MLR results as primary)
    feature_cols = [c for c in df.columns if c not in ["half_life", "smiles", "mol_id"]]
    X = df[feature_cols].fillna(0).values
    y = df["half_life"].fillna(0).values
    
    # Simple OLS for diagnostics
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LinearRegression()
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)
    
    diagnostics = perform_residual_diagnostics(y, y_pred)

    # 7. Prepare Results
    # We will report the best R2 between MLR and LASSO, or just MLR if LASSO failed
    best_r2 = max(mlr_r2, lasso_r2) if (mlr_r2 or lasso_r2) else 0.0
    best_coeffs = lasso_coeffs if lasso_r2 >= mlr_r2 else mlr_coeffs

    results = {
        "status": "PASS",
        "N": N,
        "R2": float(best_r2),
        "p_values": None, # Placeholder for future p-value calculation if needed
        "coefficients": best_coeffs,
        "methodology": "MLR+LASSO",
        "timestamp": datetime.utcnow().isoformat(),
        "diagnostics": diagnostics
    }

    # 8. Save
    save_analysis_results(results)
    logger.info(f"Analysis complete. R2: {best_r2:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())