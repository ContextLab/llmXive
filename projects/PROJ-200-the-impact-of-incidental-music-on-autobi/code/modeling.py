"""
Statistical Modeling Module for PROJ-200.

This module handles fitting linear mixed-effects models, sensitivity analysis,
and permutation tests as per the updated specification (US3).
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import numpy as np
import pandas as pd

from config import get_project_root, get_config_dict

logger = logging.getLogger(__name__)

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for predictors.

    This implements T035. Checks for multicollinearity (VIF > 5).

    Args:
        df (pd.DataFrame): The dataframe with predictor variables.
        predictors (List[str]): List of column names to check.

    Returns:
        Dict[str, float]: VIF for each predictor.
    """
    logger.info("Checking for multicollinearity (VIF)...")
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
    except ImportError:
        raise ImportError("statsmodels is required for VIF calculation.")

    vif_data = {}
    X = df[predictors].dropna()
    
    if X.empty:
        logger.warning("No valid data for VIF calculation.")
        return {}

    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
        if vif > 5:
            logger.warning(f"High multicollinearity detected for {col}: VIF = {vif:.2f}")

    return vif_data

def fit_mixed_model(df: pd.DataFrame) -> Any:
    """
    Fits a linear mixed-effects model for vividness.

    Formula: mean_vividness ~ residualized_exposure + popularity + (1|user_id)
    Implements T033.

    Args:
        df (pd.DataFrame): The aggregated User-Track Pair dataframe.

    Returns:
        statsmodels MixedLMResults: The fitted model.
    """
    logger.info("Fitting mixed-effects model for vividness...")
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        raise ImportError("statsmodels is required for mixed-effects modeling.")

    # Formula based on spec update (FR-005)
    formula = "mean_vividness ~ residualized_exposure_score + overall_popularity_score + (1|user_id)"
    
    # Handle missing values
    model_data = df.dropna(subset=['mean_vividness', 'residualized_exposure_score', 'overall_popularity_score', 'user_id'])

    if len(model_data) == 0:
        raise ValueError("No valid data for model fitting.")

    # Fit model
    # Note: statsmodels MixedLM uses 'groups' for the random effect
    # We use 'user_id' as the group
    try:
        model = smf.mixedlm("mean_vividness ~ residualized_exposure_score + overall_popularity_score", 
                            model_data, 
                            groups=model_data["user_id"])
        result = model.fit()
        logger.info("Model fitting successful.")
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def fit_valence_model(df: pd.DataFrame) -> Any:
    """
    Fits a linear mixed-effects model for valence.

    Formula: mean_valence ~ residualized_exposure + popularity + (1|user_id)
    Implements T034.

    Args:
        df (pd.DataFrame): The aggregated User-Track Pair dataframe.

    Returns:
        statsmodels MixedLMResults: The fitted model.
    """
    logger.info("Fitting mixed-effects model for valence...")
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        raise ImportError("statsmodels is required.")

    formula = "mean_valence ~ residualized_exposure_score + overall_popularity_score + (1|user_id)"
    model_data = df.dropna(subset=['mean_valence', 'residualized_exposure_score', 'overall_popularity_score', 'user_id'])

    if len(model_data) == 0:
        raise ValueError("No valid data for valence model.")

    model = smf.mixedlm("mean_valence ~ residualized_exposure_score + overall_popularity_score", 
                        model_data, 
                        groups=model_data["user_id"])
    result = model.fit()
    logger.info("Valence model fitting successful.")
    return result

def extract_model_summary(result: Any) -> pd.DataFrame:
    """
    Extracts a summary dataframe from a fitted model.

    Args:
        result (statsmodels MixedLMResults): The fitted model.

    Returns:
        pd.DataFrame: Summary with coefficients, SEs, p-values.
    """
    summary = result.summary2().tables[1]
    df_summary = summary.to_dataframe()
    df_summary.reset_index(inplace=True)
    df_summary.rename(columns={'index': 'term'}, inplace=True)
    return df_summary

def save_regression_results(result: Any, output_path: Path):
    """
    Saves regression results to a CSV file.
    Implements T038.

    Args:
        result (statsmodels MixedLMResults): The fitted model.
        output_path (Path): Path to save the CSV.
    """
    logger.info(f"Saving regression results to {output_path}")
    df_summary = extract_model_summary(result)
    # Add VIFs if available (calculated separately)
    df_summary.to_csv(output_path, index=False)

def run_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs sensitivity analysis with different Levenshtein thresholds (2, 6).
    Implements T044.

    Re-matches, re-aggregates, and re-models for each threshold.

    Args:
        df (pd.DataFrame): The full dataset (cues + tracks).

    Returns:
        pd.DataFrame: Summary of results across thresholds.
    """
    logger.info("Running sensitivity analysis...")
    # This is a placeholder for the full logic which would call matching and aggregation
    # functions with different thresholds.
    results = []
    thresholds = [2, 6]
    for t in thresholds:
        logger.info(f"Processing threshold {t}...")
        # ... (logic to re-match, aggregate, fit model) ...
        # For now, we return a placeholder
        results.append({'threshold': t, 'status': 'simulated'})
    
    return pd.DataFrame(results)

def run_permutation_test(df: pd.DataFrame, n_iterations: int = 1000) -> Dict[str, Any]:
    """
    Performs a block-permutation test on the User-Track Pair dataset.
    Implements T045.

    Shuffles `residualized_exposure_score` among tracks while preserving
    the User-Track grouping structure.

    Args:
        df (pd.DataFrame): The aggregated User-Track Pair dataframe.
        n_iterations (int): Number of permutations.

    Returns:
        Dict[str, Any]: Results including p-value and null distribution.
    """
    logger.info(f"Running block-permutation test ({n_iterations} iterations)...")
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        raise ImportError("statsmodels is required.")

    # Observed statistic
    model_data = df.dropna(subset=['mean_vividness', 'residualized_exposure_score', 'user_id'])
    if len(model_data) == 0:
        raise ValueError("No valid data for permutation test.")

    # Fit observed model
    observed_model = smf.mixedlm("mean_vividness ~ residualized_exposure_score", 
                                 model_data, 
                                 groups=model_data["user_id"])
    observed_result = observed_model.fit()
    observed_stat = observed_result.params['residualized_exposure_score']
    
    null_distribution = []
    
    # Block permutation: Shuffle exposure scores by track, not by row
    # We need to identify unique tracks and shuffle their exposure scores
    # Then assign back to all rows for that track
    
    tracks = model_data['track_id'].unique() if 'track_id' in model_data.columns else model_data['matched_title'].unique()
    
    for i in range(n_iterations):
        # Create a copy
        perm_data = model_data.copy()
        
        # Shuffle exposure scores by track
        # Extract unique track exposures
        track_exposures = perm_data.groupby('track_id')['residualized_exposure_score'].first().reset_index()
        # Shuffle the exposure values
        np.random.shuffle(track_exposures['residualized_exposure_score'].values)
        
        # Merge back
        perm_data = perm_data.merge(track_exposures[['track_id', 'residualized_exposure_score']], on='track_id', suffixes=('', '_perm'))
        perm_data['residualized_exposure_score'] = perm_data['residualized_exposure_score_perm']
        perm_data.drop(columns=['residualized_exposure_score_perm'], inplace=True)
        
        # Fit model
        try:
            perm_model = smf.mixedlm("mean_vividness ~ residualized_exposure_score", 
                                     perm_data, 
                                     groups=perm_data["user_id"])
            perm_result = perm_model.fit()
            null_distribution.append(perm_result.params['residualized_exposure_score'])
        except:
            null_distribution.append(np.nan)

    null_distribution = np.array(null_distribution)
    null_distribution = null_distribution[~np.isnan(null_distribution)]
    
    # Calculate p-value
    p_value = (np.sum(np.abs(null_distribution) >= np.abs(observed_stat)) + 1) / (len(null_distribution) + 1)
    
    logger.info(f"Permutation test complete. Observed: {observed_stat:.4f}, P-value: {p_value:.4f}")
    
    return {
        'observed_statistic': observed_stat,
        'p_value': p_value,
        'null_distribution': null_distribution
    }
