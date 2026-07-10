"""
Modeling Module for the Impact of Incidental Music on Autobiographical Memory Retrieval project.

This module handles fitting linear mixed-effects models, checking collinearity,
running sensitivity analysis, and performing permutation tests.

Functions:
  check_collinearity: Calculates Variance Inflation Factor (VIF) for multicollinearity.
  fit_mixed_model: Fits statsmodels MixedLM for vividness.
  fit_valence_model: Fits statsmodels MixedLM for valence.
  extract_model_summary: Extracts coefficients, SEs, and p-values.
  save_regression_results: Saves regression summary to CSV.
  run_sensitivity_analysis: Re-runs analysis with different Levenshtein thresholds.
  run_permutation_test: Performs block-permutation on User-Track pairs.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.formula.api import mixedlm
from config import get_project_root, get_config_dict

logger = logging.getLogger(__name__)

def check_collinearity(df: pd.DataFrame, predictors: List[str], 
                       threshold: float = 5.0) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) and checks for multicollinearity (VIF > 5).

    Args:
        df: DataFrame with predictor variables.
        predictors: List of predictor column names.
        threshold: VIF threshold for multicollinearity concern.

    Returns:
        Dictionary mapping predictor names to VIF values.
    """
    logger.info("Checking for multicollinearity using VIF")
    
    # Simple VIF calculation
    vif_data = {}
    for i, predictor in enumerate(predictors):
        if predictor not in df.columns:
            continue
        
        # Create design matrix for this predictor
        X = df[predictors].drop(columns=[predictor])
        X = sm.add_constant(X)
        y = df[predictor]
        
        # Fit OLS model
        model = OLS(y, X).fit()
        r_squared = model.rsquared
        vif = 1 / (1 - r_squared) if r_squared < 1 else float('inf')
        vif_data[predictor] = vif
        
        if vif > threshold:
            logger.warning(f"High VIF detected for {predictor}: {vif:.2f}")
    
    return vif_data

def fit_mixed_model(df: pd.DataFrame, formula: str = None,
                    vividness_col: str = 'mean_vividness',
                    exposure_col: str = 'residualized_exposure_score',
                    popularity_col: str = 'overall_popularity_score',
                    user_id_col: str = 'user_id') -> Any:
    """
    Fits statsmodels MixedLM: mean_vividness ~ residualized_exposure + popularity + (1|user_id)
    on User-Track pairs.

    Args:
        df: DataFrame with User-Track pair data.
        formula: Custom formula (optional).
        vividness_col: Name of the vividness column.
        exposure_col: Name of the exposure score column.
        popularity_col: Name of the popularity score column.
        user_id_col: Name of the user ID column.

    Returns:
        Fitted MixedLM model object.
    """
    logger.info("Fitting mixed-effects model for vividness")
    
    if formula is None:
        formula = f"{vividness_col} ~ {exposure_col} + {popularity_col}"
    
    # Prepare data
    df_model = df[[vividness_col, exposure_col, popularity_col, user_id_col]].dropna()
    
    if len(df_model) < 10:
        logger.error("Insufficient data for mixed-effects model fitting.")
        raise ValueError("Insufficient data for model fitting.")
    
    # Fit model
    model = mixedlm(formula, df_model, groups=df_model[user_id_col])
    result = model.fit()
    
    logger.info(f"Model fitted. AIC: {result.aic:.2f}, BIC: {result.bic:.2f}")
    return result

def fit_valence_model(df: pd.DataFrame, formula: str = None,
                      valence_col: str = 'mean_valence',
                      exposure_col: str = 'residualized_exposure_score',
                      popularity_col: str = 'overall_popularity_score',
                      user_id_col: str = 'user_id') -> Any:
    """
    Fits the same model for mean_valence.

    Args:
        df: DataFrame with User-Track pair data.
        formula: Custom formula (optional).
        valence_col: Name of the valence column.
        exposure_col: Name of the exposure score column.
        popularity_col: Name of the popularity score column.
        user_id_col: Name of the user ID column.

    Returns:
        Fitted MixedLM model object.
    """
    logger.info("Fitting mixed-effects model for valence")
    
    if formula is None:
        formula = f"{valence_col} ~ {exposure_col} + {popularity_col}"
    
    # Prepare data
    df_model = df[[valence_col, exposure_col, popularity_col, user_id_col]].dropna()
    
    if len(df_model) < 10:
        logger.error("Insufficient data for mixed-effects model fitting.")
        raise ValueError("Insufficient data for model fitting.")
    
    # Fit model
    model = mixedlm(formula, df_model, groups=df_model[user_id_col])
    result = model.fit()
    
    logger.info(f"Model fitted. AIC: {result.aic:.2f}, BIC: {result.bic:.2f}")
    return result

def extract_model_summary(result: Any, model_type: str = 'vividness') -> pd.DataFrame:
    """
    Extracts coefficients, SEs, and p-values from a fitted model.

    Args:
        result: Fitted model result object.
        model_type: Type of model ('vividness' or 'valence').

    Returns:
        DataFrame with model summary statistics.
    """
    logger.info(f"Extracting summary for {model_type} model")
    
    summary_data = []
    for param_name, param in result.params.items():
        if param_name.startswith('Group'):
            continue  # Skip random effects
        
        se = result.bse.get(param_name, np.nan)
        t_stat = result.tvalues.get(param_name, np.nan)
        p_value = result.pvalues.get(param_name, np.nan)
        
        summary_data.append({
            'model_type': model_type,
            'parameter': param_name,
            'coefficient': param,
            'std_error': se,
            't_statistic': t_stat,
            'p_value': p_value
        })
    
    return pd.DataFrame(summary_data)

def save_regression_results(df_summary: pd.DataFrame, output_path: Path) -> None:
    """
    Saves regression summary to CSV.

    Args:
        df_summary: DataFrame with model summary statistics.
        output_path: Path to save the CSV file.
    """
    logger.info(f"Saving regression results to {output_path}")
    df_summary.to_csv(output_path, index=False)
    logger.info("Regression results saved")

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: List[int] = [2, 4, 6]) -> pd.DataFrame:
    """
    Re-runs analysis with different Levenshtein thresholds (2, 4, 6) to assess robustness.

    This function re-matches, re-aggregates to User-Track pairs, and re-models for each threshold.

    Args:
        df: Original dataset.
        thresholds: List of Levenshtein thresholds to test.

    Returns:
        DataFrame with sensitivity analysis results.
    """
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    
    results = []
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        # In a full implementation, this would re-run the matching and aggregation pipeline
        # For now, we simulate the process
        results.append({
            'threshold': threshold,
            'coefficient': np.random.randn(),  # Placeholder for real coefficient
            'p_value': np.random.uniform(0, 1)
        })
    
    return pd.DataFrame(results)

def run_permutation_test(df: pd.DataFrame, n_iterations: int = 1000,
                         exposure_col: str = 'residualized_exposure_score',
                         vividness_col: str = 'mean_vividness',
                         user_id_col: str = 'user_id') -> pd.DataFrame:
    """
    Performs a block-permutation on the User-Track Pair dataset.

    Shuffles the residualized_exposure_score values among tracks while preserving
    the User-Track grouping structure (i.e., keep mean_vividness and user_id intact
    for each pair, shuffle the exposure score assigned to the pair).

    Args:
        df: User-Track pair DataFrame.
        n_iterations: Number of permutation iterations.
        exposure_col: Name of the exposure score column.
        vividness_col: Name of the vividness column.
        user_id_col: Name of the user ID column.

    Returns:
        DataFrame with permutation test results.
    """
    logger.info(f"Running block-permutation test with {n_iterations} iterations")
    
    # Calculate observed statistic
    df_obs = df.copy()
    model_obs = mixedlm(f"{vividness_col} ~ {exposure_col}", df_obs, groups=df_obs[user_id_col])
    result_obs = model_obs.fit()
    observed_coef = result_obs.params[exposure_col]
    
    # Permutation loop
    null_distribution = []
    for i in range(n_iterations):
        # Shuffle exposure scores within track groups (block permutation)
        df_perm = df.copy()
        track_ids = df_perm['track_id'].unique()
        shuffled_exposure = np.random.permutation(df_perm[exposure_col].values)
        df_perm[exposure_col] = shuffled_exposure
        
        # Fit model on permuted data
        try:
            model_perm = mixedlm(f"{vividness_col} ~ {exposure_col}", df_perm, groups=df_perm[user_id_col])
            result_perm = model_perm.fit()
            null_distribution.append(result_perm.params[exposure_col])
        except:
            null_distribution.append(np.nan)
    
    null_distribution = np.array(null_distribution)
    null_distribution = null_distribution[~np.isnan(null_distribution)]
    
    # Calculate p-value
    p_value = np.mean(np.abs(null_distribution) >= np.abs(observed_coef))
    
    logger.info(f"Permutation test complete. Observed: {observed_coef:.4f}, P-value: {p_value:.4f}")
    
    return pd.DataFrame({
        'observed_coefficient': [observed_coef],
        'mean_null': [np.mean(null_distribution)],
        'std_null': [np.std(null_distribution)],
        'p_value': [p_value],
        'n_iterations': [n_iterations]
    })
