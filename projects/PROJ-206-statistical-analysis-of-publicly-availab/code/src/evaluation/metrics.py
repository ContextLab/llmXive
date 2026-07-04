import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats

from src.utils.config import get_data_root, resolve_path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_rmse(actual: pd.Series, predicted: pd.Series) -> float:
    """Calculate Root Mean Squared Error."""
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted series must have the same length")
    if len(actual) == 0:
        return 0.0
    return math.sqrt(np.mean((actual - predicted) ** 2))

def calculate_mae(actual: pd.Series, predicted: pd.Series) -> float:
    """Calculate Mean Absolute Error."""
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted series must have the same length")
    if len(actual) == 0:
        return 0.0
    return np.mean(np.abs(actual - predicted))

def evaluate_frequentist_forecasts(
    forecasts_path: str,
    outcomes_path: str,
    output_path: str
) -> Dict[str, float]:
    """
    Evaluate frequentist forecasts against actual outcomes.
    
    Args:
        forecasts_path: Path to frequentist_forecasts.csv
        outcomes_path: Path to election outcomes data
        output_path: Path to save evaluation results
    
    Returns:
        Dictionary with RMSE and MAE for simple and weighted averages
    """
    logger.info(f"Evaluating forecasts from {forecasts_path}")
    
    forecasts_df = pd.read_csv(forecasts_path)
    outcomes_df = pd.read_csv(outcomes_path)
    
    # Merge forecasts with outcomes
    # Assuming both have 'election_date' or similar key
    merged = pd.merge(
        forecasts_df, 
        outcomes_df, 
        on='election_date', 
        how='inner',
        suffixes=('_forecast', '_outcome')
    )
    
    if merged.empty:
        logger.error("No overlapping records between forecasts and outcomes")
        return {}
    
    results = {}
    
    # Calculate metrics for simple average
    simple_rmse = calculate_rmse(
        merged['actual_vote_share'], 
        merged['simple_avg_forecast']
    )
    simple_mae = calculate_mae(
        merged['actual_vote_share'], 
        merged['simple_avg_forecast']
    )
    
    results['simple_avg_rmse'] = simple_rmse
    results['simple_avg_mae'] = simple_mae
    
    # Calculate metrics for weighted average
    weighted_rmse = calculate_rmse(
        merged['actual_vote_share'], 
        merged['weighted_avg_forecast']
    )
    weighted_mae = calculate_mae(
        merged['actual_vote_share'], 
        merged['weighted_avg_forecast']
    )
    
    results['weighted_avg_rmse'] = weighted_rmse
    results['weighted_avg_mae'] = weighted_mae
    
    # Save results
    results_df = pd.DataFrame([results])
    results_df.to_csv(output_path, index=False)
    logger.info(f"Evaluation results saved to {output_path}")
    
    return results

def calculate_coverage(
    forecasts_path: str,
    outcomes_path: str,
    lower_col: str = "lower_95",
    upper_col: str = "upper_95",
    actual_col: str = "actual_vote_share",
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate credible interval coverage rate against actual outcomes.
    
    This function verifies FR-009 and SC-002 by checking how often the 
    actual election outcome falls within the predicted 95% credible interval.
    
    Args:
        forecasts_path: Path to Bayesian forecast CSV containing CI bounds
        outcomes_path: Path to election outcomes CSV with actual results
        lower_col: Name of the column containing lower CI bound (default: "lower_95")
        upper_col: Name of the column containing upper CI bound (default: "upper_95")
        actual_col: Name of the column containing actual vote share
        output_path: Optional path to save coverage results CSV
    
    Returns:
        Dictionary containing:
            - coverage_rate: Proportion of outcomes within CI (0.0 to 1.0)
            - total_predictions: Number of predictions evaluated
            - within_ci_count: Number of outcomes within CI
            - outside_ci_count: Number of outcomes outside CI
            - ci_width_mean: Mean width of credible intervals
            - ci_width_std: Standard deviation of CI widths
    """
    logger.info(f"Calculating coverage for {forecasts_path}")
    
    # Load data
    forecasts_df = pd.read_csv(forecasts_path)
    outcomes_df = pd.read_csv(outcomes_path)
    
    # Merge forecasts with outcomes
    merged = pd.merge(
        forecasts_df,
        outcomes_df,
        on='election_date',
        how='inner',
        suffixes=('_forecast', '_outcome')
    )
    
    if merged.empty:
        logger.error("No overlapping records between forecasts and outcomes")
        return {
            'coverage_rate': 0.0,
            'total_predictions': 0,
            'within_ci_count': 0,
            'outside_ci_count': 0,
            'ci_width_mean': 0.0,
            'ci_width_std': 0.0
        }
    
    # Ensure columns exist
    required_cols = [lower_col, upper_col, actual_col]
    missing_cols = [col for col in required_cols if col not in merged.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in merged data: {missing_cols}")
    
    # Calculate coverage
    within_ci = (
        (merged[actual_col] >= merged[lower_col]) & 
        (merged[actual_col] <= merged[upper_col])
    )
    
    total_predictions = len(merged)
    within_ci_count = within_ci.sum()
    outside_ci_count = total_predictions - within_ci_count
    coverage_rate = within_ci_count / total_predictions if total_predictions > 0 else 0.0
    
    # Calculate CI widths
    ci_widths = merged[upper_col] - merged[lower_col]
    ci_width_mean = ci_widths.mean()
    ci_width_std = ci_widths.std()
    
    results = {
        'coverage_rate': coverage_rate,
        'total_predictions': total_predictions,
        'within_ci_count': int(within_ci_count),
        'outside_ci_count': int(outside_ci_count),
        'ci_width_mean': ci_width_mean,
        'ci_width_std': ci_width_std
    }
    
    logger.info(f"Coverage Rate: {coverage_rate:.4f} ({within_ci_count}/{total_predictions})")
    logger.info(f"Mean CI Width: {ci_width_mean:.4f}, Std: {ci_width_std:.4f}")
    
    # Save detailed results if path provided
    if output_path:
        results_df = pd.DataFrame([results])
        results_df.to_csv(output_path, index=False)
        logger.info(f"Coverage results saved to {output_path}")
    
    return results

def main():
    """Main entry point for coverage calculation."""
    data_root = get_data_root()
    
    # Paths
    forecasts_path = resolve_path(data_root, "processed/bayesian_forecasts.csv")
    outcomes_path = resolve_path(data_root, "raw/election_outcomes.csv")
    output_path = resolve_path(data_root, "processed/coverage_results.csv")
    
    # Check if files exist
    if not Path(forecasts_path).exists():
        logger.error(f"Bayesian forecasts not found at {forecasts_path}")
        logger.info("Please run src/models/bayesian.py first to generate forecasts.")
        return
    
    if not Path(outcomes_path).exists():
        logger.error(f"Election outcomes not found at {outcomes_path}")
        logger.info("Please ensure election outcomes data is available.")
        return
    
    # Calculate coverage
    results = calculate_coverage(
        forecasts_path=forecasts_path,
        outcomes_path=outcomes_path,
        output_path=output_path
    )
    
    print(f"\nCoverage Analysis Results:")
    print(f"  Total Predictions: {results['total_predictions']}")
    print(f"  Within CI: {results['within_ci_count']}")
    print(f"  Outside CI: {results['outside_ci_count']}")
    print(f"  Coverage Rate: {results['coverage_rate']:.4f}")
    print(f"  Mean CI Width: {results['ci_width_mean']:.4f}")
    print(f"  CI Width Std: {results['ci_width_std']:.4f}")
    
    # Check against expected 95% coverage (FR-009, SC-002)
    expected_coverage = 0.95
    if results['coverage_rate'] >= expected_coverage:
        logger.info(f"Coverage meets or exceeds expected {expected_coverage} threshold.")
    else:
        logger.warning(f"Coverage ({results['coverage_rate']:.4f}) is below expected {expected_coverage} threshold.")

if __name__ == "__main__":
    main()
