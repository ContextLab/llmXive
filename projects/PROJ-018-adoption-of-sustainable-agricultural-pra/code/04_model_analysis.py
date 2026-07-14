"""
Model Analysis: Logistic Regression, VIF, FDR, ROC/AUC, Mediation.

This script performs the core statistical analysis for User Story 3.
It fits a logistic regression model, calculates VIFs, applies FDR correction,
computes ROC/AUC metrics, and performs mediation analysis.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.metrics import roc_curve, auc, roc_auc_score
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for figure generation
import matplotlib.pyplot as plt

# Import local utilities
from config import get_config
from logging_config import update_log_section, log_operation

# -----------------------------------------------------------------------------
# Custom Exceptions
# -----------------------------------------------------------------------------

class CustomDataError(Exception):
    """Raised when data loading or validation fails."""
    pass

class ModelError(Exception):
    """Raised when model fitting or analysis fails."""
    pass

# -----------------------------------------------------------------------------
# Configuration & Paths
# -----------------------------------------------------------------------------

def get_config_paths() -> Dict[str, Path]:
    """
    Resolve all required file paths using the central config.
    """
    project_root = Path(get_config("project_root", "."))
    return {
        "processed_data_path": project_root / get_config("processed_data_path", "data/processed"),
        "results_path": project_root / get_config("results_path", "results"),
        "modeling_log_path": project_root / get_config("modeling_log_path", "modeling_log.yaml"),
    }

# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------

def load_engineered_data(paths: Dict[str, Path]) -> pd.DataFrame:
    """
    Load the engineered dataset containing 'adoption_binary' and 'engagement_score'.
    """
    input_path = paths["processed_data_path"] / "engineered_data.csv"
    if not input_path.exists():
        raise CustomDataError(f"Engineered data not found at {input_path}. "
                              "Please run code/03_engineer_features.py first.")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['adoption_binary', 'engagement_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise CustomDataError(f"Missing required columns in engineered data: {missing}")
    
    logging.info(f"Loaded engineered data with {len(df)} rows from {input_path}")
    return df

# -----------------------------------------------------------------------------
# Data Preparation
# -----------------------------------------------------------------------------

def prepare_model_data(
    df: pd.DataFrame,
    target_col: str = 'adoption_binary',
    main_predictor: str = 'engagement_score',
    covariates: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare data for regression: handle missing values, select predictors.
    Returns the cleaned dataframe and the list of predictor column names.
    """
    # Drop rows with missing values in key columns
    cols_to_check = [target_col, main_predictor]
    if covariates:
        cols_to_check.extend(covariates)
    
    # Filter to only existing columns in case covariates list has extras
    cols_to_check = [c for c in cols_to_check if c in df.columns]
    
    df_clean = df.dropna(subset=cols_to_check)
    
    if len(df_clean) == 0:
        raise CustomDataError("No valid rows remaining after dropping missing values.")
    
    predictors = [main_predictor]
    if covariates:
        predictors.extend([c for c in covariates if c in df_clean.columns])
    
    logging.info(f"Prepared model data: {len(df_clean)} rows, predictors: {predictors}")
    return df_clean, predictors

# -----------------------------------------------------------------------------
# Logistic Regression
# -----------------------------------------------------------------------------

def fit_logistic_regression(
    df: pd.DataFrame,
    target_col: str,
    predictors: List[str]
) -> smGLMResultsWrapper:
    """
    Fit a logistic regression model using statsmodels.
    Returns the fitted model results.
    """
    X = df[predictors]
    y = df[target_col]
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    try:
        model = sm.Logit(y, X)
        results = model.fit(disp=0)  # disp=0 suppresses convergence output
    except Exception as e:
        raise ModelError(f"Failed to fit logistic regression: {str(e)}")
    
    logging.info("Logistic regression model fitted successfully.")
    return results

# -----------------------------------------------------------------------------
# VIF Calculation
# -----------------------------------------------------------------------------

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    Returns a DataFrame with predictor names and VIF values.
    """
    X = df[predictors]
    X = sm.add_constant(X)
    
    vif_data = []
    for col in X.columns:
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_data.append({'predictor': col, 'vif': vif})
        except Exception:
            vif_data.append({'predictor': col, 'vif': np.nan})
    
    vif_df = pd.DataFrame(vif_data)
    
    # Log warnings for high VIF
    high_vif = vif_df[vif_df['vif'] >= 5]
    if not high_vif.empty:
        logging.warning(f"High collinearity detected (VIF >= 5) for: {high_vif['predictor'].tolist()}")
    
    return vif_df

# -----------------------------------------------------------------------------
# FDR Correction
# -----------------------------------------------------------------------------

def apply_fdr_correction(
    p_values: List[float],
    alpha: float = 0.10
) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns adjusted p-values.
    """
    from statsmodels.stats.multitest import multipletests
    
    try:
        _, p_adj, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
        return list(p_adj)
    except Exception as e:
        logging.error(f"FDR correction failed: {str(e)}")
        return p_values  # Return original if failed

# -----------------------------------------------------------------------------
# ROC Curve & AUC Calculation (T039 Implementation)
# -----------------------------------------------------------------------------

def calculate_roc_metrics(
    df: pd.DataFrame,
    target_col: str,
    predictor_cols: List[str],
    results: smGLMResultsWrapper,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Calculate ROC curve and AUC for the fitted logistic regression model.
    Plots the ROC curve and saves it to the results directory.
    
    Returns a dictionary containing AUC value, threshold data, and figure path.
    """
    # Get predicted probabilities
    X = df[predictor_cols]
    X = sm.add_constant(X)
    y_true = df[target_col]
    
    y_pred_proba = results.predict(X)
    
    # Calculate AUC
    try:
        auc_value = roc_auc_score(y_true, y_pred_proba)
    except ValueError as e:
        # Handle edge cases where only one class is present
        logging.warning(f"Could not calculate AUC: {str(e)}. Setting AUC to NaN.")
        auc_value = np.nan
    
    # Calculate ROC curve points
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    
    # Plot ROC Curve
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc_value:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Chance')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    
    # Save figure
    roc_plot_path = output_dir / "roc_curve.png"
    plt.savefig(roc_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"ROC curve saved to {roc_plot_path} with AUC = {auc_value:.3f}")
    
    return {
        "auc": auc_value,
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
        "figure_path": str(roc_plot_path)
    }

def interpret_auc(auc_value: float) -> str:
    """
    Provide a qualitative interpretation of the AUC value.
    """
    if np.isnan(auc_value):
        return "Unable to calculate (insufficient class variance)"
    if auc_value < 0.5:
        return "No discrimination (worse than chance)"
    elif auc_value < 0.6:
        return "Poor discrimination"
    elif auc_value < 0.7:
        return "Fair discrimination"
    elif auc_value < 0.8:
        return "Good discrimination"
    elif auc_value < 0.9:
        return "Very good discrimination"
    else:
        return "Excellent discrimination"

# -----------------------------------------------------------------------------
# Mediation Analysis (Placeholder/Stub for T040 - kept for structure)
# -----------------------------------------------------------------------------

def perform_mediation_analysis(
    df: pd.DataFrame,
    target_col: str,
    main_predictor: str,
    mediator_col: str,
    covariates: List[str]
) -> Dict[str, Any]:
    """
    Placeholder for mediation analysis (Baron & Kenny + Bootstrap).
    Note: This is marked as 'exploratory' per FR-012.
    """
    logging.info("Mediation analysis requested but marked as exploratory.")
    return {
        "status": "exploratory",
        "note": "Full implementation pending T040"
    }

# -----------------------------------------------------------------------------
# Results Saving
# -----------------------------------------------------------------------------

def save_results(
    results: Any,
    vif_df: pd.DataFrame,
    roc_metrics: Dict[str, Any],
    fdr_p_values: List[float],
    predictors: List[str],
    output_dir: Path,
    log_path: Path
) -> None:
    """
    Save all model results to YAML and update the modeling log.
    """
    import yaml
    from datetime import datetime

    # Prepare summary data
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "model_type": "Logistic Regression",
        "predictors": predictors,
        "vif_diagnostics": vif_df.to_dict(orient='records'),
        "roc_analysis": {
            "auc": roc_metrics['auc'],
            "interpretation": interpret_auc(roc_metrics['auc']),
            "figure_path": roc_metrics['figure_path']
        },
        "fdr_corrected_p_values": fdr_p_values,
        "coefficients": results.params.to_dict(),
        "p_values": results.pvalues.to_dict()
    }

    # Save YAML
    results_yaml_path = output_dir / "model_results.yaml"
    with open(results_yaml_path, 'w') as f:
        # Custom representer to handle numpy types
        def numpy_representer(dumper, data):
            return dumper.represent_scalar('tag:yaml.org,2002:float', str(float(data)))
        yaml.add_representer(np.float64, numpy_representer)
        yaml.add_representer(np.float32, numpy_representer)
        yaml.dump(summary, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Model results saved to {results_yaml_path}")

    # Update modeling log
    log_data = {
        "model_analysis": {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "auc": roc_metrics['auc'],
            "vif_warning": (vif_df['vif'] >= 5).any(),
            "fdr_threshold": 0.10
        }
    }
    update_log_section("model_analysis", log_data, log_path=log_path)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    """
    Execute the full model analysis pipeline.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    args = argparse.ArgumentParser(description="Run Model Analysis")
    args.add_argument("--target", default="adoption_binary", help="Target variable name")
    args.add_argument("--predictor", default="engagement_score", help="Main predictor name")
    args.add_argument("--covariates", nargs="+", default=["age", "education", "farm_size", "credit"], 
                      help="List of covariate column names")
    args_parsed = args.parse_args()

    try:
        # 1. Setup Paths
        paths = get_config_paths()
        
        # 2. Load Data
        df = load_engineered_data(paths)
        
        # 3. Prepare Data
        df_clean, predictors = prepare_model_data(
            df, 
            target_col=args_parsed.target, 
            main_predictor=args_parsed.predictor, 
            covariates=args_parsed.covariates
        )
        
        # 4. Fit Model
        model_results = fit_logistic_regression(df_clean, args_parsed.target, predictors)
        
        # 5. VIF Analysis
        vif_df = calculate_vif(df_clean, predictors)
        
        # 6. FDR Correction
        p_vals = model_results.pvalues.drop('const').tolist()
        fdr_p_vals = apply_fdr_correction(p_vals)
        
        # 7. ROC/AUC Analysis (T039)
        roc_metrics = calculate_roc_metrics(
            df_clean, 
            args_parsed.target, 
            predictors, 
            model_results, 
            paths["results_path"]
        )
        
        # 8. Save Results
        save_results(
            model_results,
            vif_df,
            roc_metrics,
            fdr_p_vals,
            predictors,
            paths["results_path"],
            paths["modeling_log_path"]
        )
        
        # 9. Log Completion
        update_log_section("model_analysis", {"status": "completed"}, log_path=paths["modeling_log_path"])
        
        print(f"Analysis complete. AUC: {roc_metrics['auc']:.3f}")
        
    except CustomDataError as e:
        logging.error(f"Data Error: {e}")
        update_log_section("model_analysis", {"status": "failed", "error": str(e)}, log_path=paths.get("modeling_log_path"))
        sys.exit(1)
    except ModelError as e:
        logging.error(f"Model Error: {e}")
        update_log_section("model_analysis", {"status": "failed", "error": str(e)}, log_path=paths.get("modeling_log_path"))
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        update_log_section("model_analysis", {"status": "failed", "error": str(e)}, log_path=paths.get("modeling_log_path"))
        sys.exit(1)

if __name__ == "__main__":
    main()