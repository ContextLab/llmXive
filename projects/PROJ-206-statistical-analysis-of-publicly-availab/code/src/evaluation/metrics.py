import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Ensure we can import from the project root if run as a script
if __name__ == "__main__":
    # Add the parent directory of 'src' to sys.path to allow relative imports
    # This handles both running from project root and running from within 'code'
    parent_dir = Path(__file__).resolve().parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Also handle the case where the project is in 'code' directory
    code_dir = Path(__file__).resolve().parent.parent.parent.parent
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from src.utils.logging import get_logger
from src.utils.config import get_data_processed_path, get_project_root

logger = get_logger(__name__)

def calculate_rmse(predictions: pd.Series, actuals: pd.Series) -> float:
    """
    Calculate Root Mean Squared Error.
    
    Args:
        predictions: Series of predicted values.
        actuals: Series of actual observed values.
        
    Returns:
        RMSE value.
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have the same length")
    if len(predictions) == 0:
        return 0.0
        
    mse = np.mean((predictions - actuals) ** 2)
    return np.sqrt(mse)

def calculate_mae(predictions: pd.Series, actuals: pd.Series) -> float:
    """
    Calculate Mean Absolute Error.
    
    Args:
        predictions: Series of predicted values.
        actuals: Series of actual observed values.
        
    Returns:
        MAE value.
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have the same length")
    if len(predictions) == 0:
        return 0.0
        
    return np.mean(np.abs(predictions - actuals))

def evaluate_frequentist_forecasts(
    forecasts_df: pd.DataFrame, 
    outcomes_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Evaluate frequentist forecasts against actual election outcomes.
    
    Args:
        forecasts_df: DataFrame containing forecasts with columns including
                     'simple_avg_forecast', 'weighted_avg_forecast', 'week_start',
                     'candidate', 'actual_outcome' (if available).
        outcomes_df: DataFrame containing actual election outcomes.
                    
    Returns:
        DataFrame with RMSE and MAE for both methods.
    """
    logger.info("Evaluating frequentist forecasts against actual outcomes")
    
    # Merge forecasts with outcomes if not already merged
    # Assuming both have 'week_start' and 'candidate' or similar keys
    # For now, we'll assume forecasts_df has the actual outcome column
    
    results = []
    
    for method in ['simple_avg_forecast', 'weighted_avg_forecast']:
        if method not in forecasts_df.columns:
            logger.warning(f"Column {method} not found in forecasts_df")
            continue
            
        # Filter out rows where actual outcome is missing
        valid_data = forecasts_df.dropna(subset=['actual_outcome'])
        
        if len(valid_data) == 0:
            logger.warning("No valid data for evaluation (missing actual outcomes)")
            continue
            
        predictions = valid_data[method]
        actuals = valid_data['actual_outcome']
        
        rmse = calculate_rmse(predictions, actuals)
        mae = calculate_mae(predictions, actuals)
        
        results.append({
            'method': method,
            'rmse': rmse,
            'mae': mae,
            'n_observations': len(valid_data)
        })
        
    return pd.DataFrame(results)

def calculate_coverage(
    lower_bounds: pd.Series,
    upper_bounds: pd.Series,
    actuals: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate the coverage rate of prediction intervals.
    
    Args:
        lower_bounds: Series of lower bound predictions.
        upper_bounds: Series of upper bound predictions.
        actuals: Series of actual observed values.
        confidence_level: Target confidence level (e.g., 0.95 for 95% CI).
                        
    Returns:
        Coverage rate (proportion of actuals within the intervals).
    """
    if len(lower_bounds) != len(upper_bounds) or len(lower_bounds) != len(actuals):
        raise ValueError("All input series must have the same length")
    if len(lower_bounds) == 0:
        return 0.0
        
    within_interval = (actuals >= lower_bounds) & (actuals <= upper_bounds)
    coverage_rate = within_interval.mean()
    
    logger.info(f"Coverage rate: {coverage_rate:.4f} (target: {confidence_level})")
    return coverage_rate

def test_coverage_reliability(
    coverage_rate: float,
    n_observations: int,
    target_coverage: float = 0.95,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a binomial test to assess if the observed coverage rate
    is statistically consistent with the target coverage rate.
    
    This implements SC-002: Test coverage reliability against the null hypothesis
    that the true coverage rate equals the target (e.g., 0.95 for 95% CI).
    
    Args:
        coverage_rate: Observed coverage rate (proportion).
        n_observations: Number of observations used to calculate coverage.
        target_coverage: Target coverage rate under null hypothesis (p0).
        alpha: Significance level for the test.
        
    Returns:
        Dictionary containing test results:
        - 'statistic': z-statistic
        - 'p_value': two-tailed p-value
        - 'reject_null': boolean indicating if null hypothesis is rejected
        - 'conclusion': string interpretation of results
    """
    if n_observations == 0:
        return {
            'statistic': None,
            'p_value': None,
            'reject_null': False,
            'conclusion': "No observations to test. Cannot perform binomial test."
        }
        
    # Number of successes (observations within interval)
    n_successes = int(round(coverage_rate * n_observations))
    
    # Perform binomial test using normal approximation for large n
    # H0: p = target_coverage
    # H1: p != target_coverage (two-tailed)
    
    p0 = target_coverage
    q0 = 1 - p0
    
    # Expected number of successes under null
    expected_successes = n_observations * p0
    
    # Standard error under null
    se = np.sqrt(n_observations * p0 * q0)
    
    if se == 0:
        # Edge case: p0 is 0 or 1, or n is 0 (already handled)
        if n_successes == expected_successes:
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'reject_null': False,
                'conclusion': f"Perfect agreement with null hypothesis (p={p0})."
            }
        else:
            return {
                'statistic': float('inf') if n_successes > expected_successes else float('-inf'),
                'p_value': 0.0,
                'reject_null': True,
                'conclusion': f"Complete disagreement with null hypothesis (p={p0})."
            }
    
    # Z-statistic
    z_stat = (n_successes - expected_successes) / se
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Decision
    reject_null = p_value < alpha
    
    # Interpretation
    if reject_null:
        if coverage_rate < target_coverage:
            conclusion = (f"Reject H0 (p={p_value:.4f} < {alpha}). "
                        f"Observed coverage ({coverage_rate:.4f}) is significantly "
                        f"LOWER than target ({target_coverage}). "
                        f"Intervals are too narrow (under-coverage).")
        else:
            conclusion = (f"Reject H0 (p={p_value:.4f} < {alpha}). "
                        f"Observed coverage ({coverage_rate:.4f}) is significantly "
                        f"HIGHER than target ({target_coverage}). "
                        f"Intervals are too wide (over-coverage).")
    else:
        conclusion = (f"Fail to reject H0 (p={p_value:.4f} >= {alpha}). "
                    f"Observed coverage ({coverage_rate:.4f}) is consistent with "
                    f"target ({target_coverage}). Intervals are well-calibrated.")
                    
    return {
        'statistic': z_stat,
        'p_value': p_value,
        'reject_null': reject_null,
        'conclusion': conclusion,
        'n_observations': n_observations,
        'n_successes': n_successes,
        'expected_successes': expected_successes,
        'observed_coverage': coverage_rate,
        'target_coverage': target_coverage,
        'alpha': alpha
    }

def main():
    """
    Main function to demonstrate coverage reliability testing.
    This would typically be called after Bayesian model evaluation.
    """
    logger.info("Starting coverage reliability test demonstration")
    
    # Example usage with synthetic data (in real scenario, use actual model outputs)
    # This is just for demonstration of the function's interface
    try:
        # Simulate some coverage results
        n_obs = 100
        observed_coverage = 0.92  # Example observed coverage
        
        results = test_coverage_reliability(
            coverage_rate=observed_coverage,
            n_observations=n_obs,
            target_coverage=0.95,
            alpha=0.05
        )
        
        logger.info(f"Coverage Test Results: {results['conclusion']}")
        logger.info(f"  Z-statistic: {results['statistic']:.4f}")
        logger.info(f"  P-value: {results['p_value']:.4f}")
        logger.info(f"  Reject H0: {results['reject_null']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in coverage reliability test: {e}")
        raise

if __name__ == "__main__":
    main()
