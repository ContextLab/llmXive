"""
Statistical modeling module for the social support resilience study.
Implements OLS regression with interaction terms, heteroskedasticity-consistent
standard errors, and model result extraction.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan

logger = logging.getLogger(__name__)

# Constants
OUTCOMES = ['depression', 'anxiety', 'ptsd']
PREDICTORS = ['social_support', 'harassment_exposure']
COVARIATES = ['age', 'gender', 'education', 'income']
INTERACTION_COL = 'social_support:harassment_exposure'

def load_synthetic_cohort(file_path: str = "data/results/synthetic_cohort.csv") -> pd.DataFrame:
    """Load the synthetic cohort dataset."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Synthetic cohort file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded synthetic cohort with {len(df)} rows and {len(df.columns)} columns")
    return df

def create_interaction_term(df: pd.DataFrame, col1: str = 'social_support', col2: str = 'harassment_exposure') -> pd.DataFrame:
    """Create an interaction term between two columns."""
    df = df.copy()
    interaction_name = f"{col1}:{col2}"
    df[interaction_name] = df[col1] * df[col2]
    logger.debug(f"Created interaction term: {interaction_name}")
    return df

def fit_ols_model(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
    covariates: List[str],
    interaction_term: Optional[str] = None,
    robust: bool = True
) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit an OLS model with optional interaction term and robust standard errors.
    
    Args:
        df: DataFrame containing the data
        outcome: Name of the outcome variable
        predictors: List of main predictor variables
        covariates: List of control variables
        interaction_term: Name of the interaction column (if pre-computed)
        robust: If True, use HC3 robust standard errors
        
    Returns:
        Tuple of (model_results, summary_dict)
    """
    # Prepare design matrix
    features = predictors + covariates
    if interaction_term and interaction_term in df.columns:
        features.append(interaction_term)
    
    # Handle missing values in the selected columns
    cols_to_use = [outcome] + features
    clean_df = df[cols_to_use].dropna()
    
    if len(clean_df) < 10:
        logger.warning(f"Insufficient data for {outcome}: {len(clean_df)} rows after cleaning")
        return None, {}
    
    X = clean_df[features]
    y = clean_df[outcome]
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC3' if robust else 'nonrobust')
    
    # Extract summary
    summary = {
        'outcome': outcome,
        'n_obs': results.nobs,
        'r_squared': results.rsquared,
        'adj_r_squared': results.rsquared_adj,
        'f_pvalue': results.f_pvalue,
        'coefficients': {},
        'std_errors': {},
        'p_values': {},
        'conf_int_lower': {},
        'conf_int_upper': {},
        'robust': robust
    }
    
    for var in features:
        if var in results.params.index:
            summary['coefficients'][var] = float(results.params[var])
            summary['std_errors'][var] = float(results.bse[var])
            summary['p_values'][var] = float(results.pvalues[var])
            conf_int = results.conf_int()
            summary['conf_int_lower'][var] = float(conf_int.loc[var, 0])
            summary['conf_int_upper'][var] = float(conf_int.loc[var, 1])
    
    return results, summary

def extract_model_results(results: Any, outcome: str) -> Dict[str, Any]:
    """Extract detailed results from a fitted model."""
    if results is None:
        return {}
    
    return {
        'outcome': outcome,
        'n_obs': results.nobs,
        'r_squared': results.rsquared,
        'adj_r_squared': results.rsquared_adj,
        'f_statistic': results.fvalue,
        'f_pvalue': results.f_pvalue,
        'params': results.params.to_dict(),
        'bse': results.bse.to_dict(),
        'pvalues': results.pvalues.to_dict(),
        'conf_int': results.conf_int().to_dict()
    }

def run_all_models(
    df: pd.DataFrame,
    outcomes: List[str] = None,
    robust: bool = True,
    include_interaction: bool = True
) -> List[Dict[str, Any]]:
    """
    Run OLS models for all specified outcomes.
    
    Args:
        df: The synthetic cohort DataFrame
        outcomes: List of outcome variables to model
        robust: Use robust standard errors
        include_interaction: Include interaction term if available
        
    Returns:
        List of result dictionaries for each outcome
    """
    if outcomes is None:
        outcomes = OUTCOMES
    
    results_list = []
    
    # Pre-compute interaction if needed
    if include_interaction:
        df = create_interaction_term(df)
        interaction_name = INTERACTION_COL
    else:
        interaction_name = None
    
    for outcome in outcomes:
        if outcome not in df.columns:
            logger.warning(f"Outcome variable '{outcome}' not found in dataset, skipping")
            continue
        
        logger.info(f"Fitting model for outcome: {outcome}")
        
        try:
            _, summary = fit_ols_model(
                df=df,
                outcome=outcome,
                predictors=PREDICTORS,
                covariates=COVARIATES,
                interaction_term=interaction_name,
                robust=robust
            )
            
            if summary:
                results_list.append(summary)
                logger.info(f"Model for {outcome} completed: R²={summary['r_squared']:.4f}, F-p={summary['f_pvalue']:.4f}")
            else:
                logger.warning(f"Model for {outcome} returned empty summary")
                
        except Exception as e:
            logger.error(f"Failed to fit model for {outcome}: {str(e)}", exc_info=True)
    
    return results_list

def main():
    """Main entry point for running models."""
    logging.basicConfig(level=logging.INFO)
    
    # Load data
    try:
        df = load_synthetic_cohort()
    except FileNotFoundError as e:
        logger.error(str(e))
        return []
    
    # Run models
    results = run_all_models(df)
    
    # Save results to memory (for downstream tasks) or return
    return results

if __name__ == "__main__":
    main()
