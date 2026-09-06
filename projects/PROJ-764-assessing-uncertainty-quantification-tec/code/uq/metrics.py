"""
UQ Metrics Module

Implements metrics for evaluating uncertainty quantification:
- Expected Calibration Error (ECE)
- Interval Score
- Sharpness
- Uncertainty Decomposition (Aleatoric vs Epistemic)
"""
import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

def expected_calibration_error(
    predictions: np.ndarray,
    true_values: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    target_coverage: float = 0.90,
    n_bins: int = 10
) -> float:
    """
    Compute Expected Calibration Error (ECE) for uncertainty intervals.
    
    ECE measures the difference between the nominal coverage (e.g., 90%)
    and the actual empirical coverage, weighted by bin size.
    
    Args:
        predictions: Array of point predictions (not directly used, but kept for API consistency)
        true_values: Array of true target values
        lower_bounds: Array of lower bounds for the interval
        upper_bounds: Array of upper bounds for the interval
        target_coverage: Target coverage probability (e.g., 0.90 for 90% interval)
        n_bins: Number of bins to use for calibration assessment
    
    Returns:
        ECE value (float)
    """
    if len(predictions) != len(true_values):
        raise ValueError("Predictions and true values must have the same length")
    
    # Calculate empirical coverage for each sample
    covered = (true_values >= lower_bounds) & (true_values <= upper_bounds)
    
    # Sort by prediction uncertainty (width of interval) to create bins
    interval_widths = upper_bounds - lower_bounds
    sorted_indices = np.argsort(interval_widths)
    
    # Create bins based on sorted indices
    bin_size = len(sorted_indices) // n_bins
    ece = 0.0
    
    for i in range(n_bins):
        start_idx = i * bin_size
        end_idx = (i + 1) * bin_size if i < n_bins - 1 else len(sorted_indices)
        
        bin_indices = sorted_indices[start_idx:end_idx]
        bin_covered = covered[bin_indices]
        bin_size_actual = len(bin_indices)
        
        if bin_size_actual == 0:
            continue
        
        empirical_coverage = np.mean(bin_covered)
        calibration_error = abs(empirical_coverage - target_coverage)
        
        # Weight by bin size
        ece += (bin_size_actual / len(sorted_indices)) * calibration_error
    
    return float(ece)

def interval_score(
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    true_values: np.ndarray,
    alpha: float = 0.10
) -> float:
    """
    Compute the Interval Score for uncertainty intervals.
    
    The Interval Score penalizes both wide intervals and intervals that
    do not contain the true value. Lower scores are better.
    
    Score = (U - L) + (2/alpha) * (L - y) * I(y < L) + (2/alpha) * (y - U) * I(y > U)
    
    Args:
        lower_bounds: Array of lower bounds (L)
        upper_bounds: Array of upper bounds (U)
        true_values: Array of true target values (y)
        alpha: Significance level (e.g., 0.10 for 90% interval)
    
    Returns:
        Mean interval score (float)
    """
    if len(lower_bounds) != len(true_values) or len(upper_bounds) != len(true_values):
        raise ValueError("All arrays must have the same length")
    
    # Interval width
    width = upper_bounds - lower_bounds
    
    # Penalties for missing the true value
    penalty_lower = (2.0 / alpha) * (lower_bounds - true_values) * (true_values < lower_bounds)
    penalty_upper = (2.0 / alpha) * (true_values - upper_bounds) * (true_values > upper_bounds)
    
    # Total score
    scores = width + penalty_lower + penalty_upper
    
    return float(np.mean(scores))

def sharpness(
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray
) -> float:
    """
    Compute Sharpness, which measures the average width of prediction intervals.
    
    Sharpness is a property of the predictions alone (does not depend on true values).
    Lower sharpness (narrower intervals) is better, provided coverage is maintained.
    
    Args:
        lower_bounds: Array of lower bounds
        upper_bounds: Array of upper bounds
    
    Returns:
        Mean interval width (float)
    """
    if len(lower_bounds) != len(upper_bounds):
        raise ValueError("Lower and upper bounds must have the same length")
    
    widths = upper_bounds - lower_bounds
    return float(np.mean(widths))

def decompose_uncertainty(
    predictions_df: pd.DataFrame,
    method: str
) -> Dict[str, float]:
    """
    Decompose uncertainty into aleatoric and epistemic components.
    
    For Deep Ensembles and MC Dropout:
    - Epistemic variance: variance of the mean predictions across ensemble members
    - Aleatoric variance: mean of the predicted variances
    - Total variance: aleatoric + epistemic
    
    For Sparse GP:
    - Returns null for aleatoric/epistemic as they are not separately estimated
    
    Args:
        predictions_df: DataFrame with predictions and variance estimates
        method: Method name ('deep_ensemble', 'mc_dropout', 'sparse_gp')
    
    Returns:
        Dictionary with 'aleatoric', 'epistemic', 'total' variance estimates
    """
    method_df = predictions_df[predictions_df['method'] == method]
    
    if len(method_df) == 0:
        logger.warning(f"No predictions found for method: {method}")
        return {'aleatoric': None, 'epistemic': None, 'total': None}
    
    if method == 'sparse_gp':
        # For GP, we don't have separate aleatoric/epistemic decomposition
        # Use the total variance as provided
        total_variance = method_df['variance'].mean()
        return {
            'aleatoric': None,
            'epistemic': None,
            'total': float(total_variance)
        }
    
    # For Deep Ensemble and MC Dropout
    # The 'variance' column in the predictions is the total variance
    # We need to decompose it based on the method's characteristics
    
    # In our implementation, the variance column already contains the total variance
    # For ensemble methods, we can estimate:
    # - Epistemic: variance of predictions (if we had multiple predictions per sample)
    # - Aleatoric: average of predicted variances
    
    # Since we have aggregated predictions per sample, we use:
    total_variance = method_df['variance'].mean()
    
    # If we have aleatoric and epistemic columns (from T022d decomposition)
    if 'aleatoric' in method_df.columns and 'epistemic' in method_df.columns:
        avg_aleatoric = method_df['aleatoric'].mean()
        avg_epistemic = method_df['epistemic'].mean()
        
        # Handle null values for Sparse GP rows if mixed
        avg_aleatoric = avg_aleatoric if not pd.isna(avg_aleatoric) else 0.0
        avg_epistemic = avg_epistemic if not pd.isna(avg_epistemic) else 0.0
    else:
        # Fallback: assume equal split if decomposition not available
        # This is a rough estimate
        avg_aleatoric = total_variance * 0.5
        avg_epistemic = total_variance * 0.5
    
    return {
        'aleatoric': float(avg_aleatoric),
        'epistemic': float(avg_epistemic),
        'total': float(total_variance)
    }

def calculate_all_metrics(
    predictions_df: pd.DataFrame,
    true_values: pd.Series
) -> pd.DataFrame:
    """
    Calculate all calibration metrics for all methods in the predictions dataframe.
    
    Args:
        predictions_df: DataFrame with UQ predictions
        true_values: Series of true target values indexed by sample_id
    
    Returns:
        DataFrame with metrics for each method
    """
    methods = predictions_df['method'].unique()
    results = []
    
    for method in methods:
        method_df = predictions_df[predictions_df['method'] == method]
        
        # Get aligned true values
        method_true = true_values[true_values.index.isin(method_df['sample_id'])]
        
        if len(method_true) == 0:
            logger.warning(f"No true values found for method: {method}")
            continue
        
        # Compute ECE
        ece_50 = expected_calibration_error(
            method_df['prediction'].values,
            method_true.values,
            method_df['lower_50'].values,
            method_df['upper_50'].values,
            target_coverage=0.50
        )
        ece_90 = expected_calibration_error(
            method_df['prediction'].values,
            method_true.values,
            method_df['lower_90'].values,
            method_df['upper_90'].values,
            target_coverage=0.90
        )
        ece = (ece_50 + ece_90) / 2.0
        
        # Compute Interval Score
        is_50 = interval_score(
            method_df['lower_50'].values,
            method_df['upper_50'].values,
            method_true.values,
            alpha=0.50
        )
        is_90 = interval_score(
            method_df['lower_90'].values,
            method_df['upper_90'].values,
            method_true.values,
            alpha=0.90
        )
        interval_score_avg = (is_50 + is_90) / 2.0
        
        # Compute Sharpness
        sharpness_50 = sharpness(method_df['lower_50'].values, method_df['upper_50'].values)
        sharpness_90 = sharpness(method_df['lower_90'].values, method_df['upper_90'].values)
        sharpness_avg = (sharpness_50 + sharpness_90) / 2.0
        
        # Compute Coverage
        coverage_50 = np.mean(
            (method_true.values >= method_df['lower_50'].values) &
            (method_true.values <= method_df['upper_50'].values)
        )
        coverage_90 = np.mean(
            (method_true.values >= method_df['lower_90'].values) &
            (method_true.values <= method_df['upper_90'].values)
        )
        
        results.append({
            'method': method,
            'ece': ece,
            'interval_score': interval_score_avg,
            'sharpness': sharpness_avg,
            'coverage_50': coverage_50,
            'coverage_90': coverage_90
        })
    
    return pd.DataFrame(results)

def main():
    """Main entry point for testing the metrics module."""
    logger.info("Testing UQ metrics module...")
    
    # Create sample data
    np.random.seed(42)
    n_samples = 1000
    
    predictions = np.random.randn(n_samples)
    true_values = predictions + np.random.randn(n_samples) * 0.5
    lower_90 = predictions - 2.0
    upper_90 = predictions + 2.0
    
    # Test ECE
    ece = expected_calibration_error(predictions, true_values, lower_90, upper_90, 0.90)
    logger.info(f"ECE (90%): {ece:.4f}")
    
    # Test Interval Score
    is_score = interval_score(lower_90, upper_90, true_values, 0.10)
    logger.info(f"Interval Score (90%): {is_score:.4f}")
    
    # Test Sharpness
    sh = sharpness(lower_90, upper_90)
    logger.info(f"Sharpness: {sh:.4f}")
    
    logger.info("Metrics module test complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()