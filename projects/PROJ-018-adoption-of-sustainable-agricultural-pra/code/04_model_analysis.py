"""Model analysis pipeline for US3.

This script loads the engineered dataset, fits a logistic regression
model predicting ``adoption_binary`` from ``engagement_score`` and any
additional covariates, computes VIF diagnostics, applies Benjamini‑Hochberg
FDR correction, evaluates ROC/AUC, and writes all artefacts to the
``results/`` directory.  It also updates ``modeling_log.yaml`` with
timestamps and a hash of the modelling choices.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import auc, roc_curve
import matplotlib.pyplot as plt

# Project‑level utilities
from config import get_config, get_processed_data_path, get_results_path, get_modeling_log_path
from logging_config import log_operation, update_log_section

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------

class CustomDataError(RuntimeError):
    """Raised when required input data cannot be located or is malformed."""

class ModelError(RuntimeError):
    """Raised for any modelling‑related failure."""

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

@log_operation
def get_config_paths() -> dict[str, Path]:
    """Collect frequently used paths from the configuration."""
    cfg = get_config()
    return {
        "processed": get_processed_data_path(),
        "results": get_results_path(),
        "log": get_modeling_log_path(),
    }

@log_operation
def load_engineered_data(path: Path) -> pd.DataFrame:
    """Load the engineered CSV; raise ``CustomDataError`` if missing."""
    if not path.is_file():
        raise CustomDataError(f"Engineered data not found at {path}")
    df = pd.read_csv(path)
    return df

@log_operation
def prepare_model_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Split ``df`` into design matrix ``X`` and outcome ``y``.

    - ``adoption_binary`` is the dependent variable.
    - ``engagement_score`` and all other numeric/categorical columns
      (excluding the outcome) are used as predictors.
    - Categorical columns are one‑hot encoded (drop first to avoid collinearity).
    """
    if "adoption_binary" not in df.columns:
        raise ModelError("Column 'adoption_binary' missing from engineered data.")

    y = df["adoption_binary"]
    X = df.drop(columns=["adoption_binary"])

    # One‑hot encode object / category dtype columns
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns
    if len(categorical_cols):
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)

    # Add constant for intercept
    X = sm.add_constant(X, has_constant="add")
    return X, y

@log_operation
def fit_logistic_regression(X: pd.DataFrame, y: pd.Series) -> sm.Logit:
    """Fit a logistic regression model using statsmodels."""
    try:
        model = sm.Logit(y, X, missing="drop")
        result = model.fit(disp=False)
        return result
    except Exception as exc:
        raise ModelError(f"Logistic regression failed: {exc}") from exc

@log_operation
def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """Calculate variance‑inflation factors for each predictor (excluding constant)."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    vif_data = []
    # Exclude the constant term from VIF calculation
    cols = [c for c in X.columns if c != "const"]
    for i, col in enumerate(cols):
        vif = variance_inflation_factor(X[cols].values, i)
        vif_data.append({"variable": col, "VIF": round(vif, 3)})
    return pd.DataFrame(vif_data)

@log_operation
def apply_fdr_correction(pvalues: pd.Series, q: float = 0.10) -> pd.DataFrame:
    """
    Perform Benjamini‑Hochberg FDR correction.

    Returns a DataFrame with original p‑values, adjusted q‑values and a
    boolean flag indicating significance at the supplied ``q`` level.
    """
    from statsmodels.stats.multitest import multipletests

    adjusted = multipletests(pvalues, alpha=q, method="fdr_bh")
    reject, p_adj = adjusted[0], adjusted[1]
    out = pd.DataFrame(
        {
            "p_value": pvalues,
            "p_adj": p_adj,
            "reject": reject,
        }
    )
    return out

@log_operation
def calculate_roc_metrics(y_true: pd.Series, y_score: pd.Series) -> dict[str, Any]:
    """Compute ROC curve points, AUC, and return a dict of metrics."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    return {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
        "auc": float(roc_auc),
    }

@log_operation
def plot_roc_curve(metrics: dict[str, Any], out_path: Path) -> None:
    """Generate a ROC plot and write it to ``out_path``."""
    plt.figure()
    plt.plot(metrics["fpr"], metrics["tpr"], color="darkorange", lw=2,
             label=f"ROC curve (AUC = {metrics['auc']:.3f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic")
    plt.legend(loc="lower right")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()

@log_operation
def save_results(result: sm.Logit, vif: pd.DataFrame, fdr: pd.DataFrame,
                 roc: dict[str, Any], paths: dict[str, Path]) -> None:
    """Persist all modelling artefacts to the ``results`` directory."""
    # 1. Regression coefficients & summary
    coeff_path = paths["results"] / "logistic_regression.json"
    coeff_path.parent.mkdir(parents=True, exist_ok=True)
    coeff_path.write_text(
        json.dumps(
            {
                "params": result.params.to_dict(),
                "pvalues": result.pvalues.to_dict(),
                "stderr": result.bse.to_dict(),
                "aic": result.aic,
                "bic": result.bic,
                "log_likelihood": result.llf,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # 2. VIF diagnostics
    vif_path = paths["results"] / "vif.json"
    vif_path.write_text(vif.to_json(orient="records", indent=2), encoding="utf-8")

    # 3. FDR‑adjusted p‑values
    fdr_path = paths["results"] / "fdr.json"
    fdr_path.write_text(fdr.to_json(orient="records", indent=2), encoding="utf-8")

    # 4. ROC/AUC metrics
    roc_path = paths["results"] / "roc.json"
    roc_path.write_text(json.dumps(roc, indent=2), encoding="utf-8")

    # 5. ROC plot (figure)
    plot_path = paths["results"] / "roc_curve.png"
    plot_roc_curve(roc, plot_path)

    # Update the modelling log with a simple hash of the modelling choices
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": "logistic_regression",
        "features_used": list(vif["variable"]),
        "auc": roc["auc"],
    }
    update_log_section("model_analysis", log_entry, log_path=paths["log"])

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fit logistic regression, compute diagnostics, and save artefacts."
    )
    parser.add_argument(
        "--engineered",
        type=str,
        default=str(get_processed_data_path() / "engineered_data.csv"),
        help="Path to the engineered CSV (default: data/processed/engineered_data.csv)",
    )
    args = parser.parse_args()

    paths = get_config_paths()
    engineered_path = Path(args.engineered)

    # Load data
    df = load_engineered_data(engineered_path)

    # Prepare matrices
    X, y = prepare_model_data(df)

    # Fit model
    model_result = fit_logistic_regression(X, y)

    # VIF diagnostics
    vif_df = calculate_vif(X)

    # FDR correction on model p‑values
    fdr_df = apply_fdr_correction(model_result.pvalues)

    # ROC / AUC – use predicted probabilities for the positive class
    y_pred_prob = model_result.predict(X)
    roc_metrics = calculate_roc_metrics(y, y_pred_prob)

    # Persist everything
    save_results(model_result, vif_df, fdr_df, roc_metrics, paths)

    print("Model analysis completed successfully.")

if __name__ == "__main__":
    # Basic logging configuration for any stray ``logging`` calls
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        main()
    except Exception as exc:
        logging.exception("Model analysis failed")
        sys.exit(1)