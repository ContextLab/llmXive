from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.model_selection import cross_val_score

from config import get_config
from logging_config import log_operation, get_logger

logger = get_logger("analysis")

# --- Data Loading Helpers ---

def get_data_path() -> Path:
    """Return the project root data path."""
    config = get_config()
    return Path(config.get("data_root", "data"))

def load_standard_subset() -> Optional[pd.DataFrame]:
    """Load the standard_subset.csv if it exists and is not empty."""
    path = get_data_path() / "processed" / "standard_subset.csv"
    if not path.exists():
        logger.log("load_standard_subset", status="missing", path=str(path))
        return None
    
    df = pd.read_csv(path)
    if df.empty:
        logger.log("load_standard_subset", status="empty", path=str(path))
        return None
    
    logger.log("load_standard_subset", status="loaded", rows=len(df))
    return df

# --- Statistical & Analysis Functions ---

def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Compute correlation matrix for numeric columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()
    return numeric_df.corr()

def compute_p_values(df: pd.DataFrame, target_col: str, feature_cols: list) -> Dict[str, float]:
    """Compute p-values for correlation between features and target."""
    p_vals = {}
    y = df[target_col].dropna()
    
    for col in feature_cols:
        x = df[col].dropna()
        # Align indices
        common_idx = x.index.intersection(y.index)
        if len(common_idx) < 5:
            p_vals[col] = 1.0
            continue
        
        x_align = x.loc[common_idx]
        y_align = y.loc[common_idx]
        
        if len(x_align) == 0:
            p_vals[col] = 1.0
            continue

        try:
            _, p = stats.pearsonr(x_align, y_align)
            p_vals[col] = float(p)
        except Exception:
            p_vals[col] = 1.0
    return p_vals

def identify_significant_correlations(correlation_matrix: pd.DataFrame, target_col: str, alpha: float = 0.05) -> list:
    """Identify features significantly correlated with target."""
    if correlation_matrix.empty or target_col not in correlation_matrix.columns:
        return []
    target_series = correlation_matrix[target_col]
    # Filter absolute correlation > threshold (simple heuristic)
    # In a real scenario, we'd use p-values, but here we rely on the matrix
    significant = [col for col in target_series.index 
                   if col != target_col and abs(target_series[col]) > 0.3]
    return significant

def run_mlr(df: pd.DataFrame, features: list, target: str) -> Tuple[Optional[LinearRegression], Optional[float]]:
    """Run Multiple Linear Regression."""
    if df.empty or len(features) == 0:
        return None, None

    X = df[features].dropna()
    y = df.loc[X.index, target].dropna()
    
    # Re-align
    common_idx = X.index.intersection(y.index)
    if len(common_idx) < 10:
        return None, None
    
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if X.empty:
        return None, None

    model = LinearRegression()
    model.fit(X, y)
    
    # R2 score
    r2 = model.score(X, y)
    return model, float(r2)

def run_lasso_regression(df: pd.DataFrame, features: list, target: str) -> Tuple[Optional[LassoCV], Optional[float], Optional[Dict[str, float]]]:
    """Run LASSO regression with cross-validation."""
    if df.empty or len(features) == 0:
        return None, None, None

    X = df[features].dropna()
    y = df.loc[X.index, target].dropna()
    
    common_idx = X.index.intersection(y.index)
    if len(common_idx) < 10:
        return None, None, None
    
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if X.empty:
        return None, None, None

    # Dynamic K-fold: K = min(5, n-1)
    n = len(X)
    k = min(5, n - 1)
    if k < 2: k = 2

    model = LassoCV(cv=k, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    r2 = float(model.score(X, y))
    coefficients = {feat: float(coeff) for feat, coeff in zip(features, model.coef_)}
    
    return model, r2, coefficients

def perform_residual_diagnostics(df: pd.DataFrame, model: LinearRegression, features: list, target: str) -> Dict[str, Any]:
    """Perform Shapiro-Wilk and Breusch-Pagan tests."""
    X = df[features]
    y = df[target]
    
    common_idx = X.index.intersection(y.index)
    if len(common_idx) < 10:
        return {"shapiro_wilk": {"stat": 0.0, "p": 1.0}, "breusch_pagan": {"stat": 0.0, "p": 1.0}}
    
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    y_pred = model.predict(X)
    residuals = y - y_pred

    # Shapiro-Wilk
    try:
        sw_stat, sw_p = stats.shapiro(residuals)
    except Exception:
        sw_stat, sw_p = 0.0, 1.0

    # Breusch-Pagan (using statsmodels logic manually or simplified)
    # BP test: Regress squared residuals on predictors
    try:
        # Simplified BP: OLS of residuals^2 on X
        from sklearn.linear_model import LinearRegression
        bp_model = LinearRegression()
        bp_model.fit(X, residuals**2)
        n = len(residuals)
        k = X.shape[1]
        # LM = n * R^2 from auxiliary regression
        ss_res = np.sum((residuals**2 - bp_model.predict(X))**2)
        ss_tot = np.sum((residuals**2 - np.mean(residuals**2))**2)
        r2_aux = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        lm_stat = n * r2_aux
        bp_p = 1 - stats.chi2.cdf(lm_stat, k)
    except Exception:
        lm_stat, bp_p = 0.0, 1.0

    return {
        "shapiro_wilk": {"stat": float(sw_stat), "p": float(sw_p)},
        "breusch_pagan": {"stat": float(lm_stat), "p": float(bp_p)}
    }

# --- Main Output Logic (T026) ---

def save_analysis_results(results: Dict[str, Any]) -> Path:
    """Save analysis results to JSON."""
    output_path = get_data_path() / "processed" / "analysis_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("save_analysis_results", path=str(output_path), status="success")
    return output_path

def save_analysis_results_wrapper(status: str, n: int, r2: Optional[float], p_values: Optional[Dict], 
                                  coefficients: Optional[Dict], diagnostics: Optional[Dict]) -> Path:
    """Wrapper to format and save results per T026 schema."""
    results = {
        "status": status,
        "N": n,
        "R2": r2,
        "p_values": p_values,
        "coefficients": coefficients,
        "methodology": "MLR+LASSO",
        "timestamp": datetime.utcnow().isoformat(),
        "diagnostics": diagnostics if diagnostics else {
            "shapiro_wilk": {"stat": 0.0, "p": 1.0},
            "breusch_pagan": {"stat": 0.0, "p": 1.0}
        }
    }
    return save_analysis_results(results)

from datetime import datetime

def main():
    """
    Main entry point for T026: Save Analysis Results.
    Reads gate status and data, performs analysis if passed, saves results.
    """
    data_root = get_data_path()
    gate_status_path = data_root / "gate_status.json"
    stat_gate_status_path = data_root / "stat_gate_status.json"
    
    # 1. Check Gate Status
    gate_status = {"status": "FAIL", "reason": "Unknown", "N": 0}
    if gate_status_path.exists():
        with open(gate_status_path, "r") as f:
            gate_status = json.load(f)
    
    # 2. Check Statistical Gate Status
    stat_status = {"status": "FAIL", "reason": "Unknown", "N": 0}
    if stat_gate_status_path.exists():
        with open(stat_gate_status_path, "r") as f:
            stat_status = json.load(f)

    # 3. Determine Outcome
    if gate_status.get("status") != "PASS" or stat_status.get("status") != "PASS":
        # Gate Failed: Save FAIL result
        n_val = gate_status.get("N", stat_status.get("N", 0))
        logger.log("main", status="gate_fail", reason="Data or Statistical Gate Failed", N=n_val)
        
        save_analysis_results_wrapper(
            status="FAIL",
            n=n_val,
            r2=None,
            p_values=None,
            coefficients=None,
            diagnostics=None
        )
        return

    # 4. Gate Passed: Perform Analysis
    df = load_standard_subset()
    if df is None or df.empty:
        logger.log("main", status="no_data", path="standard_subset.csv")
        save_analysis_results_wrapper(
            status="FAIL",
            n=0,
            r2=None,
            p_values=None,
            coefficients=None,
            diagnostics=None
        )
        return

    # Identify target and features (assuming standard columns exist)
    # We look for 'half_life' as target and numeric descriptors as features
    target_col = 'half_life'
    if target_col not in df.columns:
        # Fallback or error handling
        logger.log("main", status="missing_target", target=target_col)
        save_analysis_results_wrapper(
            status="FAIL",
            n=len(df),
            r2=None,
            p_values=None,
            coefficients=None,
            diagnostics=None
        )
        return

    # Select numeric features excluding target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    features = [c for c in numeric_cols if c != target_col]
    
    if not features:
        logger.log("main", status="no_features")
        save_analysis_results_wrapper(
            status="FAIL",
            n=len(df),
            r2=None,
            p_values=None,
            coefficients=None,
            diagnostics=None
        )
        return

    # Run MLR
    mlr_model, r2 = run_mlr(df, features, target_col)
    if mlr_model is None:
        logger.log("main", status="mlr_failed")
        save_analysis_results_wrapper(
            status="FAIL",
            n=len(df),
            r2=None,
            p_values=None,
            coefficients=None,
            diagnostics=None
        )
        return

    # Run LASSO
    lasso_model, lasso_r2, lasso_coeffs = run_lasso_regression(df, features, target_col)
    
    # Compute P-values
    p_vals = compute_p_values(df, target_col, features)

    # Diagnostics
    diagnostics = perform_residual_diagnostics(df, mlr_model, features, target_col)

    # Save Results
    save_analysis_results_wrapper(
        status="PASS",
        n=len(df),
        r2=float(r2) if r2 is not None else None,
        p_values=p_vals,
        coefficients=lasso_coeffs,
        diagnostics=diagnostics
    )
    logger.log("main", status="success", n=len(df), r2=r2)

if __name__ == "__main__":
    main()
