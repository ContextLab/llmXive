"""
Model Analysis Script for Sustainable Agriculture Adoption Study (T036, T037, T038, T039).
Implements logistic regression, VIF diagnostics, FDR correction, and ROC/AUC analysis.
"""
from __future__ import annotations

import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.metrics import roc_curve, auc, roc_auc_score
from scipy import stats
import matplotlib.pyplot as plt

# Local imports
from config import get_config
from logging_config import log_operation, get_logger

# Suppress specific warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = get_logger("model_analysis")

class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass

@log_operation("load_engineered_data")
def load_engineered_data() -> pd.DataFrame:
    """Load the engineered dataset produced by T022."""
    config = get_config()
    input_path = config.get_data_path("engineered_data.csv")
    
    if not os.path.exists(input_path):
        raise CustomDataError(f"Engineered data not found at {input_path}. Run 03_engineer_features.py first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded engineered data with {len(df)} rows and {len(df.columns)} columns.")
    return df

@log_operation("prepare_model_data")
def prepare_model_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Prepare data for logistic regression.
    Returns: (X, y, feature_names)
    """
    target = "adoption_binary"
    if target not in df.columns:
        raise CustomDataError(f"Target column '{target}' not found in dataset.")
    
    # Define predictors based on spec
    # Primary: engagement_score
    # Covariates: age, education, farm_size, credit_access (if available)
    potential_covariates = ["age", "education", "farm_size", "credit_access"]
    
    predictors = ["engagement_score"]
    for cov in potential_covariates:
        if cov in df.columns:
            predictors.append(cov)
    
    # Check for missing values in predictors/target
    cols_to_check = predictors + [target]
    missing_mask = df[cols_to_check].isnull().any(axis=1)
    if missing_mask.any():
        logger.warning(f"Dropping {missing_mask.sum()} rows with missing values in predictors/target.")
        df = df[~missing_mask]
    
    X = df[predictors]
    y = df[target]
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    return X, y, predictors

@log_operation("fit_logistic_regression")
def fit_logistic_regression(X: pd.DataFrame, y: pd.Series) -> sm.LogitResultsWrapper:
    """Fit logistic regression model."""
    model = sm.Logit(y, X)
    result = model.fit(disp=0)  # disp=0 to suppress convergence warnings in log
    logger.info(f"Logistic regression converged: {result.converged}")
    return result

@log_operation("calculate_vif")
def calculate_vif(X: pd.DataFrame, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    Excludes the constant term.
    """
    vif_data = {}
    # X for VIF should not have the constant if we want to check multicollinearity among predictors
    X_vif = X.drop('const', axis=1, errors='ignore')
    
    for i, col in enumerate(X_vif.columns):
        try:
            vif = variance_inflation_factor(X_vif.values, i)
            vif_data[col] = vif
            if vif >= 5:
                logger.warning(f"High collinearity detected for '{col}': VIF = {vif:.2f}")
            else:
                logger.debug(f"VIF for '{col}': {vif:.2f}")
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

@log_operation("apply_fdr_correction")
def apply_fdr_correction(p_values: List[float], alpha: float = 0.10) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns adjusted p-values.
    """
    if not p_values:
        return []
    
    # statsmodels multipletests returns (reject, pvals_corrected, pvals_corrected_raw, alphacSidak)
    from statsmodels.stats.multitest import multipletests
    
    # We need to map back to original order, but multipletests handles the sorting internally
    # and returns corrected p-values in the original order.
    _, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    return list(pvals_corrected)

@log_operation("calculate_roc_metrics")
def calculate_roc_metrics(y_true: pd.Series, y_pred_proba: np.ndarray) -> Dict[str, Any]:
    """
    Calculate ROC AUC and return metrics.
    """
    auc_score = roc_auc_score(y_true, y_pred_proba)
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    
    return {
        "auc": float(auc_score),
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist()
    }

@log_operation("plot_roc_curve")
def plot_roc_curve(y_true: pd.Series, y_pred_proba: np.ndarray, output_path: str) -> None:
    """
    Generate and save ROC curve plot.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) - Sustainable Agriculture Adoption')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"ROC curve saved to {output_path}")

@log_operation("perform_mediation_analysis")
def perform_mediation_analysis(df: pd.DataFrame, X: pd.DataFrame, y: pd.Series, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for mediation analysis (T040).
    Returns an exploratory note as per requirements.
    """
    return {
        "status": "exploratory",
        "note": "Full mediation analysis (Baron & Kenny + E-values) requires T040 implementation.",
        "indirect_effect": None,
        "confidence_interval": None
    }

@log_operation("save_results")
def save_results(
    model_results: sm.LogitResultsWrapper,
    vif_data: Dict[str, float],
    fdr_p_values: List[float],
    roc_metrics: Dict[str, Any],
    mediation_results: Dict[str, Any],
    output_dir: str
) -> None:
    """Save all analysis results to YAML/JSON."""
    import json
    
    # Prepare summary
    summary = {
        "model_summary": model_results.summary2().as_text(), # Convert summary to text for storage
        "coefficients": {
            "names": model_results.params.index.tolist(),
            "values": model_results.params.tolist(),
            "p_values": model_results.pvalues.tolist(),
            "fdr_adjusted_p_values": fdr_p_values
        },
        "vif_diagnostics": vif_data,
        "roc_metrics": {
            "auc": roc_metrics["auc"]
        },
        "mediation_analysis": mediation_results
    }
    
    output_path = os.path.join(output_dir, "model_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Model results saved to {output_path}")

@log_operation("model_analysis_main")
def main() -> None:
    """Main execution flow for T039 and related US3 tasks."""
    config = get_config()
    output_dir = config.get_data_path("results")
    
    try:
        # 1. Load Data
        logger.info("Loading engineered data...")
        df = load_engineered_data()
        
        # 2. Prepare Data
        logger.info("Preparing model data...")
        X, y, feature_names = prepare_model_data(df)
        
        # 3. Fit Model
        logger.info("Fitting logistic regression...")
        model_result = fit_logistic_regression(X, y)
        
        # 4. VIF Analysis (T037)
        logger.info("Calculating VIF...")
        vif_scores = calculate_vif(X, feature_names)
        
        # 5. FDR Correction (T038)
        logger.info("Applying FDR correction...")
        p_values = model_result.pvalues.drop('const').tolist()
        adjusted_p_values = apply_fdr_correction(p_values)
        
        # 6. ROC/AUC Analysis (T039)
        logger.info("Calculating ROC metrics and plotting...")
        y_pred_proba = model_result.predict(X)
        roc_data = calculate_roc_metrics(y, y_pred_proba)
        
        roc_plot_path = os.path.join(output_dir, "roc_curve.png")
        plot_roc_curve(y, y_pred_proba, roc_plot_path)
        
        # 7. Mediation (Placeholder for T040)
        mediation_results = perform_mediation_analysis(df, X, y, config)
        
        # 8. Save Results
        logger.info("Saving results...")
        save_results(model_result, vif_scores, adjusted_p_values, roc_data, mediation_results, output_dir)
        
        logger.info("Model analysis complete.")
        
    except CustomDataError as e:
        logger.error(f"Data error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during model analysis: {e}")
        raise

if __name__ == "__main__":
    main()