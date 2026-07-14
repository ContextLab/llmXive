"""
Sensitivity analysis module.
Tests robustness of results with alternative model specifications and stratification.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def load_synthetic_cohort(file_path: str = "data/results/synthetic_cohort.csv") -> pd.DataFrame:
    """Load the synthetic cohort."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cohort file not found: {path}")
    return pd.read_csv(path)

def load_baseline_results(file_path: str = "data/results/regression_results.csv") -> pd.DataFrame:
    """Load baseline regression results."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Baseline results not found: {path}. Returning empty DataFrame.")
        return pd.DataFrame()
    return pd.read_csv(path)

def fit_ols_model_continuous(
    df: pd.DataFrame,
    outcome: str,
    continuous_var: str = 'harassment_severity',
    covariates: List[str] = None,
    robust: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Fit OLS model using continuous harassment severity instead of binary exposure.
    
    Args:
        df: DataFrame
        outcome: Outcome variable name
        continuous_var: Name of continuous harassment variable
        covariates: Control variables
        robust: Use robust SEs
        
    Returns:
        Model summary dictionary or None
    """
    if covariates is None:
        covariates = ['age', 'gender', 'education', 'income', 'social_support']
    
    if outcome not in df.columns or continuous_var not in df.columns:
        logger.warning(f"Missing variables for sensitivity model: {outcome} or {continuous_var}")
        return None
    
    cols = [outcome, continuous_var] + covariates
    clean_df = df[cols].dropna()
    
    if len(clean_df) < 10:
        return None
    
    X = clean_df[covariates + [continuous_var]]
    y = clean_df[outcome]
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC3' if robust else 'nonrobust')
    
    return {
        'outcome': outcome,
        'model_type': 'continuous_harassment',
        'n_obs': results.nobs,
        'r_squared': results.rsquared,
        'coefficients': results.params.to_dict(),
        'p_values': results.pvalues.to_dict(),
        'harassment_coef': float(results.params[continuous_var]),
        'harassment_p': float(results.pvalues[continuous_var])
    }

def stratify_by_platform(
    df: pd.DataFrame,
    platform_col: str = 'platform',
    min_count: int = 10
) -> Dict[str, pd.DataFrame]:
    """
    Stratify data by platform, keeping top 3 and grouping others as 'Other'.
    
    Args:
        df: DataFrame
        platform_col: Name of platform column
        min_count: Minimum rows required to keep a platform
        
    Returns:
        Dictionary of platform -> DataFrame
    """
    if platform_col not in df.columns:
        logger.warning(f"Platform column '{platform_col}' not found. Skipping stratification.")
        return {}
    
    # Count platforms
    counts = df[platform_col].value_counts()
    
    if len(counts) < 2:
        logger.warning(f"Less than 2 platforms found. Skipping stratification.")
        return {}
    
    # Keep top 3
    top_platforms = counts.head(3).index.tolist()
    
    # Group others
    df = df.copy()
    df[platform_col] = df[platform_col].apply(lambda x: x if x in top_platforms else 'Other')
    
    # Split
    strata = {}
    for platform in df[platform_col].unique():
        subset = df[df[platform_col] == platform]
        if len(subset) >= min_count:
            strata[platform] = subset
            logger.info(f"Stratum '{platform}': {len(subset)} rows")
        else:
            logger.warning(f"Stratum '{platform}' too small ({len(subset)} < {min_count}), skipping")
    
    return strata

def run_sensitivity_analysis(
    df: pd.DataFrame,
    outcomes: List[str] = None,
    baseline_results: pd.DataFrame = None
) -> List[Dict[str, Any]]:
    """
    Run full sensitivity analysis.
    
    Args:
        df: Synthetic cohort
        outcomes: List of outcomes to test
        baseline_results: Optional baseline for comparison
        
    Returns:
        List of sensitivity result dictionaries
    """
    if outcomes is None:
        outcomes = ['depression', 'anxiety', 'ptsd']
    
    results = []
    
    # 1. Continuous harassment model
    logger.info("Running continuous harassment sensitivity analysis...")
    for outcome in outcomes:
        if outcome not in df.columns:
            continue
        
        res = fit_ols_model_continuous(df, outcome)
        if res:
            results.append(res)
    
    # 2. Platform stratification
    logger.info("Running platform stratification analysis...")
    strata = stratify_by_platform(df)
    
    for platform, platform_df in strata.items():
        for outcome in outcomes:
            if outcome not in platform_df.columns:
                continue
            
            # Fit standard model on stratum
            covariates = ['age', 'gender', 'education', 'income', 'social_support', 'harassment_exposure']
            cols = [outcome] + covariates
            clean_df = platform_df[cols].dropna()
            
            if len(clean_df) < 10:
                continue
            
            X = sm.add_constant(clean_df[covariates])
            y = clean_df[outcome]
            
            try:
                model = sm.OLS(y, X).fit(cov_type='HC3')
                interaction_col = 'social_support:harassment_exposure'
                
                if interaction_col in model.params.index:
                    coef = float(model.params[interaction_col])
                    pval = float(model.pvalues[interaction_col])
                else:
                    coef = np.nan
                    pval = np.nan
                
                results.append({
                    'outcome': outcome,
                    'model_type': f'stratified_{platform}',
                    'n_obs': model.nobs,
                    'r_squared': model.rsquared,
                    'interaction_coef': coef,
                    'interaction_p': pval
                })
            except Exception as e:
                logger.warning(f"Failed to fit stratified model for {platform}/{outcome}: {e}")
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str = "data/results/sensitivity_analysis.csv"):
    """Save sensitivity analysis results to CSV."""
    if not results:
        logger.warning("No results to save.")
        return
    
    df = pd.DataFrame(results)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity results to {output_path}")

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        df = load_synthetic_cohort()
    except FileNotFoundError as e:
        logger.error(str(e))
        return []
    
    results = run_sensitivity_analysis(df)
    save_results(results)
    
    return results

if __name__ == "__main__":
    main()
