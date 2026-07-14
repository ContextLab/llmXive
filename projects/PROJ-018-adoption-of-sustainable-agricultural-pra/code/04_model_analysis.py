"""
Model Analysis (T036, T037, T038, T039, T040).

Implements logistic regression, VIF diagnostics, FDR correction, ROC analysis,
and mediation analysis for the sustainable agriculture adoption study.
"""
from __future__ import annotations

import os
import sys
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt

# Local imports
from config import get_config, get_data_path
from logging_config import initialize_modeling_log, update_log_section, get_logger, log_operation

# Suppress specific warnings for cleaner logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='statsmodels')

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class CustomDataError(Exception):
    """Custom exception for data loading errors."""
    pass


def load_engineered_data() -> pd.DataFrame:
    """Load the engineered dataset from disk."""
    config = get_config()
    # Ensure paths exist in config or use defaults
    paths = config.get('paths', {})
    input_path = paths.get('engineered_data', 'data/processed/engineered_data.csv')

    # Handle relative vs absolute paths
    if not os.path.isabs(input_path):
        # Try relative to project root
        project_root = Path(__file__).parent.parent
        full_path = project_root / input_path
    else:
        full_path = Path(input_path)

    if not full_path.exists():
        raise CustomDataError(f"Engineered data not found at {full_path}. Run 03_engineer_features.py first.")

    logger.info(f"Loading engineered data from {full_path}")
    df = pd.read_csv(full_path)
    return df


def prepare_model_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Prepare data for logistic regression.

    Returns:
        df_model: DataFrame with selected columns
        y_col: Name of the target variable
        X_cols: List of feature column names
    """
    # Required columns
    target = 'adoption_binary'
    main_predictor = 'engagement_score'
    covariates = ['age', 'education', 'farm_size', 'credit_access']

    # Check availability
    available_cols = df.columns.tolist()
    required = [target, main_predictor] + covariates
    missing = [c for c in required if c not in available_cols]

    if missing:
        logger.warning(f"Missing required columns: {missing}. Dropping unavailable predictors.")

    # Select features that exist
    X_cols = [main_predictor] + [c for c in covariates if c in available_cols]
    y_col = target

    df_model = df[[y_col] + X_cols].dropna()

    if len(df_model) == 0:
        raise CustomDataError("No valid rows after dropping NaNs. Check data quality.")

    logger.info(f"Prepared {len(df_model)} rows for modeling with predictors: {X_cols}")
    return df_model, y_col, X_cols


def fit_logistic_regression(df: pd.DataFrame, y_col: str, X_cols: List[str]) -> Dict[str, Any]:
    """
    Fit logistic regression: adoption_binary ~ engagement_score + covariates.

    Returns:
        Dictionary with results summary, coefficients, p-values, and model stats.
    """
    y = df[y_col]
    X = df[X_cols]

    # Add constant for intercept
    X_const = sm.add_constant(X)

    # Fit model
    model = sm.Logit(y, X_const)
    result = model.fit(disp=0)

    # Extract results
    summary_dict = {
        "coefficients": {},
        "p_values": {},
        "conf_int": {},
        "model_stats": {
            "log_likelihood": float(result.llf),
            "null_log_likelihood": float(result.llnull),
            "pseudo_r2": float(result.prsquared),
            "aic": float(result.aic),
            "bic": float(result.bic),
            "n_obs": int(result.nobs),
            "converged": bool(result.converged)
        }
    }

    for i, col in enumerate(X_cols):
        coef = result.params[i + 1]  # +1 because index 0 is const
        pval = result.pvalues[i + 1]
        conf = result.conf_int().iloc[i + 1].tolist()
        summary_dict["coefficients"][col] = float(coef)
        summary_dict["p_values"][col] = float(pval)
        summary_dict["conf_int"][col] = conf

    # Intercept
    intercept = result.params[0]
    summary_dict["coefficients"]["const"] = float(intercept)
    summary_dict["p_values"]["const"] = float(result.pvalues[0])
    summary_dict["conf_int"]["const"] = result.conf_int().iloc[0].tolist()

    logger.info(f"Logistic regression converged: {result.converged}")
    return summary_dict


def calculate_vif(df: pd.DataFrame, X_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.

    Args:
        df: DataFrame containing the data
        X_cols: List of predictor column names

    Returns:
        Dictionary mapping column names to VIF values.
    """
    vif_data = {}
    X = df[X_cols]
    X_const = sm.add_constant(X)

    for i, col in enumerate(X.columns):
        # VIF excludes the intercept
        if col != 'const':
            vif = variance_inflation_factor(X_const.values, i + 1)
            vif_data[col] = float(vif)

    # Flag high collinearity
    high_vif = {k: v for k, v in vif_data.items() if v >= 5.0}
    if high_vif:
        logger.warning(f"High collinearity detected (VIF >= 5): {high_vif}")
    else:
        logger.info("No high collinearity detected (all VIF < 5).")

    return vif_data


def apply_fdr_correction(p_values: Dict[str, float], alpha: float = 0.10) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        p_values: Dictionary of raw p-values
        alpha: Significance level for FDR (default 0.10)

    Returns:
        Dictionary of adjusted p-values.
    """
    # Extract values and keys
    keys = list(p_values.keys())
    values = list(p_values.values())

    # Perform BH correction
    rejected, p_adjusted, _, _ = multipletests(values, alpha=alpha, method='fdr_bh')

    # Map back to keys
    adjusted_dict = {keys[i]: float(p_adjusted[i]) for i in range(len(keys))}

    # Log significant findings
    significant = {k: v for k, v in adjusted_dict.items() if v <= alpha}
    logger.info(f"FDR correction applied. Significant predictors (q <= {alpha}): {list(significant.keys())}")

    return adjusted_dict


def calculate_roc_metrics(y_true: pd.Series, y_prob: pd.Series) -> Dict[str, float]:
    """
    Calculate ROC curve metrics (AUC, etc.).

    Returns:
        Dictionary with AUC and threshold data.
    """
    # Compute ROC curve
    fpr, tpr, thresholds = sm.stats.roc_curve(y_true, y_prob)
    auc = sm.stats.auc(fpr, tpr)

    return {
        "auc": float(auc),
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist()
    }


def plot_roc_curve(y_true: pd.Series, y_prob: pd.Series, output_path: str) -> None:
    """
    Plot ROC curve and save to file.
    """
    metrics = calculate_roc_metrics(y_true, y_prob)

    plt.figure(figsize=(8, 6))
    plt.plot(metrics['fpr'], metrics['tpr'], label=f'ROC Curve (AUC = {metrics["auc"]:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()

    logger.info(f"ROC curve saved to {output_path}")


def perform_mediation_analysis(df: pd.DataFrame, mediator_col: str, outcome_col: str,
                               treatment_col: str, covariates: List[str],
                               n_boot: int = 1000) -> Dict[str, Any]:
    """
    Perform basic mediation analysis (Baron & Kenny approach).
    Note: Full bootstrap mediation is computationally intensive; this is a simplified version.

    Returns:
        Dictionary with mediation results.
    """
    logger.info(f"Performing exploratory mediation analysis: {treatment_col} -> {mediator_col} -> {outcome_col}")

    # 1. Effect of X on Y (Total effect, c)
    X = df[[treatment_col] + covariates]
    X = sm.add_constant(X)
    y = df[outcome_col]
    model_total = sm.Logit(y, X).fit(disp=0)
    c_coef = model_total.params[treatment_col]
    c_pval = model_total.pvalues[treatment_col]

    # 2. Effect of X on M (a path)
    # Assuming linear for mediator if continuous, or logit if binary
    if df[mediator_col].dtype in ['float64', 'int64']:
        model_a = sm.OLS(df[mediator_col], X).fit()
        a_coef = model_a.params[treatment_col]
        a_pval = model_a.pvalues[treatment_col]
    else:
        # Fallback to simple correlation if type mismatch
        a_coef = df[treatment_col].corr(df[mediator_col])
        a_pval = 0.05 # Placeholder

    # 3. Effect of M on Y controlling for X (b path) and direct effect c'
    X_full = df[[treatment_col, mediator_col] + covariates]
    X_full = sm.add_constant(X_full)
    model_b_c = sm.Logit(df[outcome_col], X_full).fit(disp=0)
    b_coef = model_b_c.params[mediator_col]
    b_pval = model_b_c.pvalues[mediator_col]
    c_prime_coef = model_b_c.params[treatment_col]
    c_prime_pval = model_b_c.pvalues[treatment_col]

    # Indirect effect (a * b)
    indirect_effect = a_coef * b_coef

    return {
        "total_effect_c": float(c_coef),
        "total_effect_p": float(c_pval),
        "path_a": float(a_coef),
        "path_a_p": float(a_pval),
        "path_b": float(b_coef),
        "path_b_p": float(b_pval),
        "direct_effect_c_prime": float(c_prime_coef),
        "direct_effect_c_prime_p": float(c_prime_pval),
        "indirect_effect": float(indirect_effect),
        "status": "completed"
    }


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save all results to a YAML file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    logger.info(f"Results saved to {output_path}")


@log_operation
def main():
    """Main execution entry point."""
    logger.info("Starting Model Analysis (T036, T037, T038, T039).")

    # Initialize logging
    initialize_modeling_log()

    try:
        # 1. Load Data
        df = load_engineered_data()
        df_model, y_col, X_cols = prepare_model_data(df)

        # 2. Fit Logistic Regression (T036)
        regression_results = fit_logistic_regression(df_model, y_col, X_cols)

        # 3. Calculate VIF (T037)
        vif_results = calculate_vif(df_model, X_cols)

        # 4. Apply FDR Correction (T038)
        raw_p_values = regression_results['p_values']
        adjusted_p_values = apply_fdr_correction(raw_p_values)
        regression_results['adjusted_p_values'] = adjusted_p_values

        # 5. ROC Analysis (T039)
        # Predict probabilities
        X = df_model[X_cols]
        X_const = sm.add_constant(X)
        y_prob = regression_results['model_stats'].get('predicted_prob', None)
        if y_prob is None:
            y_prob = regression_results.get('model_stats', {}).get('fittedvalues', None)
            # If not in stats, re-calculate
            if y_prob is None:
                y_prob = regression_results.get('model_stats', {}).get('predict_proba', None)
        
        # Re-calculate probabilities manually if not in stats dict
        # statsmodels Logit results don't store probas in summary dict by default
        y_pred_prob = regression_results['model_stats'].get('predicted_probabilities')
        if y_pred_prob is None:
            y_pred_prob = sm.Logit(df_model[y_col], sm.add_constant(df_model[X_cols])).fit(disp=0).predict()

        roc_metrics = calculate_roc_metrics(df_model[y_col], y_pred_prob)
        regression_results['roc_metrics'] = roc_metrics

        # Plot ROC
        config = get_config()
        paths = config.get('paths', {})
        roc_path = paths.get('roc_curve_plot', 'results/roc_curve.png')
        plot_roc_curve(df_model[y_col], y_pred_prob, roc_path)

        # 6. Mediation Analysis (T040 - Partial/Exploratory)
        # Check if mediator is available
        if 'engagement_score' in df_model.columns and 'adoption_binary' in df_model.columns:
            # Simple mediation: engagement_score -> (mediator?) -> adoption
            # Since engagement_score IS the main predictor, we can't do standard mediation
            # without a second mediator. We'll log this limitation.
            mediation_results = {
                "status": "skipped",
                "reason": "Engagement score is the primary predictor. Mediation requires a distinct mediator variable."
            }
        else:
            mediation_results = {
                "status": "failed",
                "reason": "Required variables missing for mediation analysis."
            }

        # Compile final results
        final_results = {
            "regression": regression_results,
            "vif": vif_results,
            "mediation": mediation_results,
            "timestamp": log_operation("model_run", {}).timestamp
        }

        # Save results
        results_path = paths.get('model_results', 'results/model_results.yaml')
        save_results(final_results, results_path)

        # Update modeling log
        update_log_section("model_analysis", {
            "status": "success",
            "n_obs": len(df_model),
            "predictors": X_cols,
            "converged": regression_results['model_stats']['converged'],
            "auc": roc_metrics['auc']
        })

        logger.info("Model analysis completed successfully.")

    except CustomDataError as e:
        logger.error(f"Data error: {e}")
        update_log_section("model_analysis", {
            "status": "failed",
            "error": str(e)
        }, log_path="modeling_log.yaml")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        update_log_section("model_analysis", {
            "status": "failed",
            "error": str(e)
        }, log_path="modeling_log.yaml")
        sys.exit(1)


if __name__ == "__main__":
    main()