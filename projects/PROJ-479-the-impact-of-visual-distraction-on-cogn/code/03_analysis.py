"""
code/03_analysis.py
Statistical Analysis: Correlations, VIF, PCA, Regression, and Multiplicity Correction.
Implements conditional logic: if VIF >= 5, re-run analysis using PCA component.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import pearsonr
from scipy.stats import bootstrap
from scipy.stats import t as t_dist
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from utils import get_logger, set_random_seed, get_global_seed

# Configure logging
logger = get_logger(__name__)

# Constants
VIF_THRESHOLD = 5.0
SEED = get_global_seed()

def load_analysis_data(path: str) -> pd.DataFrame:
    """Load the final analysis dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis data not found at {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded analysis data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def calculate_correlations(df: pd.DataFrame, predictors: List[str], outcome: str) -> Dict[str, Dict[str, float]]:
    """Calculate Pearson correlations between predictors and outcome."""
    results = {}
    for pred in predictors:
        # Filter out NaNs for this specific pair
        valid_mask = df[[pred, outcome]].notna().all(axis=1)
        x = df.loc[valid_mask, pred]
        y = df.loc[valid_mask, outcome]
        
        if len(x) < 3:
            logger.warning(f"Not enough data for correlation: {pred} vs {outcome}")
            results[pred] = {'r': np.nan, 'p': np.nan}
            continue
        
        r, p = pearsonr(x, y)
        results[pred] = {'r': float(r), 'p': float(p)}
    return results

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors."""
    # Filter rows where all predictors are non-null
    valid_df = df[predictors].dropna()
    if valid_df.shape[0] < 10:
        logger.warning("Insufficient data for VIF calculation")
        return {p: np.nan for p in predictors}
    
    X = sm.add_constant(valid_df)
    vif_results = {}
    for i, col in enumerate(predictors):
        vif = variance_inflation_factor(X.values, i+1) # +1 because of constant
        vif_results[col] = float(vif)
    
    logger.info(f"VIF Scores: {vif_results}")
    return vif_results

def run_pca(df: pd.DataFrame, predictors: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run PCA on predictors and extract component 1."""
    valid_df = df[predictors].dropna()
    if valid_df.shape[0] < 2:
        raise ValueError("Insufficient data for PCA")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(valid_df)
    
    pca = PCA(n_components=1)
    component_1 = pca.fit_transform(X_scaled)
    
    # Map back to original index
    pca_series = pd.Series(component_1.flatten(), index=valid_df.index, name='pca_component_1')
    
    # Save explained variance
    pca_results = {
        'explained_variance_ratio': float(pca.explained_variance_ratio_[0]),
        'components': pca.components_.tolist(),
        'n_components': 1
    }
    
    # Merge back to full df
    df_with_pca = df.copy()
    df_with_pca['pca_component_1'] = pca_series
    
    return df_with_pca, pca_results

def run_regression(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """Run simple linear regression and return beta, CI."""
    valid_mask = df[[predictor_col, outcome_col]].notna().all(axis=1)
    X = df.loc[valid_mask, predictor_col]
    y = df.loc[valid_mask, outcome_col]
    
    if len(X) < 3:
        return {'beta': np.nan, 'ci_lower': np.nan, 'ci_upper': np.nan}
    
    X_const = sm.add_constant(X)
    model = sm.OLS(y, X_const).fit()
    
    beta = model.params[1]
    # 95% CI
    conf_int = model.conf_int(alpha=0.05)
    ci_lower = float(conf_int.iloc[1, 0])
    ci_upper = float(conf_int.iloc[1, 1])
    
    return {
        'beta': float(beta),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'r_squared': float(model.rsquared),
        'p_value': float(model.pvalues[1])
    }

def bootstrap_correlation(df: pd.DataFrame, x_col: str, y_col: str, n_iterations: int = 1000) -> Dict[str, float]:
    """Compute bootstrap confidence intervals for correlation."""
    valid_mask = df[[x_col, y_col]].notna().all(axis=1)
    x = df.loc[valid_mask, x_col].values
    y = df.loc[valid_mask, y_col].values
    
    if len(x) < 3:
        return {'ci_lower': np.nan, 'ci_upper': np.nan}
    
    def corr_func(data, indices):
        d = data[indices]
        return pearsonr(d[:, 0], d[:, 1])[0]
    
    data_matrix = np.column_stack((x, y))
    res = bootstrap((data_matrix,), corr_func, n_resamples=n_iterations, confidence_level=0.95)
    
    return {
        'ci_lower': float(res.confidence_interval.low),
        'ci_upper': float(res.confidence_interval.high)
    }

def apply_holm_bonferroni(p_values: Dict[str, float]) -> Dict[str, float]:
    """Apply Holm-Bonferroni correction to p-values."""
    from statsmodels.stats.multitest import multipletests
    
    if not p_values:
        return {}
    
    names = list(p_values.keys())
    p_vals = np.array(list(p_values.values()))
    
    # Filter out NaNs for the test, but keep track
    valid_mask = ~np.isnan(p_vals)
    if not np.any(valid_mask):
        return {k: np.nan for k in names}
    
    _, p_adj, _, _ = multipletests(p_vals[valid_mask], method='holm')
    
    result = {}
    for i, name in enumerate(names):
        if valid_mask[i]:
            result[name] = float(p_adj[i])
        else:
            result[name] = np.nan
    
    return result

def save_statistics(stats: Dict[str, Any], path: str):
    """Save statistics to JSON."""
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    logger.info(f"Saved statistics to {path}")

def save_pca_results(results: Dict[str, Any], path: str):
    """Save PCA results to JSON."""
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved PCA results to {path}")

def main():
    set_random_seed(SEED)
    logger.info("Starting Statistical Analysis (T034 + T031/T032/T033)")
    
    # 1. Load Data
    input_path = "data/processed/final_analysis_data.csv"
    df = load_analysis_data(input_path)
    
    predictors = ['edge_density', 'color_entropy', 'object_count']
    outcome = 'reaction_time' # Or accuracy, depending on spec, using reaction_time as primary
    
    # 2. Calculate VIF (T032)
    vif_scores = calculate_vif(df, predictors)
    
    # Save VIF report
    vif_report_path = "results/statistics/vif_report.json"
    os.makedirs(os.path.dirname(vif_report_path), exist_ok=True)
    save_statistics(vif_scores, vif_report_path)
    
    # 3. Conditional Logic (T034)
    max_vif = max([v for v in vif_scores.values() if not np.isnan(v)], default=0)
    
    final_stats = {}
    final_predictors = predictors
    use_pca = False
    
    if max_vif >= VIF_THRESHOLD:
        logger.warning(f"High Collinearity detected (Max VIF={max_vif:.2f} >= {VIF_THRESHOLD}). Switching to PCA mode.")
        use_pca = True
        
        # Run PCA (T033)
        df_pca, pca_results = run_pca(df, predictors)
        
        # Save PCA results (T033 deliverable)
        pca_path = "data/processed/pca_results.json"
        os.makedirs(os.path.dirname(pca_path), exist_ok=True)
        save_pca_results(pca_results, pca_path)
        
        final_predictors = ['pca_component_1']
        outcome = 'reaction_time' # Ensure outcome is consistent
        
        # Re-run Correlation, Bootstrap, and Regression for PCA component
        logger.info("Re-running analysis with PCA component...")
        
        # Correlation
        corr_res = calculate_correlations(df_pca, final_predictors, outcome)
        final_stats['correlations'] = corr_res
        
        # Regression (FR-007 requirement for PCA path)
        reg_res = run_regression(df_pca, 'pca_component_1', outcome)
        final_stats['regression'] = reg_res
        
        # Bootstrap (FR-009 requirement)
        boot_res = bootstrap_correlation(df_pca, 'pca_component_1', outcome)
        final_stats['bootstrap'] = boot_res
        
        # Adjusted P-values
        adj_p = apply_holm_bonferroni({k: v['p'] for k, v in corr_res.items()})
        final_stats['adjusted_p'] = adj_p
        
        final_stats['method'] = 'PCA (Collinearity Detected)'
        final_stats['vif_status'] = f"Max VIF={max_vif:.2f} >= {VIF_THRESHOLD}"
        
    else:
        logger.info("Collinearity within acceptable limits. Using raw metrics.")
        final_predictors = predictors
        
        # Correlation
        corr_res = calculate_correlations(df, predictors, outcome)
        final_stats['correlations'] = corr_res
        
        # Regression for each predictor
        reg_results = {}
        for p in predictors:
            reg_results[p] = run_regression(df, p, outcome)
        final_stats['regression'] = reg_results
        
        # Bootstrap
        boot_results = {}
        for p in predictors:
            boot_results[p] = bootstrap_correlation(df, p, outcome)
        final_stats['bootstrap'] = boot_results
        
        # Adjusted P-values
        adj_p = apply_holm_bonferroni({k: v['p'] for k, v in corr_res.items()})
        final_stats['adjusted_p'] = adj_p
        
        final_stats['method'] = 'Raw Metrics'
        final_stats['vif_status'] = f"Max VIF={max_vif:.2f} < {VIF_THRESHOLD}"
    
    # 4. Save Final Statistics (T039b)
    stats_path = "results/statistics/statistics.json"
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    save_statistics(final_stats, stats_path)
    
    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()