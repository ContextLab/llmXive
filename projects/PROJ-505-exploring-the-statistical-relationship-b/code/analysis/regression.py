"""
Regression analysis module: baseline vs full model, VIF, coefficients.
Provides utilities required by the unit and integration tests.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS

# Updated import path
from code.utils.logging import AnalysisError, get_logger, log_duration

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
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    """
    Prepare feature matrices for baseline and full models and target series.

    Returns:
        X_base: baseline predictors (with constant)
        X_full: baseline + composition predictors (with constant)
        y_dst: Dst target
        y_kp:  Kp target
        clean_df: dataframe after dropping rows with any NaNs in used columns
    """
    required = set(coupling_cols + composition_cols + ["Dst", "Kp"])
    missing = required - set(df.columns)
    if missing:
        raise AnalysisError(f"Missing required columns for regression: {missing}")

    # Drop rows with NaNs in any of the needed columns
    clean_df = df.dropna(subset=list(required)).copy()

    X_base = clean_df[coupling_cols].copy()
    X_full = clean_df[coupling_cols + composition_cols].copy()

    # Add constant term
    X_base = sm.add_constant(X_base)
    X_full = sm.add_constant(X_full)

    y_dst = clean_df["Dst"]
    y_kp = clean_df["Kp"]

    return X_base, X_full, y_dst, y_kp, clean_df


def _calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Variance Inflation Factor for each predictor (excluding the constant).
    Returns a DataFrame with columns ['feature', 'vif'].
    """
    vif_data = []
    cols = [c for c in X.columns if c != "const"]
    for col in cols:
        other_cols = [c for c in cols if c != col]
        y = X[col]
        X_other = X[other_cols]
        X_other = sm.add_constant(X_other, has_constant='add')
        model = OLS(y, X_other).fit()
        r2 = model.rsquared
        vif = 1.0 / (1.0 - r2) if r2 < 1.0 else np.inf
        vif_data.append({"feature": col, "vif": vif})
    return pd.DataFrame(vif_data)


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
    }
    return results


def _check_multicollinearity(
    vif_records: List[Dict[str, Any]],
    model_name: str,
    output_dir: Path,
) -> None:
    """
    Write a warning artifact if any VIF exceeds the threshold.
    """
    high_vif = [rec for rec in vif_records if rec["vif"] >= VIF_THRESHOLD]
    if not high_vif:
        return

    warning_path = output_dir / f"vif_warning_{model_name}.json"
    warning_content = {
        "highly_collinear_features": high_vif,
        "threshold": VIF_THRESHOLD,
    }
    with open(warning_path, "w", encoding="utf-8") as f:
        json.dump(warning_content, f, indent=2)
    logger.warning(f"High VIF detected for {model_name}; warning written to {warning_path}")


@log_duration
def run_regression_analysis(
    data_path: str,
    output_dir: str,
) -> Dict[str, Any]:
    """
    Load aligned data, fit baseline and full regression models for Dst and Kp,
    compute VIF, write artifacts, and return a summary dictionary.

    Expected output files:
        - regression_results.json
        - regression_coefficients.csv
        - (optional) vif_warning_<model>.json
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_parquet(data_path)

    coupling_cols = get_coupling_function_columns()
    composition_cols = ["O_Fe", "He_H", "C_O"]

    X_base, X_full, y_dst, y_kp, _ = _prepare_features(df, coupling_cols, composition_cols)

    # Fit models
    baseline_dst = _fit_model(X_base, y_dst, "Baseline_Dst")
    full_dst = _fit_model(X_full, y_dst, "Full_Dst")
    baseline_kp = _fit_model(X_base, y_kp, "Baseline_Kp")
    full_kp = _fit_model(X_full, y_kp, "Full_Kp")

    # Compute VIF for baseline predictors (same for both targets)
    vif_df = _calculate_vif(X_base)
    vif_records = vif_df.to_dict(orient="records")
    _check_multicollinearity(vif_records, "Baseline", output_dir)

    # Assemble summary
    summary = {
        "Baseline_Dst": baseline_dst,
        "Full_Dst": full_dst,
        "Baseline_Kp": baseline_kp,
        "Full_Kp": full_kp,
        "Delta_R2_Dst": full_dst["r_squared"] - baseline_dst["r_squared"],
        "Delta_R2_Kp": full_kp["r_squared"] - baseline_kp["r_squared"],
    }

    # Write JSON summary
    json_path = output_dir / "regression_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Write coefficients CSV (flattened)
    coeff_rows = []
    for model_key in ["Baseline_Dst", "Full_Dst", "Baseline_Kp", "Full_Kp"]:
        model_res = summary[model_key]
        for var, coef in model_res["coefficients"].items():
            coeff_rows.append(
                {
                    "model": model_key,
                    "variable": var,
                    "coefficient": coef,
                    "p_value": model_res["pvalues"].get(var, None),
                }
            )
    coeff_df = pd.DataFrame(coeff_rows)
    coeff_csv_path = output_dir / "regression_coefficients.csv"
    coeff_df.to_csv(coeff_csv_path, index=False)

    logger.info(f"Regression analysis completed; results saved to {output_dir}")
    return summary


def main() -> None:
    """Entry point placeholder."""
    logger.info("Regression module executed as script – no action defined.")


if __name__ == "__main__":
    main()
