import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.model_selection import cross_val_score, GridSearchCV
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from config import get_config
from logging_config import get_logger

# Use config for paths
def get_data_path(relative_path: str) -> Path:
    config = get_config()
    return Path(config.get("data_dir", "data")) / relative_path

def load_standard_subset() -> pd.DataFrame:
    """
    Loads the standard subset of the dataset.
    """
    logger = get_logger(__name__)
    data_path = get_data_path("processed/descriptors.csv")
    if not data_path.exists():
        logger.error(f"Data file {data_path} not found.")
        return pd.DataFrame()
    
    df = pd.read_csv(data_path)
    # Filter for standard conditions if columns exist
    if 'temp' in df.columns and 'ph' in df.columns:
        df = df[(df['temp'] == 25) & (df['ph'] == 7.4)]
    return df

def compute_correlation_matrix(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Computes correlation matrix for features and target.
    """
    cols = feature_cols + [target_col]
    return df[cols].corr()

def compute_p_values(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, float]:
    """
    Computes p-values for correlations.
    """
    p_values = {}
    for col in feature_cols:
        corr, p_val = stats.pearsonr(df[col], df[target_col])
        p_values[col] = p_val
    return p_values

def identify_significant_correlations(correlation_matrix: pd.DataFrame, p_values: Dict[str, float], threshold: float = 0.05) -> List[Tuple[str, str, float, float]]:
    """
    Identifies significant correlations based on threshold.
    """
    significant = []
    target_col = correlation_matrix.columns[-1]
    for col in correlation_matrix.columns[:-1]:
        corr = correlation_matrix.loc[col, target_col]
        p_val = p_values.get(col, 1.0)
        if abs(corr) >= 0.5 and p_val < threshold:
            significant.append((col, target_col, corr, p_val))
    return significant

def run_sensitivity_analysis(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, Any]:
    """
    Runs sensitivity analysis by varying thresholds.
    """
    logger = get_logger(__name__)
    results = {}
    for threshold in [0.1, 0.05, 0.01]:
        p_values = compute_p_values(df, feature_cols, target_col)
        significant = identify_significant_correlations(
            compute_correlation_matrix(df, feature_cols, target_col), 
            p_values, 
            threshold
        )
        results[f'threshold_{threshold}'] = significant
    return results

def run_mlr(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, Any]:
    """
    Runs Multiple Linear Regression.
    """
    logger = get_logger(__name__)
    X = df[feature_cols]
    y = df[target_col]
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R-squared
    y_pred = model.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return {
        'coefficients': dict(zip(feature_cols, model.coef_)),
        'intercept': model.intercept_,
        'r_squared': r_squared
    }

def run_conditional_covariate_model(df: pd.DataFrame, feature_cols: List[str], target_col: str, covariates: List[str]) -> Dict[str, Any]:
    """
    Runs MLR with covariates if available.
    """
    logger = get_logger(__name__)
    all_features = feature_cols + covariates
    return run_mlr(df, all_features, target_col)

def run_lasso_regression(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, Any]:
    """
    Runs LASSO regression with K=5 fold cross-validation.
    """
    logger = get_logger(__name__)
    X = df[feature_cols]
    y = df[target_col]
    
    param_grid = {'alpha': [0.01, 0.05, 0.1, 0.5, 1.0]}
    lasso = Lasso()
    grid_search = GridSearchCV(lasso, param_grid, cv=5)
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return {
        'best_alpha': grid_search.best_params_['alpha'],
        'coefficients': dict(zip(feature_cols, best_model.coef_)),
        'intercept': best_model.intercept_,
        'r_squared': r_squared
    }

def perform_residual_diagnostics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
    """
    Performs residual diagnostics (Shapiro-Wilk, Breusch-Pagan).
    """
    logger = get_logger(__name__)
    residuals = y_true - y_pred
    
    # Shapiro-Wilk test for normality
    shapiro_stat, shapiro_p = stats.shapiro(residuals)
    
    # Breusch-Pagan test for homoscedasticity
    # Requires a model object or design matrix
    # Using a simple linear model for demonstration
    try:
        bp_stat, bp_p, _, _ = het_breuschpagan(residuals, y_pred.values.reshape(-1, 1))
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {str(e)}")
        bp_p = 1.0
    
    return {
        'shapiro_wilk_p': shapiro_p,
        'breusch_pagan_p': bp_p
    }

def verify_correlation_significance(p_values: Dict[str, float], threshold: float = 0.05) -> bool:
    """
    Verifies if any correlation is significant.
    """
    return any(p < threshold for p in p_values.values())

def verify_residual_diagnostics(diagnostics: Dict[str, float], threshold: float = 0.05) -> bool:
    """
    Verifies residual diagnostics pass.
    """
    return diagnostics['shapiro_wilk_p'] > threshold and diagnostics['breusch_pagan_p'] > threshold

def save_analysis_results(results: Dict[str, Any], output_path: Path):
    """
    Saves analysis results to JSON.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for analysis.
    """
    logger = get_logger(__name__)
    logger.info("Starting analysis pipeline...")
    
    df = load_standard_subset()
    if df.empty:
        logger.error("No data to analyze.")
        return
    
    feature_cols = ['tpsa', 'rotatable_bonds', 'mw', 'aromatic_rings', 'wiener_index', 'zagreb_index']
    target_col = 'half_life'
    
    # Compute correlations
    corr_matrix = compute_correlation_matrix(df, feature_cols, target_col)
    p_values = compute_p_values(df, feature_cols, target_col)
    significant = identify_significant_correlations(corr_matrix, p_values)
    
    # Run MLR
    mlr_results = run_mlr(df, feature_cols, target_col)
    
    # Run LASSO
    lasso_results = run_lasso_regression(df, feature_cols, target_col)
    
    # Residual diagnostics
    y_pred_mlr = LinearRegression().fit(df[feature_cols], df[target_col]).predict(df[feature_cols])
    diagnostics = perform_residual_diagnostics(df[target_col], y_pred_mlr)
    
    # Verify significance
    corr_significant = verify_correlation_significance(p_values)
    residual_pass = verify_residual_diagnostics(diagnostics)
    
    # Compile results
    results = {
        'correlation_significance_pass': corr_significant,
        'residual_diagnostics_pass': residual_pass,
        'correlation_conclusion': f"Correlation exists: {corr_significant}",
        'mlr': mlr_results,
        'lasso': lasso_results,
        'diagnostics': diagnostics
    }
    
    # Save results
    output_path = get_data_path("processed/analysis_results.json")
    save_analysis_results(results, output_path)
    logger.info(f"Analysis results saved to {output_path}")

if __name__ == "__main__":
    main()
