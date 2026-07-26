import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger

logger = get_logger(__name__)

def load_regression_results() -> pd.DataFrame:
    """
    Load the regression results from the modeling step.
    Expects data/final/regression_results.csv or similar intermediate output.
    Since T033 (fit_mixed_model) is the source of truth, we assume it writes
    a temporary results file or we extract from the model object if available.
    
    For this implementation, we assume `modeling.py` has a `main` or function
    that returns the fitted model object and writes intermediate stats.
    However, since we need to generate a summary CSV, we will re-load the
    user_track_pairs and refit the model to ensure we have the latest stats,
    OR we expect the modeling step to have exported a summary.
    
    Given the task description "Generate ... containing coefficients, SEs, p-values, and VIFs",
    and the dependency on T033, we will implement the logic to refit the model
    on the available data (T029 output) to ensure we have the exact numbers
    to report, as T033 might have been run in a loop or context that didn't
    persist the final summary.
    
    Actually, T033 is `fit_mixed_model`. T038 depends on T033.
    We will load the data from T029 (user_track_pairs.parquet) and refit
    the model defined in T033 to generate the summary.
    """
    config = get_config_dict()
    project_root = get_project_root()
    pairs_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    
    if not pairs_path.exists():
        raise FileNotFoundError(f"Required input file not found: {pairs_path}")
    
    logger.info(f"Loading user-track pairs from {pairs_path}")
    df = pd.read_parquet(pairs_path)
    
    # Ensure necessary columns exist
    required_cols = ['mean_vividness', 'adolescent_exposure_ratio', 'overall_popularity_score', 'user_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in user_track_pairs: {missing}")
    
    return df

def calculate_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for the predictors in the model.
    Uses the data from the dataframe to construct the design matrix.
    """
    import patsy
    
    # Build design matrix
    y, X = patsy.dmatrices(formula, df, return_type='dataframe')
    
    # Add intercept column for VIF calculation if not present (patsy usually adds it)
    # patsy adds 'Intercept'
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == 'Intercept':
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def generate_summary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fit the MixedLM model and generate the summary dataframe with coefficients,
    standard errors, p-values, and VIFs.
    """
    config = get_config_dict()
    
    # Define the model formula as per T033
    formula = "mean_vividness ~ adolescent_exposure_ratio + overall_popularity_score"
    
    # Prepare data for statsmodels MixedLM
    # We need to group by user_id
    groups = df['user_id']
    endog = df['mean_vividness']
    exog = df[['adolescent_exposure_ratio', 'overall_popularity_score']]
    
    # Fit the model
    logger.info("Fitting MixedLM model...")
    try:
        model = sm.MixedLM(endog, exog, groups=groups)
        result = model.fit()
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise
    
    # Extract results
    summary = []
    
    # Fixed effects
    for param_name, coef in result.params.items():
        if param_name == 'group_var': # Skip variance component if present in params
            continue
        std_err = result.bse[param_name]
        # t-value
        t_val = coef / std_err if std_err != 0 else np.nan
        # p-value (two-sided)
        # Approximate p-value using normal distribution for large samples or t-distribution
        # statsmodels usually provides this, but let's compute if missing
        p_val = 2 * (1 - sm.distributions.norm.cdf(abs(t_val)))
        
        summary.append({
            'term': param_name,
            'coef': coef,
            'std_err': std_err,
            't_val': t_val,
            'p_value': p_val,
            'type': 'fixed_effect'
        })
    
    # Random effects (variance)
    if hasattr(result, 'cov_re'):
        # Extract random intercept variance
        # result.random_effects is a dict of user_id -> effects
        # result.cov_re is the covariance matrix of random effects
        # We want the variance of the random intercept
        if result.cov_re is not None:
            # Assuming 1x1 matrix for random intercept
            re_var = float(result.cov_re[0, 0])
            re_std = np.sqrt(re_var)
            summary.append({
                'term': 'Random Intercept Variance',
                'coef': re_var,
                'std_err': np.nan, # SE for variance is complex
                't_val': np.nan,
                'p_value': np.nan,
                'type': 'random_effect'
            })
    
    # Calculate VIFs
    vifs = calculate_vif(df, formula)
    for term, vif_val in vifs.items():
        # Find if this term exists in summary, else add it
        found = False
        for row in summary:
            if row['term'] == term:
                row['vif'] = vif_val
                found = True
                break
        if not found:
            summary.append({
                'term': term,
                'coef': np.nan,
                'std_err': np.nan,
                't_val': np.nan,
                'p_value': np.nan,
                'vif': vif_val,
                'type': 'vif'
            })
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary)
    
    # Ensure VIF column exists even if empty
    if 'vif' not in summary_df.columns:
        summary_df['vif'] = np.nan
    
    return summary_df

def main():
    """
    Main entry point for generating the regression summary.
    """
    setup_logging()
    logger.info("Starting regression summary generation (T038)...")
    
    try:
        # Load data
        df = load_regression_results()
        
        # Generate summary
        summary_df = generate_summary_dataframe(df)
        
        # Save to CSV
        project_root = get_project_root()
        output_path = project_root / "data" / "final" / "regression_summary.csv"
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        summary_df.to_csv(output_path, index=False)
        logger.info(f"Regression summary saved to {output_path}")
        
        # Update state.yaml if needed (handled by state_manager if integrated)
        # For now, just logging
        logger.info("T038 completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate regression summary: {e}")
        raise

if __name__ == "__main__":
    main()