"""
Regression analysis module: baseline vs full model, VIF, coefficients.
Updated to match integration test expectations.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS

from code.utils.logging import AnalysisError, get_logger, log_duration
from code.config import PROC_DIR, ARTIFACT_DIR

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
VIF_THRESHOLD = 5.0  # Threshold for flagging multicollinearity

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_coupling_function_columns() -> List[str]:
    """
    Return list of coupling function column names.
    """
    return ["epsilon", "newell", "v_bs", "v_bt"]

def _prepare_features(
    df: pd.DataFrame,
    coupling_cols: List[str],
    composition_cols: List[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare feature matrices for baseline and full models and target series.

    Returns:
        X_base: baseline predictors (with constant)
        X_full: baseline + composition predictors (with constant)
        y_dst: Dst target
        y_kp:  Kp target
    """
    required = set(coupling_cols + composition_cols + ["Dst", "Kp"])
    missing = required - set(df.columns)
    if missing:
        raise AnalysisError(f"Missing required columns for regression: {missing}")

    # Drop rows with any NaNs in required columns
    clean_df = df.dropna(subset=list(required)).copy()

    X_base = clean_df[coupling_cols].copy()
    X_full = clean_df[coupling_cols + composition_cols].copy()

    # Add constant term
    X_base = sm.add_constant(X_base)
    X_full = sm.add_constant(X_full)

    y_dst = clean_df["Dst"]
    y_kp = clean_df["Kp"]

    return X_base, X_full, y_dst, y_kp

def _calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Variance Inflation Factor for each predictor (excluding the constant).
    Returns a DataFrame with columns ['feature', 'vif'].
    """
    vif_records = []
    cols = [c for c in X.columns if c != "const"]
    for col in cols:
        other_cols = [c for c in cols if c != col]
        y = X[col]
        X_other = X[other_cols]
        X_other = sm.add_constant(X_other, has_constant='add')
        model = OLS(y, X_other).fit()
        r2 = model.rsquared
        vif = np.inf if r2 == 1.0 else 1.0 / (1.0 - r2)
        vif_records.append({"feature": col, "vif": vif})
    return pd.DataFrame(vif_records)

def _fit_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
) -> Dict[str, Any]:
    """
    Fit an OLS model and return a dictionary with results.
    """
    if X.shape[0] < 10:
        raise AnalysisError(f"Not enough observations to fit {model_name}")

    model = OLS(y, X).fit()
    results = {
        "model_name": model_name,
        "coefficients": model.params.to_dict(),
        "pvalues": model.pvalues.to_dict(),
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "n_obs": int(model.nobs),
        "features_used": list(X.columns),
    }
    return results

@log_duration
def run_regression_analysis(
    data_path: str | None = None,
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """
    Load aligned data, fit baseline and full regression models for Dst and Kp,
    compute VIF, write artifacts, and return a summary dictionary.

    If ``data_path`` or ``output_dir`` are ``None``, defaults are taken from
    ``code.config`` (PROC_DIR / "aligned_hourly.parquet" and ARTIFACT_DIR).
    """
    # Resolve defaults
    if data_path is None:
        data_path = PROC_DIR / "aligned_hourly.parquet"
    if output_dir is None:
        output_dir = ARTIFACT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_parquet(data_path)

    coupling_cols = get_coupling_function_columns()
    composition_cols = ["O_Fe", "He_H", "C_O"]

    X_base, X_full, y_dst, y_kp = _prepare_features(df, coupling_cols, composition_cols)

    # Fit models
    baseline_dst = _fit_model(X_base, y_dst, "Baseline_Dst")
    full_dst = _fit_model(X_full, y_dst, "Full_Dst")
    baseline_kp = _fit_model(X_base, y_kp, "Baseline_Kp")
    full_kp = _fit_model(X_full, y_kp, "Full_Kp")

    # Compute VIF on baseline predictors (same for both targets)
    vif_df = _calculate_vif(X_base)
    vif_scores = {row["feature"]: row["vif"] for _, row in vif_df.iterrows()}
    high_vif_flags = {
        feat: (vif >= VIF_THRESHOLD) for feat, vif in vif_scores.items()
    }

    # Write baseline JSON
    baseline_path = output_dir / "baseline_regression_results.json"
    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "R2": baseline_dst["r_squared"],
                "adj_R2": baseline_dst["adj_r_squared"],
                "coefficients": baseline_dst["coefficients"],
                "pvalues": baseline_dst["pvalues"],
                "features_used": baseline_dst["features_used"],
            },
            f,
            indent=2,
        )

    # Write full JSON
    full_path = output_dir / "full_regression_results.json"
    with full_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "R2": full_dst["r_squared"],
                "adj_R2": full_dst["adj_r_squared"],
                "coefficients": full_dst["coefficients"],
                "pvalues": full_dst["pvalues"],
                "features_used": full_dst["features_used"],
                "delta_r2": full_dst["r_squared"] - baseline_dst["r_squared"],
            },
            f,
            indent=2,
        )

    # Write VIF results
    vif_path = output_dir / "vif_results.json"
    with vif_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"vif_scores": vif_scores, "high_vif_flags": high_vif_flags},
            f,
            indent=2,
        )

    logger.info(f"Regression artifacts written to {output_dir}")

    # Return a combined summary (useful for callers)
    return {
        "baseline_dst": baseline_dst,
        "full_dst": full_dst,
        "baseline_kp": baseline_kp,
        "full_kp": full_kp,
        "vif": vif_scores,
        "high_vif": high_vif_flags,
    }

def main() -> None:
    """
    Simple CLI entry point that runs the regression using default paths.
    """
    run_regression_analysis()

if __name__ == "__main__":
    main()
