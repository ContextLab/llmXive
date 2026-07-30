import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.bootstrap import _Bootstrapper
from statsmodels.stats.weightstats import _tconfint_generic

from logger import get_logger
from analysis.bootstrap_ci import load_seed_config

# Configure logging
logger = get_logger(__name__)

# Constants
BOOTSTRAP_RESAMPLES = 1000
DRY_RUN_RESAMPLES = 10
MAX_BOOTSTRAP_TIME_HOURS = 5.0
MAX_BOOTSTRAP_TIME_SECONDS = MAX_BOOTSTRAP_TIME_HOURS * 3600

def load_synthetic_cohort(path: str = "data/results/analysis_cohort.csv") -> pd.DataFrame:
    """Load the analysis cohort from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis cohort not found at {path}. Run preprocessing pipeline first.")
    return pd.read_csv(path)

def create_interaction_term(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """Create an interaction term between two columns."""
    df = df.copy()
    interaction_name = f"{col1}:{col2}"
    if interaction_name not in df.columns:
        df[interaction_name] = df[col1] * df[col2]
    return df

def fit_ols_model(df: pd.DataFrame, outcome: str, predictors: List[str], 
                  robust: bool = True) -> Optional[sm.OLSResults]:
    """Fit an OLS model with optional HC3 robust standard errors."""
    try:
        X = df[predictors]
        y = df[outcome]
        
        # Drop rows with NaN in relevant columns
        mask = ~(X.isna().any(axis=1) | y.isna())
        X_clean = X[mask]
        y_clean = y[mask]
        
        if len(X_clean) < 30:
            logger.warning(f"Not enough samples for {outcome} after dropping NaNs.")
            return None

        X_const = sm.add_constant(X_clean)
        model = sm.OLS(y_clean, X_const)
        results = model.fit()

        if robust:
            # HC3 robust standard errors
            results_robust = results.get_robustcov_results(cov_type='HC3')
            return results_robust
        return results
    except Exception as e:
        logger.error(f"Failed to fit OLS model for {outcome}: {e}")
        return None

def extract_model_results(results: sm.OLSResults, outcome: str) -> Dict[str, Any]:
    """Extract key statistics from a fitted model."""
    params = results.params
    conf_int = results.conf_int()
    
    interaction_term = f"SocialSupport:HarassmentExposure"
    interaction_idx = params.index.get_loc(interaction_term) if interaction_term in params.index else None
    
    result = {
        "outcome": outcome,
        "coefficients": params.to_dict(),
        "p_values": results.pvalues.to_dict(),
        "interaction_coefficient": params[interaction_term] if interaction_term in params.index else None,
        "interaction_p_value": results.pvalues[interaction_term] if interaction_term in results.pvalues.index else None,
        "r_squared": results.rsquared,
        "n_obs": results.nobs
    }
    
    if interaction_idx is not None:
        result["interaction_ci_lower"] = conf_int.iloc[interaction_idx, 0]
        result["interaction_ci_upper"] = conf_int.iloc[interaction_idx, 1]
        
    return result

def estimate_bootstrap_runtime(df: pd.DataFrame, outcome: str, predictors: List[str], 
                               n_resamples: int = DRY_RUN_RESAMPLES) -> float:
    """
    Perform a dry-run bootstrap to estimate the time per resample.
    Returns the estimated time in seconds for the full number of resamples.
    """
    logger.info(f"Running bootstrap feasibility check for {outcome} with {n_resamples} resamples...")
    
    X = df[predictors]
    y = df[outcome]
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask]
    y_clean = y[mask]
    
    if len(X_clean) < 30:
        logger.warning(f"Insufficient data for bootstrap check on {outcome}.")
        return float('inf')

    X_const = sm.add_constant(X_clean)
    base_model = sm.OLS(y_clean, X_const)
    
    start_time = time.time()
    
    # We use a simplified loop to mimic the statsmodels bootstrap behavior without full overhead
    # to get a raw timing estimate.
    try:
        # Fit once to ensure model is valid
        base_model.fit()
        
        # Perform dry run
        for _ in range(n_resamples):
            # Simple random sampling with replacement
            indices = np.random.choice(len(X_clean), size=len(X_clean), replace=True)
            X_boot = X_const.iloc[indices]
            y_boot = y_clean.iloc[indices]
            
            boot_model = sm.OLS(y_boot, X_boot)
            boot_res = boot_model.fit()
            
            # Just check if it fits, don't store everything to keep overhead low
            if boot_res.params is None:
                raise ValueError("Model failed to fit on bootstrap sample")
                
    except Exception as e:
        logger.error(f"Bootstrap dry run failed: {e}")
        return float('inf')
        
    elapsed = time.time() - start_time
    time_per_resample = elapsed / n_resamples
    total_estimated_time = time_per_resample * BOOTSTRAP_RESAMPLES
    
    logger.info(f"Bootstrap dry run completed in {elapsed:.2f}s. "
                f"Estimated time for {BOOTSTRAP_RESAMPLES} resamples: {total_estimated_time:.2f}s "
                f"({total_estimated_time/3600:.2f} hours).")
                
    return total_estimated_time

def run_all_models(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Run OLS models for all outcomes and return results."""
    outcomes = ["depression", "anxiety", "ptsd"]
    # Filter out outcomes that don't exist in the dataframe
    outcomes = [o for o in outcomes if o in df.columns]
    
    if not outcomes:
        raise ValueError("No valid outcome variables found in the cohort.")
        
    predictors = ["SocialSupport", "HarassmentExposure", "SocialSupport:HarassmentExposure", 
                  "age", "gender", "education", "income"]
    # Ensure predictors exist
    predictors = [p for p in predictors if p in df.columns]
    
    if "SocialSupport:HarassmentExposure" not in predictors:
        df = create_interaction_term(df, "SocialSupport", "HarassmentExposure")
        
    all_results = []
    
    for outcome in outcomes:
        logger.info(f"Fitting model for outcome: {outcome}")
        
        # Pre-flight Bootstrap Feasibility Check (Task T045)
        estimated_time = estimate_bootstrap_runtime(df, outcome, predictors)
        
        if estimated_time > MAX_BOOTSTRAP_TIME_SECONDS:
            warning_msg = f"W-SLOW-BOOT-001: Estimated bootstrap time ({estimated_time:.1f}s) exceeds limit ({MAX_BOOTSTRAP_TIME_SECONDS}s). " \
                          f"Proceeding with caution. Consider reducing resamples or using normal approximation if spec allows."
            logger.warning(warning_msg)
            # We do not halt, but we log the warning. The spec requires the check and log.
            # The actual execution will proceed, but the warning is the critical part.
        
        results = fit_ols_model(df, outcome, predictors, robust=True)
        if results:
            extracted = extract_model_results(results, outcome)
            all_results.append(extracted)
        else:
            logger.warning(f"Skipping {outcome} due to model fitting failure.")
            
    return all_results

def main():
    """Main entry point for the models module."""
    logger.info("Starting model fitting and bootstrap feasibility check...")
    
    # Load data
    cohort_path = "data/results/analysis_cohort.csv"
    if not os.path.exists(cohort_path):
        logger.error(f"Cohort file not found: {cohort_path}")
        return
        
    df = load_synthetic_cohort(cohort_path)
    
    # Run models
    results = run_all_models(df)
    
    logger.info(f"Completed fitting {len(results)} models.")
    
    # Save results if needed (handled by save_regression_results.py usually)
    return results

if __name__ == "__main__":
    main()