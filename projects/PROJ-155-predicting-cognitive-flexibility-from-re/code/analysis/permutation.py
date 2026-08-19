"""
Permutation test implementation for User Story 3.

This module provides functions to perform a permutation test to validate the
statistical significance of the association between RSFC variability and cognitive flexibility.
It handles the shuffling of labels, calculation of the null distribution, and p-value estimation.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from scipy import stats
from code.config import set_seed

logger = logging.getLogger(__name__)


def calculate_test_statistic(
    df: pd.DataFrame,
    target_col: str,
    predictor_col: str,
    covariate_cols: List[str]
) -> float:
    """
    Calculate the test statistic (slope of the predictor) for the regression model.
    
    The model is: target ~ predictor + covariates
    Returns the coefficient (beta) for the predictor variable.
    
    Args:
        df: DataFrame containing the data.
        target_col: Name of the target variable column (e.g., 'Flexibility_Score').
        predictor_col: Name of the predictor variable column (e.g., 'Variability_Metric').
        covariate_cols: List of covariate column names (e.g., ['Age', 'Sex', 'Mean_FD']).
        
    Returns:
        float: The regression coefficient (slope) for the predictor.
    """
    # Prepare features
    features = [predictor_col] + covariate_cols
    X = df[features].values
    y = df[target_col].values
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    
    # Fit linear regression using least squares
    try:
        # (X^T X)^-1 X^T y
        coeffs, _, _, _ = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        # The coefficient for the predictor is at index 1 (index 0 is intercept)
        predictor_idx = 1
        return float(coeffs[predictor_idx])
    except np.linalg.LinAlgError:
        logger.error("Singular matrix in regression calculation. Returning NaN.")
        return np.nan


def run_permutation_test(
    df: pd.DataFrame,
    target_col: str,
    predictor_col: str,
    covariate_cols: List[str],
    n_permutations: int = 10000,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a permutation test to assess the significance of the predictor's association with the target.
    
    The test shuffles the target variable (or the predictor relative to target) to generate a null
    distribution of the test statistic. The p-value is the proportion of null statistics that are
    as extreme or more extreme than the observed statistic.
    
    Args:
        df: DataFrame containing the data.
        target_col: Name of the target variable column.
        predictor_col: Name of the predictor variable column.
        covariate_cols: List of covariate column names.
        n_permutations: Number of permutations to run.
        random_seed: Random seed for reproducibility.
        
    Returns:
        dict: A dictionary containing:
            - 'observed_statistic': The test statistic from the original data.
            - 'null_distribution': Array of test statistics from permuted data.
            - 'p_value': The calculated p-value.
            - 'is_significant': Boolean indicating if p_value < 0.05.
    """
    if random_seed is not None:
        set_seed(random_seed)
    
    logger.info(f"Starting permutation test with {n_permutations} iterations.")
    logger.info(f"Target: {target_col}, Predictor: {predictor_col}, Covariates: {covariate_cols}")
    
    # Calculate observed statistic
    observed_stat = calculate_test_statistic(df, target_col, predictor_col, covariate_cols)
    
    if np.isnan(observed_stat):
        logger.error("Observed statistic is NaN. Skipping permutation test.")
        return {
            'observed_statistic': np.nan,
            'null_distribution': np.array([]),
            'p_value': np.nan,
            'is_significant': False
        }
    
    logger.info(f"Observed statistic: {observed_stat:.6f}")
    
    # Generate null distribution
    null_distribution = np.zeros(n_permutations)
    n_subjects = len(df)
    target_values = df[target_col].values
    
    # Covariates and predictor remain fixed in this permutation strategy
    # We shuffle the target variable relative to the predictors
    # This tests the null hypothesis that the target is independent of the predictors
    
    for i in range(n_permutations):
        # Shuffle target values
        shuffled_target = np.random.permutation(target_values)
        
        # Create a temporary dataframe with shuffled target
        # We only need the columns relevant for the statistic calculation
        # but we must keep the structure consistent
        temp_df = df.copy()
        temp_df[target_col] = shuffled_target
        
        # Calculate statistic on shuffled data
        perm_stat = calculate_test_statistic(temp_df, target_col, predictor_col, covariate_cols)
        null_distribution[i] = perm_stat
        
        if (i + 1) % 1000 == 0:
            logger.debug(f"Completed {i + 1}/{n_permutations} permutations.")
    
    # Calculate p-value
    # Two-tailed test: proportion of |null| >= |observed|
    # Or one-tailed: proportion of null >= observed (if we expect positive correlation)
    # Given the research hypothesis (variability predicts flexibility), we assume a directional test.
    # However, standard permutation tests often use two-tailed for robustness.
    # We will use the standard definition: p = (count(|null| >= |observed|) + 1) / (n + 1)
    
    # For a directional hypothesis (positive correlation), we can use:
    # p = (count(null >= observed) + 1) / (n + 1)
    # Let's use the two-tailed approach for robustness unless specified otherwise.
    # But looking at the task description, it implies a specific association.
    # We'll calculate the one-tailed p-value (greater than or equal) as it's common in regression
    # where we care about the sign of the coefficient.
    
    # Count how many null stats are >= observed stat
    count_extreme = np.sum(null_distribution >= observed_stat)
    p_value = (count_extreme + 1) / (n_permutations + 1)
    
    # Check significance
    is_significant = p_value < 0.05
    
    logger.info(f"Permutation test complete. P-value: {p_value:.6f}, Significant: {is_significant}")
    
    return {
        'observed_statistic': observed_stat,
        'null_distribution': null_distribution,
        'p_value': p_value,
        'is_significant': is_significant
    }