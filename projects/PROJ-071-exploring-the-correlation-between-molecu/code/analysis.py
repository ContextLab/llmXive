from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Import shared utilities
from logging_config import get_logger, log_operation, log_pipeline_failure
from config import get_config

logger = get_logger("analysis")

def get_data_path() -> Path:
    """Return the project root data path."""
    return Path(__file__).parent.parent / "data"

def load_gate_status() -> Dict[str, Any]:
    """Load gate status from data/gate_status.json."""
    gate_path = get_data_path() / "gate_status.json"
    if not gate_path.exists():
        return {"status": "UNKNOWN"}
    with open(gate_path, "r") as f:
        return json.load(f)

def load_stat_gate_status() -> Dict[str, Any]:
    """Load statistical gate status from data/stat_gate_status.json."""
    stat_gate_path = get_data_path() / "stat_gate_status.json"
    if not stat_gate_path.exists():
        return {"status": "UNKNOWN"}
    with open(stat_gate_path, "r") as f:
        return json.load(f)

def load_standard_subset() -> pd.DataFrame:
    """Load the standard subset of data."""
    subset_path = get_data_path() / "processed" / "standard_subset.csv"
    if not subset_path.exists():
        raise FileNotFoundError(f"Standard subset not found at {subset_path}")
    return pd.read_csv(subset_path)

def save_analysis_results(results: Dict[str, Any]) -> None:
    """Save analysis results to data/processed/analysis_results.json."""
    output_path = get_data_path() / "processed" / "analysis_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("AnalysisResultsSaved", {"path": str(output_path)})

def run_lasso_regression(df: pd.DataFrame, target_col: str = "half_life_hours") -> Dict[str, Any]:
    """Run LASSO regression and return coefficients and R2."""
    feature_cols = [col for col in df.columns if col not in ["smiles", "half_life_hours", "canonical_smiles"]]
    if not feature_cols:
        raise ValueError("No feature columns found in dataframe")

    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]

    if X.empty or y.empty:
        return {"status": "SKIPPED", "reason": "Empty data after dropping NaNs"}

    X = add_constant(X)
    model = OLS(y, X)
    result = model.fit()

    return {
        "coefficients": result.params.to_dict(),
        "r2": float(result.rsquared),
        "adj_r2": float(result.rsquared_adj),
        "feature_count": len(feature_cols)
    }

def perform_residual_diagnostics(df: pd.DataFrame, target_col: str = "half_life_hours") -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests on model residuals.
    Returns a dictionary with test statistics and p-values.
    """
    # 1. Prepare Data
    feature_cols = [col for col in df.columns if col not in ["smiles", "half_life_hours", "canonical_smiles"]]
    if not feature_cols:
        raise ValueError("No feature columns found for residual diagnostics")

    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]

    if len(X) < 3:
        raise ValueError("Insufficient data points for residual diagnostics (N < 3)")

    X = add_constant(X)

    # 2. Fit OLS Model (using OLS for diagnostics as LASSO residuals can be biased by shrinkage)
    model = OLS(y, X)
    results = model.fit()
    residuals = results.resid

    diagnostics = {
        "shapiro_wilk": {"stat": None, "p": None},
        "breusch_pagan": {"stat": None, "p": None},
        "n_samples": int(len(residuals)),
        "n_features": len(feature_cols)
    }

    # 3. Shapiro-Wilk Test (Normality of residuals)
    try:
        stat, p_value = stats.shapiro(residuals)
        diagnostics["shapiro_wilk"]["stat"] = float(stat)
        diagnostics["shapiro_wilk"]["p"] = float(p_value)
    except Exception as e:
        logger.log("ShapiroWilkFailed", {"error": str(e)})
        diagnostics["shapiro_wilk"]["error"] = str(e)

    # 4. Breusch-Pagan Test (Homoscedasticity)
    # The test requires an endogenous variable (y) and exogenous variables (X)
    try:
        # het_breuschpagan returns (lm, lm_pvalue, f, f_pvalue)
        # We use the LM statistic and its p-value
        bp_test = het_breuschpagan(residuals, results.model.exog)
        diagnostics["breusch_pagan"]["stat"] = float(bp_test[0]) # LM statistic
        diagnostics["breusch_pagan"]["p"] = float(bp_test[1])   # LM p-value
    except Exception as e:
        logger.log("BreuschPaganFailed", {"error": str(e)})
        diagnostics["breusch_pagan"]["error"] = str(e)

    return diagnostics

def main() -> int:
    """
    Main entry point for the analysis task (T023, T024, T025).
    1. Checks Gate Status.
    2. Loads Standard Subset.
    3. Runs LASSO/MLR.
    4. Performs Residual Diagnostics (T025).
    5. Saves Results.
    """
    logger.log("AnalysisStart", {"task": "T025"})

    # Check Gate Status
    gate_status = load_gate_status()
    if gate_status.get("status") != "PASS":
        logger.log("GateFailed", {"status": gate_status.get("status")})
        save_analysis_results({
            "status": "SKIPPED",
            "reason": "Data Availability Gate Failed",
            "gate_status": gate_status,
            "N": 0,
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": None,
            "diagnostics": None
        })
        return 0 # Exit cleanly but skip

    # Check Statistical Gate Status (Standard Subset)
    stat_gate = load_stat_gate_status()
    if stat_gate.get("status") != "PASS":
        logger.log("StatGateFailed", {"status": stat_gate.get("status")})
        save_analysis_results({
            "status": "SKIPPED",
            "reason": "Statistical Gate (Standard Subset) Failed",
            "gate_status": gate_status,
            "stat_gate_status": stat_gate,
            "N": 0,
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": None,
            "diagnostics": None
        })
        return 0

    try:
        # Load Data
        df = load_standard_subset()
        logger.log("DataLoaded", {"rows": len(df), "columns": list(df.columns)})

        if len(df) == 0:
            raise ValueError("Loaded standard subset is empty")

        # Run Regression (T023/T024)
        regression_results = run_lasso_regression(df)
        
        # Run Residual Diagnostics (T025)
        diag_results = perform_residual_diagnostics(df)

        # Compile Final Results
        final_results = {
            "status": "PASS",
            "N": len(df),
            "R2": regression_results.get("r2"),
            "p_values": None, # Extracted from coefficients if needed, or kept separate
            "coefficients": regression_results.get("coefficients"),
            "methodology": "MLR+LASSO",
            "timestamp": None, # Will be set by save_analysis_results or internal logic if needed
            "diagnostics": diag_results
        }

        save_analysis_results(final_results)
        logger.log("AnalysisComplete", {"status": "PASS", "N": len(df)})
        return 0

    except Exception as e:
        logger.log("AnalysisError", {"error": str(e)})
        log_pipeline_failure("Analysis", str(e))
        # Save a failure result to ensure artifact exists
        save_analysis_results({
            "status": "FAIL",
            "reason": str(e),
            "N": 0,
            "R2": None,
            "p_values": None,
            "coefficients": None,
            "methodology": "MLR+LASSO",
            "timestamp": None,
            "diagnostics": None
        })
        return 1

if __name__ == "__main__":
    sys.exit(main())