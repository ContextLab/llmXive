import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from sklearn.metrics import roc_curve, auc, roc_auc_score
import matplotlib.pyplot as plt

from config import get_config, set_random_seed
from logging_config import get_logger, update_log_section

# Ensure matplotlib uses a non-interactive backend for headless execution
plt.switch_backend('Agg')

logger = get_logger(__name__)

def load_engineered_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the engineered dataset from the processed data directory."""
    data_path = Path(config['paths']['processed_data'])
    file_path = data_path / 'engineered_data.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(f"Engineered data file not found at {file_path}. Run T020-T022 first.")
    
    logger.info(f"Loading engineered data from {file_path}")
    df = pd.read_csv(file_path)
    return df

def prepare_model_data(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
    """Prepare data for logistic regression, handling missing values and selecting predictors."""
    # Select target and predictors based on config or defaults
    target_col = config.get('model', {}).get('target_column', 'adoption_binary')
    engagement_col = config.get('model', {}).get('engagement_column', 'engagement_score')
    covariates = config.get('model', {}).get('covariates', ['age', 'education', 'farm_size', 'credit'])
    
    # Ensure target exists
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    # Filter to rows with non-null target and engagement
    valid_cols = [target_col, engagement_col] + [c for c in covariates if c in df.columns]
    model_df = df[valid_cols].dropna()
    
    if model_df.empty:
        raise ValueError("No valid rows remaining after dropping NaNs for model variables.")
    
    logger.info(f"Model data prepared: {len(model_df)} rows, predictors: {valid_cols}")
    return model_df, [engagement_col] + [c for c in covariates if c in valid_cols]

def fit_logistic_regression(df: pd.DataFrame, target_col: str, predictors: List[str], config: Dict[str, Any]) -> sm.results.logit.LogitResults:
    """Fit a logistic regression model using statsmodels."""
    y = df[target_col]
    X = df[predictors]
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    model = sm.Logit(y, X)
    result = model.fit(disp=False)
    
    logger.info("Logistic regression model fitted successfully.")
    return result

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor (VIF) for all predictors."""
    X = df[predictors]
    X = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
        
        if vif >= 5:
            logger.warning(f"High collinearity detected for {col}: VIF = {vif:.2f}")
    
    return vif_data

def apply_fdr_correction(p_values: List[float]) -> Tuple[List[float], List[bool]]:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    if not p_values:
        return [], []
    
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=0.10, method='fdr_bh')
    return list(pvals_corrected), list(reject)

def calculate_roc_metrics(y_true: pd.Series, y_prob: pd.Series) -> Dict[str, float]:
    """Calculate ROC AUC and related metrics."""
    roc_auc = roc_auc_score(y_true, y_prob)
    logger.info(f"ROC AUC calculated: {roc_auc:.4f}")
    return {'auc': roc_auc}

def plot_roc_curve(y_true: pd.Series, y_prob: pd.Series, config: Dict[str, Any]) -> str:
    """
    Generate ROC curve plot and save to file.
    Returns the path to the saved figure.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    
    output_dir = Path(config['paths']['results'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'roc_curve.png'
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"ROC curve plot saved to {output_path}")
    return str(output_path)

def perform_mediation_analysis(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for mediation analysis (T040).
    Returns a structure indicating it is not yet implemented.
    """
    logger.info("Mediation analysis not yet implemented (T040).")
    return {"status": "pending", "method": "baron_kenny_bootstrap"}

def calculate_sensitivity_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for sensitivity analysis (T040).
    """
    logger.info("Sensitivity analysis not yet implemented (T040).")
    return {"status": "pending"}

def save_results(results: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Save all model results to a YAML file."""
    output_dir = Path(config['paths']['results'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'model_results.yaml'
    
    with open(output_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Results saved to {output_path}")
    return str(output_path)

def main():
    """Main entry point for Task T039: ROC Curve and AUC Calculation."""
    set_random_seed(42) # Default seed from config if not set
    config = get_config()
    
    try:
        # 1. Load Data
        df = load_engineered_data(config)
        model_df, predictors = prepare_model_data(df, config)
        
        target_col = config.get('model', {}).get('target_column', 'adoption_binary')
        engagement_col = config.get('model', {}).get('engagement_column', 'engagement_score')
        
        # 2. Fit Model (Required to get predictions for ROC)
        # Note: T036 handles the main fit, but we need predictions here.
        # We re-fit or use the result if passed. For this task, we fit locally.
        y = model_df[target_col]
        X = model_df[predictors]
        X = sm.add_constant(X)
        logit_model = sm.Logit(y, X)
        result = logit_model.fit(disp=False)
        
        # 3. Calculate Predicted Probabilities
        y_prob = result.predict(X)
        
        # 4. Calculate AUC
        auc_metrics = calculate_roc_metrics(y, y_prob)
        
        # 5. Plot ROC Curve
        roc_path = plot_roc_curve(y, y_prob, config)
        
        # 6. Compile Results
        results = {
            "task_id": "T039",
            "roc_auc": auc_metrics['auc'],
            "roc_curve_plot_path": roc_path,
            "model_summary": result.summary2().as_text(),
            "n_observations": len(model_df)
        }
        
        # Save results
        results_path = save_results(results, config)
        
        # Update modeling log
        update_log_section(
            config['paths']['modeling_log'],
            "roc_analysis",
            {
                "auc": auc_metrics['auc'],
                "plot_path": roc_path,
                "status": "completed"
            }
        )
        
        logger.info("Task T039 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T039 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()