"""
Robustness checks module for the political news exposure analysis.

This module implements:
1. Bootstrap resampling (Task T021)
2. Alpha sensitivity sweep (Task T022)
3. Monte Carlo Standard Error calculation
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path

from config_manager import get_results_path, get_bootstrap_count, get_analysis_seed, get_alpha_level
from models import fit_primary_model
from logging_config import get_logger

logger = get_logger(__name__)


def run_bootstrap_analysis(
    data: pd.DataFrame,
    n_bootstrap: int = 1000,
    seed: Optional[int] = None,
    interaction_term: str = "news_exposure_z:political_ideology"
) -> pd.DataFrame:
    """
    Perform bootstrap resampling to estimate the stability of the interaction term.
    
    This function:
    1. Resamples the data with replacement `n_bootstrap` times.
    2. Fits the primary model to each resample.
    3. Collects the coefficient for the interaction term.
    4. Calculates the Monte Carlo Standard Error (std of the bootstrap distribution).
    5. Calculates 95% Confidence Intervals (percentile method).
    
    Args:
        data: The preprocessed dataframe with imputed values.
        n_bootstrap: Number of bootstrap iterations (default 1000).
        seed: Random seed for reproducibility.
        interaction_term: Name of the interaction column in the model.
        
    Returns:
        A DataFrame containing the bootstrap statistics:
        - mean_coefficient
        - monte_carlo_se (std of bootstrap coeffs)
        - ci_lower (2.5th percentile)
        - ci_upper (97.5th percentile)
    """
    if seed is None:
        seed = get_analysis_seed()
    
    np.random.seed(seed)
    logger.info(f"Starting bootstrap analysis with n={n_bootstrap} and seed={seed}")
    
    bootstrap_coeffs = []
    
    # Pre-define formula to avoid parsing overhead in loop if possible, 
    # but fit_primary_model handles it. We assume fit_primary_model is efficient enough.
    # For large n, we might optimize, but 1000 is standard.
    
    for i in range(n_bootstrap):
        # Resample rows with replacement
        resample_indices = np.random.choice(data.index, size=len(data), replace=True)
        resample_data = data.loc[resample_indices].copy()
        
        try:
            # Fit model on resample
            # We assume fit_primary_model returns a statsmodels RegressionResults object
            # or a dict-like object with .params
            result = fit_primary_model(resample_data)
            
            # Extract interaction coefficient
            if hasattr(result, 'params'):
                coeff = result.params.get(interaction_term)
            elif isinstance(result, dict):
                coeff = result.get(interaction_term)
            else:
                logger.warning(f"Unexpected result type from fit_primary_model: {type(result)}")
                continue
            
            if coeff is not None:
                bootstrap_coeffs.append(coeff)
            
        except Exception as e:
            # If a resample fails (e.g., singular matrix), skip it
            logger.debug(f"Bootstrap iteration {i} failed: {e}")
            continue
    
    if len(bootstrap_coeffs) == 0:
        raise ValueError("No valid bootstrap samples were generated.")
    
    coeffs_array = np.array(bootstrap_coeffs)
    
    # Calculate statistics
    mean_coeff = np.mean(coeffs_array)
    # Monte Carlo SE is the standard deviation of the bootstrap distribution
    mc_se = np.std(coeffs_array, ddof=1)
    
    # Confidence Intervals (Percentile Method)
    ci_lower = np.percentile(coeffs_array, 2.5)
    ci_upper = np.percentile(coeffs_array, 97.5)
    
    logger.info(f"Bootstrap complete. Mean: {mean_coeff:.4f}, SE: {mc_se:.4f}, CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    summary_df = pd.DataFrame([{
        'term': interaction_term,
        'mean_coefficient': mean_coeff,
        'monte_carlo_se': mc_se,
        'ci_lower_95': ci_lower,
        'ci_upper_95': ci_upper,
        'n_successful_resamples': len(coeffs_array)
    }])
    
    return summary_df


def run_alpha_sweep(
    data: pd.DataFrame,
    thresholds: Optional[List[float]] = None,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Evaluate the significance of the interaction term across different alpha levels.
    
    Args:
        data: The preprocessed dataframe.
        thresholds: List of alpha thresholds to test (default: [0.01, 0.05, 0.10]).
        seed: Random seed for any stochastic processes (though OLS is deterministic,
              this is kept for API consistency if needed).
              
    Returns:
        DataFrame with columns: alpha, significant (bool), p_value, coefficient.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10]
    
    logger.info(f"Running alpha sweep for thresholds: {thresholds}")
    
    # Fit the primary model once on the full data
    model_result = fit_primary_model(data)
    
    interaction_term = "news_exposure_z:political_ideology"
    
    if hasattr(model_result, 'params'):
        coeff = model_result.params.get(interaction_term)
        p_val = model_result.pvalues.get(interaction_term)
    elif isinstance(model_result, dict):
        coeff = model_result.get(interaction_term)
        p_val = model_result.get('pvalue') # Assuming dict structure
    else:
        raise ValueError("Could not extract parameters from model result.")
    
    if p_val is None:
        raise ValueError("P-value for interaction term is missing.")
    
    results = []
    for alpha in thresholds:
        is_significant = p_val < alpha
        results.append({
            'alpha': alpha,
            'significant': is_significant,
            'p_value': p_val,
            'coefficient': coeff
        })
    
    return pd.DataFrame(results)


def run_covariate_adjustment(
    data: pd.DataFrame,
    covariates: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Re-fit the model with additional covariates to check robustness.
    
    Args:
        data: Preprocessed dataframe.
        covariates: List of covariate column names (e.g., ['age', 'gender', 'education']).
                    
    Returns:
        DataFrame comparing the primary model and adjusted model coefficients.
    """
    if covariates is None:
        covariates = ['age', 'gender', 'education']
    
    logger.info(f"Running covariate adjustment with: {covariates}")
    
    # Check if covariates exist
    missing = [c for c in covariates if c not in data.columns]
    if missing:
        logger.warning(f"Covariates not found in data: {missing}. Skipping adjustment.")
        return pd.DataFrame()
    
    # Construct formula for adjusted model
    # Primary: IAT_D ~ news_exposure_z * political_ideology
    # Adjusted: IAT_D ~ news_exposure_z * political_ideology + age + gender + education
    
    base_terms = "news_exposure_z * political_ideology"
    cov_terms = " + ".join(covariates)
    full_formula = f"IAT_D_score ~ {base_terms} + {cov_terms}"
    
    try:
        X = sm.add_constant(data[['news_exposure_z', 'political_ideology'] + covariates])
        y = data['IAT_D_score']
        
        # Handle potential collinearity or missing values in the specific subset
        # Ensure no NaNs
        valid_idx = y.dropna().index
        # Check if covariates have NaNs in valid_idx
        for col in covariates + ['news_exposure_z', 'political_ideology']:
            valid_idx = valid_idx.intersection(data[col].dropna().index)
        
        if len(valid_idx) < 10:
            logger.error("Insufficient data for covariate adjustment.")
            return pd.DataFrame()
        
        X_adj = X.loc[valid_idx]
        y_adj = y.loc[valid_idx]
        
        model = sm.OLS(y_adj, X_adj).fit()
        
        # Extract interaction coefficient
        # The interaction term name in statsmodels is usually 'news_exposure_z:political_ideology'
        interaction_name = "news_exposure_z:political_ideology"
        if interaction_name in model.params:
            adj_coeff = model.params[interaction_name]
            adj_pval = model.pvalues[interaction_name]
            adj_se = model.bse[interaction_name]
        else:
            # Fallback if naming differs
            interaction_name = [k for k in model.params.index if 'news_exposure_z' in k and 'political_ideology' in k][0]
            adj_coeff = model.params[interaction_name]
            adj_pval = model.pvalues[interaction_name]
            adj_se = model.bse[interaction_name]
        
        return pd.DataFrame([{
            'model_type': 'covariate_adjusted',
            'interaction_term': interaction_name,
            'coefficient': adj_coeff,
            'p_value': adj_pval,
            'se': adj_se,
            'covariates_added': ', '.join(covariates)
        }])
        
    except Exception as e:
        logger.error(f"Failed to fit covariate adjusted model: {e}")
        return pd.DataFrame()


def save_robustness_results(
    bootstrap_results: pd.DataFrame,
    alpha_sweep_results: pd.DataFrame,
    covariate_results: pd.DataFrame,
    output_path: Optional[Path] = None
):
    """
    Save all robustness metrics to a single CSV file.
    """
    if output_path is None:
        output_path = get_results_path() / "robustness_metrics.csv"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Concatenate if possible, or write separately. 
    # For simplicity in this task, we write a combined file or multiple rows.
    # Since the structures differ, we might write them as separate sections or normalize.
    # Let's create a summary dataframe with a 'metric_type' column.
    
    rows = []
    
    if not bootstrap_results.empty:
        for _, row in bootstrap_results.iterrows():
            r = row.to_dict()
            r['metric_type'] = 'bootstrap'
            rows.append(r)
            
    if not alpha_sweep_results.empty:
        for _, row in alpha_sweep_results.iterrows():
            r = row.to_dict()
            r['metric_type'] = 'alpha_sweep'
            rows.append(r)
            
    if not covariate_results.empty:
        for _, row in covariate_results.iterrows():
            r = row.to_dict()
            r['metric_type'] = 'covariate_adjustment'
            rows.append(r)
            
    if rows:
        final_df = pd.DataFrame(rows)
        final_df.to_csv(output_path, index=False)
        logger.info(f"Robustness metrics saved to {output_path}")
    else:
        logger.warning("No robustness results to save.")

def run_all_robustness_checks(data: pd.DataFrame):
    """
    Orchestrate the full robustness pipeline.
    """
    n_boot = get_bootstrap_count()
    seed = get_analysis_seed()
    
    logger.info("Starting full robustness analysis pipeline.")
    
    # 1. Bootstrap
    bootstrap_res = run_bootstrap_analysis(data, n_bootstrap=n_boot, seed=seed)
    
    # 2. Alpha Sweep
    alpha_res = run_alpha_sweep(data)
    
    # 3. Covariate Adjustment
    cov_res = run_covariate_adjustment(data)
    
    # 4. Save
    save_robustness_results(bootstrap_res, alpha_res, cov_res)
    
    return {
        'bootstrap': bootstrap_res,
        'alpha_sweep': alpha_res,
        'covariate': cov_res
    }