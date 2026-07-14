"""
User Story 3: Logistic Regression, Mediation Analysis, and Reporting.
Implements ROC curve plotting and AUC calculation as per T039.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve

# Import config and logging utilities
from config import get_config, load_config_from_yaml
from logging_config import (
    append_log_entry,
    get_logger,
    log_operation,
    update_log_section,
)

class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass


class ModelError(Exception):
    """Custom exception for model-related errors."""
    pass


def get_config_paths() -> Dict[str, Any]:
    """Load configuration paths from config.yaml."""
    config = get_config()
    return {
        "engineered_data_path": config.get("engineered_data_path", "data/processed/engineered_data.csv"),
        "results_dir": config.get("results_dir", "results"),
        "modeling_log_path": config.get("modeling_log_path", "modeling_log.yaml"),
    }


def load_engineered_data(path: str) -> pd.DataFrame:
    """Load the engineered dataset."""
    if not os.path.exists(path):
        raise CustomDataError(f"Engineered data file not found at {path}")
    df = pd.read_csv(path)
    required_cols = ["adoption_binary", "engagement_score"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise CustomDataError(f"Missing required columns in engineered data: {missing}")
    return df


def prepare_model_data(df: pd.DataFrame) -> tuple:
    """
    Prepare data for logistic regression.
    Returns X (design matrix), y (outcome), and the formula string.
    """
    # Define outcome
    y = df["adoption_binary"]

    # Define predictors: engagement_score + covariates
    # Covariates from spec: age, education, farm_size, credit
    covariates = []
    for col in ["age", "education", "farm_size", "credit"]:
        if col in df.columns:
            covariates.append(col)
        else:
            # Log warning but continue
            pass

    predictors = ["engagement_score"] + covariates

    # Handle missing values in predictors for the model
    model_cols = predictors + ["adoption_binary"]
    valid_df = df[model_cols].dropna()

    if len(valid_df) == 0:
        raise ModelError("No valid rows remaining after dropping missing values for model variables.")

    X = valid_df[predictors]
    y = valid_df["adoption_binary"]

    return X, y, predictors


def fit_logistic_regression(X: pd.DataFrame, y: pd.Series, predictors: List[str]) -> sm.results.wrapper.Wrapper:
    """Fit a logistic regression model using statsmodels."""
    X_with_const = sm.add_constant(X)
    model = sm.Logit(y, X_with_const)
    result = model.fit(disp=False)
    return result

    Args:
        df: DataFrame with target and predictors
        predictors: List of predictor column names (excluding target)

def calculate_vif(X: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each predictor."""
    vif_data = {}
    X_with_const = sm.add_constant(X)
    for col in predictors:
        if col in X_with_const.columns:
            try:
                vif = sm.stats.outliers_influence.variance_inflation_factor(
                    X_with_const.values, X_with_const.columns.get_loc(col)
                )
                vif_data[col] = vif
            except Exception:
                vif_data[col] = np.nan
    return vif_data


def apply_fdr_correction(p_values: List[float], alpha: float = 0.10) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    from statsmodels.stats.multitest import multipletests
    _, corrected_pvals, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return corrected_pvals.tolist()


def calculate_roc_metrics(y_true: pd.Series, y_pred_proba: np.ndarray) -> Dict[str, float]:
    """
    Calculate ROC curve metrics: AUC and FPR/TPR arrays.
    Implements T039 requirement.
    """
    auc = roc_auc_score(y_true, y_pred_proba)
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    return {
        "auc": auc,
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist()
    }


def plot_roc_curve(y_true: pd.Series, y_pred_proba: np.ndarray, output_path: str) -> None:
    """
    Generate and save the ROC curve plot.
    Implements T039 requirement to create a figure.
    """
    auc = roc_auc_score(y_true, y_pred_proba)
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.tight_layout()

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def perform_mediation_analysis(df: pd.DataFrame, outcome: str, mediator: str, exposure: str) -> Dict[str, Any]:
    """
    Placeholder for mediation analysis (T040).
    Returns exploratory results.
    """
    return {
        "status": "exploratory",
        "note": "Mediation analysis requires Baron & Kenny steps with bootstrap. Not fully implemented in this task."
    }

    logging.info(f"Performing exploratory mediation analysis: {independent_col} -> {mediator_col} -> {dependent_col}")

def calculate_evalue_sensitivity(estimate: float, ci_low: float, ci_high: float) -> Dict[str, Any]:
    """
    Placeholder for E-value sensitivity analysis (T040).
    """
    return {
        "status": "skipped",
        "reason": "E-values library not installed or analysis pending."
    }


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save model results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


@log_operation("model_analysis_main")
def main():
    """Main execution for Model Analysis."""
    logger = get_logger()
    paths = get_config_paths()

    try:
        # Update log section
        update_log_section("model_analysis", {"status": "started", "timestamp": datetime.utcnow().isoformat()})

        # 1. Load Data
        print("Loading engineered data...")
        df = load_engineered_data(paths["engineered_data_path"])

        # 2. Prepare Data
        X, y, predictors = prepare_model_data(df)

        # 3. Fit Logistic Regression
        print("Fitting logistic regression...")
        model_result = fit_logistic_regression(X, y, predictors)

        # 4. VIF Diagnostics
        print("Calculating VIF...")
        vif_scores = calculate_vif(X, predictors)
        collinearity_warnings = {k: v for k, v in vif_scores.items() if v >= 5}

        # 5. FDR Correction
        p_values = model_result.pvalues.drop('const').tolist()
        corrected_pvals = apply_fdr_correction(p_values)

        # 6. T039: ROC Curve and AUC
        print("Calculating ROC/AUC and plotting...")
        y_pred_proba = model_result.predict(X)
        roc_metrics = calculate_roc_metrics(y, y_pred_proba)
        
        # Save AUC to results
        results = {
            "regression_summary": model_result.summary2().as_text(),
            "coefficients": model_result.params.to_dict(),
            "p_values": model_result.pvalues.to_dict(),
            "corrected_p_values": dict(zip([p for p in model_result.pvalues.drop('const').index], corrected_pvals)),
            "vif_scores": vif_scores,
            "collinearity_warnings": collinearity_warnings,
            "roc": {
                "auc": roc_metrics["auc"],
                "fpr": roc_metrics["fpr"],
                "tpr": roc_metrics["tpr"],
                "thresholds": roc_metrics["thresholds"]
            }
        }

        # Plot ROC Curve (T039)
        roc_plot_path = os.path.join(paths["results_dir"], "roc_curve.png")
        plot_roc_curve(y, y_pred_proba, roc_plot_path)
        print(f"ROC curve saved to {roc_plot_path}")

        # Save JSON results
        results_path = os.path.join(paths["results_dir"], "model_results.json")
        save_results(results, results_path)

        # Update modeling log
        log_entry = {
            "status": "completed",
            "auc": roc_metrics["auc"],
            "collinearity_warnings": collinearity_warnings,
            "fdr_applied": True
        }
        update_log_section("model_analysis", log_entry)

        print("Model analysis completed successfully.")

    except Exception as e:
        error_msg = str(e)
        print(f"Error during model analysis: {error_msg}")
        update_log_section("model_analysis", {"status": "failed", "error": error_msg})
        raise


if __name__ == "__main__":
    main()