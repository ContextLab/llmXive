import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats

# Ensure config and utils are available if needed, though this file
# primarily focuses on analysis logic as per task T023.
# We assume the environment has the necessary dependencies installed.

logger = logging.getLogger(__name__)

def check_vif(df: pd.DataFrame, covariates: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for covariates.
    Returns a dictionary mapping column name to VIF value.
    """
    vif_data = {}
    # Add a constant for the intercept if using OLS, but VIF usually
    # checks the predictors themselves.
    X = df[covariates].dropna()
    if X.empty:
        return vif_data
    
    # Add constant for the regression matrix if needed for VIF calculation context
    # However, standard VIF calculation on the matrix X:
    # VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing X_i on other X's.
    
    for col in X.columns:
        try:
            # Regress col against all other columns
            y = X[col]
            X_other = X.drop(columns=[col])
            if X_other.shape[1] == 0:
                vif_data[col] = 1.0
                continue
            
            model = sm.OLS(y, sm.add_constant(X_other)).fit()
            r_squared = model.rsquared
            if r_squared == 1.0:
                vif_data[col] = np.inf
            else:
                vif_data[col] = 1.0 / (1.0 - r_squared)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def fit_mixed_effects_model(df: pd.DataFrame, 
                            formula: str, 
                            groups: str) -> Any:
    """
    Fit a linear mixed-effects model.
    """
    # Clean data for model fitting
    model_data = df.dropna(subset=[col.strip('` ') for col in formula.split() if col not in ['~', '+', '(', ')', '|', '1']])
    if model_data.empty:
        raise ValueError("No valid data for mixed effects model after dropping NaNs.")
    
    try:
        model = mixedlm(formula, model_data, groups=model_data[groups])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit mixed effects model: {e}")
        raise

def calculate_partial_correlations(df: pd.DataFrame, 
                                   x_col: str, 
                                   y_col: str, 
                                   control_cols: List[str]) -> Tuple[float, float]:
    """
    Calculate partial correlation between x and y controlling for control_cols.
    Returns (correlation, p-value).
    """
    # Prepare data
    cols = [x_col, y_col] + control_cols
    data = df[cols].dropna()
    if data.shape[0] < 3:
        return 0.0, 1.0

    # Residualize
    X = data[control_cols]
    if X.shape[1] > 0:
        X = sm.add_constant(X)
        model_x = sm.OLS(data[x_col], X).fit()
        res_x = model_x.resid
        model_y = sm.OLS(data[y_col], X).fit()
        res_y = model_y.resid
    else:
        res_x = data[x_col]
        res_y = data[y_col]

    corr, p_value = stats.pearsonr(res_x, res_y)
    return corr, p_value

def run_meta_analysis(correlations: List[float], sample_sizes: List[int]) -> Dict[str, Any]:
    """
    Perform meta-analysis using Fisher's z-transformation.
    correlations: list of r values
    sample_sizes: list of N values
    """
    if not correlations or not sample_sizes:
        return {"z_mean": 0, "ci_lower": 0, "ci_upper": 0, "p_value": 1.0}

    # Fisher transformation
    z_values = [0.5 * np.log((1 + r) / (1 - r)) for r in correlations]
    variances = [1 / (n - 3) for n in sample_sizes]
    
    # Weighted mean
    weights = [1 / v if v > 0 else 0 for v in variances]
    total_weight = sum(weights)
    if total_weight == 0:
        return {"z_mean": 0, "ci_lower": 0, "ci_upper": 0, "p_value": 1.0}

    z_mean = sum(w * z for w, z in zip(weights, z_values)) / total_weight
    
    # Standard error of the mean
    se_mean = np.sqrt(1 / total_weight)
    
    # 95% CI
    z_lower = z_mean - 1.96 * se_mean
    z_upper = z_mean + 1.96 * se_mean
    
    # Back-transform to r
    r_mean = (np.exp(2 * z_mean) - 1) / (np.exp(2 * z_mean) + 1)
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    # P-value for H0: mean = 0
    z_stat = z_mean / se_mean
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    return {
        "r_mean": r_mean,
        "ci_lower": r_lower,
        "ci_upper": r_upper,
        "p_value": p_value,
        "z_mean": z_mean,
        "n_studies": len(correlations)
    }

def run_sensitivity_analysis(df: pd.DataFrame, 
                             thresholds: List[int], 
                             x_col: str, 
                             y_col: str, 
                             control_cols: List[str]) -> pd.DataFrame:
    """
    Run correlation analysis for different LOC thresholds.
    """
    results = []
    for thresh in thresholds:
        mask = df['avg_loc'] >= thresh
        subset = df[mask]
        if len(subset) < 5:
            results.append({
                "threshold": thresh,
                "n": len(subset),
                "correlation": np.nan,
                "p_value": np.nan
            })
            continue
        
        corr, p_val = calculate_partial_correlations(subset, x_col, y_col, control_cols)
        results.append({
            "threshold": thresh,
            "n": len(subset),
            "correlation": corr,
            "p_value": p_val
        })
    
    return pd.DataFrame(results)

def run_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main analysis runner. Loads data, runs models, and returns results dict.
    """
    logger.info("Running analysis pipeline...")
    
    # Load data
    data_path = Path(config.get('data_path', 'data/processed/unified_metrics.csv'))
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Define columns
    x_col = 'total_lines_changed'
    y_col = 'debt_score'
    control_cols = ['avg_loc', 'contributor_count', 'project_age']
    
    # Ensure required columns exist
    required_cols = [x_col, y_col] + control_cols + ['repo_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")
    
    # 1. VIF Check
    vif_results = check_vif(df, control_cols)
    logger.info(f"VIF Results: {vif_results}")
    
    # 2. Mixed Effects Model
    formula = f"{y_col} ~ {x_col} + {' + '.join(control_cols)}"
    # Use 'repo_id' for grouping
    try:
        mixed_result = fit_mixed_effects_model(df, formula, 'repo_id')
        mixed_summary = mixed_result.summary().as_csv() if hasattr(mixed_result.summary(), 'as_csv') else str(mixed_result.summary())
    except Exception as e:
        logger.warning(f"Mixed model failed: {e}")
        mixed_summary = None

    # 3. Partial Correlation
    corr, p_val = calculate_partial_correlations(df, x_col, y_col, control_cols)
    
    # 4. Meta-analysis (per repo)
    # Group by repo and calculate r for each
    repo_results = []
    for repo_id, group in df.groupby('repo_id'):
        if len(group) < 5:
            continue
        r, p = calculate_partial_correlations(group, x_col, y_col, control_cols)
        repo_results.append({'repo_id': repo_id, 'r': r, 'n': len(group)})
    
    meta_input_r = [r['r'] for r in repo_results if not np.isnan(r['r'])]
    meta_input_n = [r['n'] for r in repo_results if not np.isnan(r['r'])]
    
    meta_result = run_meta_analysis(meta_input_r, meta_input_n)
    
    # 5. Sensitivity Analysis
    thresholds = config.get('loc_thresholds', [5, 10, 20])
    sensitivity_df = run_sensitivity_analysis(df, thresholds, x_col, y_col, control_cols)
    
    return {
        "vif": vif_results,
        "mixed_model_summary": mixed_summary,
        "partial_correlation": {"r": corr, "p": p_val},
        "meta_analysis": meta_result,
        "sensitivity_analysis": sensitivity_df,
        "raw_correlation": corr
    }

def main():
    """
    Entry point for analysis. Loads config, runs analysis, saves results.
    """
    import sys
    # Simple config loading for the script
    config = {
        'data_path': 'data/processed/unified_metrics.csv',
        'loc_thresholds': [5, 10, 20]
    }
    
    try:
        results = run_analysis(config)
        
        # Save Results
        results_path = Path('data/results')
        results_path.mkdir(parents=True, exist_ok=True)
        
        # 1. correlation_results.csv
        corr_results = pd.DataFrame([results['partial_correlation']])
        corr_results.to_csv(results_path / 'correlation_results.csv', index=False)
        
        # 2. sensitivity_analysis.csv
        results['sensitivity_analysis'].to_csv(results_path / 'sensitivity_analysis.csv', index=False)
        
        # 3. meta_analysis_results.csv
        meta_df = pd.DataFrame([results['meta_analysis']])
        meta_df.to_csv(results_path / 'meta_analysis_results.csv', index=False)
        
        logger.info("Analysis complete. Results saved to data/results/")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()