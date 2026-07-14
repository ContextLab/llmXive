"""
Model Analysis Script for Sustainable Agricultural Practices Study (US3).
Implements logistic regression, VIF diagnostics, FDR correction, ROC analysis,
and mediation analysis.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.metrics import roc_curve, auc, roc_auc_score, confusion_matrix
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt

# Import local configuration and utilities
try:
    from config import get_config, get_data_path
except ImportError:
    # Fallback for direct execution without package context
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, get_data_path

try:
    from logging_config import log_operation, update_log_section, append_log_entry
except ImportError:
    # Fallback if logging_config is not in path
    class DummyLogger:
        def log(self, *args, **kwargs): return None
    def log_operation(*args, **kwargs):
        if len(args) == 1 and callable(args[0]): return args[0]
        return DummyLogger().log(*args, **kwargs)
    def update_log_section(*args, **kwargs): pass
    def append_log_entry(*args, **kwargs): pass


class CustomDataError(Exception):
    """Custom exception for data-related errors in modeling."""
    pass

class ModelError(Exception):
    """Custom exception for model fitting errors."""
    pass


def get_config_paths() -> Dict[str, str]:
    """Get standardized file paths from config."""
    config = get_config()
    return {
        'engineered_data': str(Path(config['paths']['processed_data']) / 'engineered_data.csv'),
        'results_dir': config['paths']['results'],
        'modeling_log': config['paths']['modeling_log'],
        'figures_dir': config['paths']['figures']
    }


def load_engineered_data(file_path: str) -> pd.DataFrame:
    """Load the engineered dataset with validation."""
    if not os.path.exists(file_path):
        raise CustomDataError(f"Engineered data file not found: {file_path}")

    df = pd.read_csv(file_path)
    required_cols = ['adoption_binary', 'engagement_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise CustomDataError(f"Missing required columns in engineered data: {missing}")

    return df


def prepare_model_data(
    df: pd.DataFrame,
    outcome_col: str = 'adoption_binary',
    predictor_col: str = 'engagement_score',
    covariates: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare data for logistic regression.
    Returns cleaned DataFrame and list of predictor names.
    """
    model_df = df[[outcome_col, predictor_col]].copy()

    # Drop rows with missing values in key columns
    model_df = model_df.dropna(subset=[outcome_col, predictor_col])

    predictors = [predictor_col]

    if covariates:
        # Filter to only existing covariates
        existing_covs = [c for c in covariates if c in df.columns]
        if existing_covs:
            model_df = model_df.join(df[existing_covs])
            model_df = model_df.dropna()
            predictors.extend(existing_covs)

    return model_df, predictors


def fit_logistic_regression(
    df: pd.DataFrame,
    formula: str
) -> sm.results.discrete.LogitResultsWrapper:
    """Fit logistic regression model using statsmodels."""
    try:
        model = smf.logit(formula, data=df)
        results = model.fit(disp=False)
        return results
    except Exception as e:
        raise ModelError(f"Failed to fit logistic regression: {str(e)}")


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    VIF >= 5 indicates potential collinearity.
    """
    vif_results = {}
    X = df[predictors].copy()
    X = sm.add_constant(X)

    for col in predictors:
        try:
            # Regress this predictor against all others
            y = X[col]
            X_other = X.drop(columns=[col])
            if 'const' in X_other.columns:
                X_other = X_other.drop(columns=['const'])
            X_other = sm.add_constant(X_other)

            if X_other.shape[1] > 1:
                model = sm.OLS(y, X_other).fit()
                vif = 1.0 / (1.0 - model.rsquared)
                vif_results[col] = vif
            else:
                vif_results[col] = 1.0
        except Exception:
            vif_results[col] = float('inf')

    return vif_results


def apply_fdr_correction(p_values: List[float], alpha: float = 0.10) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return []

    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]

    # BH procedure
    ranks = np.arange(1, n + 1)
    adjusted = sorted_pvals * n / ranks
    adjusted = np.minimum(adjusted, 1.0)

    # Ensure monotonicity (cumulative min from end)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])

    # Map back to original order
    final_adjusted = np.empty(n)
    final_adjusted[sorted_indices] = adjusted

    return final_adjusted.tolist()


def calculate_roc_metrics(
    y_true: np.ndarray,
    y_proba: np.ndarray
) -> Dict[str, float]:
    """
    Calculate ROC AUC and related metrics.
    """
    try:
        auc_score = roc_auc_score(y_true, y_proba)
        return {
            'auc': float(auc_score),
            'n_positive': int(np.sum(y_true)),
            'n_negative': int(len(y_true) - np.sum(y_true)),
            'total_samples': int(len(y_true))
        }
    except Exception as e:
        raise ModelError(f"Failed to calculate ROC metrics: {str(e)}")


def plot_roc_curve(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    output_path: str,
    title: str = "ROC Curve - Sustainable Agriculture Adoption Model"
) -> None:
    """
    Plot ROC curve and save to file.
    FR-009: Implement ROC curve plotting and AUC calculation.
    SC-003: Ensure model performance is assessed via ROC/AUC.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_proba)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def perform_mediation_analysis(
    df: pd.DataFrame,
    outcome: str,
    mediator: str,
    predictor: str,
    covariates: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Placeholder for mediation analysis.
    Actual implementation requires Baron & Kenny approach with bootstrap.
    Returns exploratory results.
    """
    return {
        'status': 'exploratory',
        'note': 'Mediation analysis requires evalues library and bootstrap resampling. '
                'Full implementation pending T040.'
    }


def calculate_evalue_sensitivity(
    results: sm.results.discrete.LogitResultsWrapper,
    term: str
) -> Dict[str, Any]:
    """
    Placeholder for E-value sensitivity analysis.
    """
    return {
        'status': 'skipped',
        'reason': 'evalues library not installed'
    }


def save_results(
    results: Dict[str, Any],
    output_dir: str,
    filename: str = 'model_results.json'
) -> None:
    """Save model results to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def main():
    """Main entry point for model analysis."""
    parser = argparse.ArgumentParser(description='Run model analysis for US3')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    args = parser.parse_args()

    if args.config:
        get_config(args.config)

    paths = get_config_paths()
    engineered_data_path = paths['engineered_data']
    results_dir = paths['results_dir']
    figures_dir = paths['figures_dir']

    # Initialize logging
    update_log_section("model_analysis", {"status": "started", "timestamp": datetime.utcnow().isoformat()})

    try:
        # 1. Load Data
        df = load_engineered_data(engineered_data_path)
        update_log_section("model_analysis", {"status": "data_loaded", "n_rows": len(df)})

        # 2. Prepare Model Data
        # Define covariates based on typical demographic controls
        covariates = ['age', 'education', 'farm_size', 'credit_access']
        model_df, predictors = prepare_model_data(df, covariates=covariates)

        if len(model_df) < 10:
            raise CustomDataError("Insufficient data for modeling after cleaning.")

        # 3. Fit Logistic Regression
        formula = 'adoption_binary ~ ' + ' + '.join(predictors)
        log_results = fit_logistic_regression(model_df, formula)

        # 4. Calculate VIF
        vif_results = calculate_vif(model_df, predictors)
        collinearity_warnings = {k: v for k, v in vif_results.items() if v >= 5.0}

        # 5. FDR Correction
        p_values = [log_results.pvalues[p] for p in predictors]
        adjusted_p_values = apply_fdr_correction(p_values, alpha=0.10)
        fdr_results = dict(zip(predictors, adjusted_p_values))

        # 6. ROC Analysis (T039 Implementation)
        y_true = model_df['adoption_binary'].values
        y_proba = log_results.predict().values

        roc_metrics = calculate_roc_metrics(y_true, y_proba)
        roc_plot_path = os.path.join(figures_dir, 'roc_curve.png')
        plot_roc_curve(y_true, y_proba, roc_plot_path, title="ROC Curve: Adoption Model")

        # 7. Mediation & Sensitivity (Placeholders for T040)
        mediation_results = perform_mediation_analysis(model_df, 'adoption_binary', 'engagement_score', 'engagement_score')
        sensitivity_results = calculate_evalue_sensitivity(log_results, 'engagement_score')

        # Compile Results
        final_results = {
            'model_summary': {
                'n_samples': len(model_df),
                'formula': formula,
                'pseudo_r2': log_results.prsquared,
                'converged': log_results.converged
            },
            'coefficients': {
                name: {
                    'coef': float(log_results.params[name]),
                    'std_err': float(log_results.bse[name]),
                    'p_value': float(log_results.pvalues[name]),
                    'p_adj': float(fdr_results[name]),
                    'odds_ratio': float(math.exp(log_results.params[name]))
                }
                for name in predictors
            },
            'diagnostics': {
                'vif': vif_results,
                'collinearity_warnings': collinearity_warnings,
                'fdr_threshold': 0.10
            },
            'performance': {
                'auc': roc_metrics['auc'],
                'roc_plot': roc_plot_path,
                'n_positive': roc_metrics['n_positive'],
                'n_negative': roc_metrics['n_negative']
            },
            'mediation': mediation_results,
            'sensitivity': sensitivity_results
        }

        # Save Results
        save_results(final_results, results_dir, 'model_results.json')

        # Update Log
        update_log_section("model_analysis", {
            "status": "completed",
            "auc": roc_metrics['auc'],
            "vif_warnings": len(collinearity_warnings),
            "results_file": os.path.join(results_dir, 'model_results.json')
        })

        print(f"Model analysis complete. AUC: {roc_metrics['auc']:.3f}")
        print(f"Results saved to: {os.path.join(results_dir, 'model_results.json')}")
        print(f"ROC plot saved to: {roc_plot_path}")

    except Exception as e:
        update_log_section("model_analysis", {"status": "failed", "error": str(e)})
        raise


if __name__ == "__main__":
    main()