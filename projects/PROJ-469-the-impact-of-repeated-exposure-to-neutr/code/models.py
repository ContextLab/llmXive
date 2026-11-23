"""
Models module for fitting linear regression models and analyzing results.
"""

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import logging
from pathlib import Path
from config_manager import get_results_path

logger = logging.getLogger(__name__)

def fit_primary_model(df: pd.DataFrame) -> dict:
    """
    Fit the primary linear regression model:
    IAT_D ~ news_exposure_z * political_ideology
    
    Args:
        df: Preprocessed DataFrame with derived variables.
        
    Returns:
        Dictionary containing model results (coefficients, p-values, etc.)
    """
    logger.info("Fitting primary linear regression model...")
    
    # Ensure required columns exist
    required_cols = ['IAT_D_score', 'news_exposure_z', 'political_ideology']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for primary model: {missing_cols}")
    
    # Prepare data
    y = df['IAT_D_score'].dropna()
    # Align X with y
    X = df[['news_exposure_z', 'political_ideology']].loc[y.index]
    
    # Create interaction term
    X['interaction'] = X['news_exposure_z'] * X['political_ideology']
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X, missing='drop')
    results = model.fit()
    
    # Extract results
    res_dict = {
        'interaction_coef': results.params.get('interaction', np.nan),
        'interaction_pval': results.pvalues.get('interaction', np.nan),
        'interaction_se': results.bse.get('interaction', np.nan),
        'news_exposure_coef': results.params.get('news_exposure_z', np.nan),
        'ideology_coef': results.params.get('political_ideology', np.nan),
        'r_squared': results.rsquared,
        'n_obs': results.nobs,
        'f_pvalue': results.f_pvalue
    }
    
    logger.info(f"Primary model fitted. R-squared: {res_dict['r_squared']:.4f}")
    return res_dict

def fit_covariate_model(df: pd.DataFrame) -> dict:
    """
    Fit the model with covariates:
    IAT_D ~ news_exposure_z * political_ideology + age + gender + education
    
    Args:
        df: Preprocessed DataFrame with derived variables.
        
    Returns:
        Dictionary containing model results with covariate adjustments.
    """
    logger.info("Fitting covariate-adjusted model...")
    
    required_cols = ['IAT_D_score', 'news_exposure_z', 'political_ideology', 'age', 'gender', 'education']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # Log warning but try to proceed if possible, or raise
        logger.warning(f"Covariate model missing columns: {missing_cols}. Skipping covariates.")
        # Fallback to primary model if covariates missing
        return fit_primary_model(df)
    
    # Prepare data
    y = df['IAT_D_score'].dropna()
    # Align X with y
    X = df[['news_exposure_z', 'political_ideology', 'age', 'gender', 'education']].loc[y.index]
    
    # Create interaction term
    X['interaction'] = X['news_exposure_z'] * X['political_ideology']
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X, missing='drop')
    results = model.fit()
    
    # Extract results
    res_dict = {
        'interaction_coef': results.params.get('interaction', np.nan),
        'interaction_pval': results.pvalues.get('interaction', np.nan),
        'interaction_se': results.bse.get('interaction', np.nan),
        'news_exposure_coef': results.params.get('news_exposure_z', np.nan),
        'ideology_coef': results.params.get('political_ideology', np.nan),
        'age_coef': results.params.get('age', np.nan),
        'gender_coef': results.params.get('gender', np.nan),
        'education_coef': results.params.get('education', np.nan),
        'r_squared': results.rsquared,
        'n_obs': results.nobs,
        'f_pvalue': results.f_pvalue
    }
    
    logger.info(f"Covariate model fitted. R-squared: {res_dict['r_squared']:.4f}")
    return res_dict

def compare_models(primary_res: dict, covariate_res: dict) -> dict:
    """Compare primary and covariate models."""
    return {
        'coef_change': covariate_res.get('interaction_coef', 0) - primary_res.get('interaction_coef', 0),
        'pval_change': covariate_res.get('interaction_pval', 1) - primary_res.get('interaction_pval', 1),
        'r_squared_change': covariate_res.get('r_squared', 0) - primary_res.get('r_squared', 0)
    }

def save_model_results(results: dict) -> None:
    """
    Save model results to results/primary_model.csv.
    This function was missing from the original models.py and caused the import error in main.py.
    """
    results_path = get_results_path()
    output_file = results_path / "primary_model.csv"
    
    # Flatten results for CSV
    flat_results = {k: [v] if not isinstance(v, (list, dict)) else v for k, v in results.items()}
    df = pd.DataFrame(flat_results)
    df.to_csv(output_file, index=False)
    logger.info(f"Model results saved to {output_file}")

def check_model_convergence(results) -> bool:
    """Check if model results are finite."""
    if not results:
        return False
    # Check if any key coefficient is NaN or Inf
    coef = results.get('interaction_coef')
    if coef is None or not np.isfinite(coef):
        return False
    return True

def calculate_vif(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """Calculate Variance Inflation Factor for features."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X = df[features].dropna()
    X = sm.add_constant(X)
    vif_data = pd.DataFrame()
    vif_data["Feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    return vif_data

def run_primary_analysis(df: pd.DataFrame) -> dict:
    """Run the primary analysis pipeline."""
    res = fit_primary_model(df)
    save_model_results(res)
    return res

def run_covariate_analysis(df: pd.DataFrame) -> dict:
    """Run the covariate analysis pipeline."""
    res = fit_covariate_model(df)
    return res