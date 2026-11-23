"""
Evaluation metrics for frequentist and Bayesian forecasts.

Implements RMSE, MAE, and coverage calculations against actual election outcomes.
"""
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from src.utils.config import get_data_root, resolve_path
from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_rmse(actual: pd.Series, predicted: pd.Series) -> float:
    """
    Calculate Root Mean Squared Error between actual and predicted values.
    
    Args:
        actual: Series of actual election outcomes (vote share)
        predicted: Series of predicted vote shares
        
    Returns:
        RMSE value
    """
    if len(actual) != len(predicted):
        raise ValueError(f"Length mismatch: actual={len(actual)}, predicted={len(predicted)}")
    
    if len(actual) == 0:
        raise ValueError("Cannot calculate RMSE on empty series")
        
    squared_errors = (actual - predicted) ** 2
    mse = squared_errors.mean()
    rmse = math.sqrt(mse)
    
    logger.info(f"Calculated RMSE: {rmse:.6f} (n={len(actual)})")
    return rmse


def calculate_mae(actual: pd.Series, predicted: pd.Series) -> float:
    """
    Calculate Mean Absolute Error between actual and predicted values.
    
    Args:
        actual: Series of actual election outcomes (vote share)
        predicted: Series of predicted vote shares
        
    Returns:
        MAE value
    """
    if len(actual) != len(predicted):
        raise ValueError(f"Length mismatch: actual={len(actual)}, predicted={len(predicted)}")
    
    if len(actual) == 0:
        raise ValueError("Cannot calculate MAE on empty series")
        
    absolute_errors = (actual - predicted).abs()
    mae = absolute_errors.mean()
    
    logger.info(f"Calculated MAE: {mae:.6f} (n={len(actual)})")
    return mae


def evaluate_frequentist_forecasts(
    forecasts_path: Optional[str] = None,
    outcomes_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate frequentist forecasts against actual election outcomes.
    
    Computes RMSE and MAE for both simple average and weighted average forecasts.
    
    Args:
        forecasts_path: Path to frequentist_forecasts.csv (defaults to data/processed/)
        outcomes_path: Path to election outcomes (defaults to data/processed/outcomes.csv)
        
    Returns:
        Dictionary containing:
            - simple_avg_rmse: RMSE for simple average forecast
            - simple_avg_mae: MAE for simple average forecast
            - weighted_avg_rmse: RMSE for weighted average forecast
            - weighted_avg_mae: MAE for weighted average forecast
            - metrics_df: DataFrame with per-election metrics
    """
    data_root = get_data_root()
    
    # Resolve paths
    if forecasts_path is None:
        forecasts_path = str(data_root / "processed" / "frequentist_forecasts.csv")
    if outcomes_path is None:
        outcomes_path = str(data_root / "processed" / "outcomes.csv")
        
    forecasts_path = resolve_path(forecasts_path)
    outcomes_path = resolve_path(outcomes_path)
    
    logger.info(f"Loading forecasts from: {forecasts_path}")
    logger.info(f"Loading outcomes from: {outcomes_path}")
    
    # Load data
    if not Path(forecasts_path).exists():
        raise FileNotFoundError(f"Forecasts file not found: {forecasts_path}")
    if not Path(outcomes_path).exists():
        raise FileNotFoundError(f"Outcomes file not found: {outcomes_path}")
        
    forecasts_df = pd.read_csv(forecasts_path)
    outcomes_df = pd.read_csv(outcomes_path)
    
    # Validate required columns
    required_forecast_cols = ['simple_avg_forecast', 'weighted_avg_forecast']
    for col in required_forecast_cols:
        if col not in forecasts_df.columns:
            raise ValueError(f"Missing required column in forecasts: {col}")
            
    if 'actual_vote_share' not in outcomes_df.columns:
        raise ValueError("Missing 'actual_vote_share' column in outcomes file")
    if 'election_id' not in outcomes_df.columns:
        raise ValueError("Missing 'election_id' column in outcomes file")
        
    # Merge forecasts with outcomes
    # Assuming both have election_id for joining
    if 'election_id' not in forecasts_df.columns:
        # Try to infer from file or use index
        logger.warning("election_id not found in forecasts, attempting to merge by index")
        outcomes_df = outcomes_df.reset_index(drop=True)
        forecasts_df = forecasts_df.reset_index(drop=True)
        
    merged = pd.merge(
        forecasts_df, 
        outcomes_df[['election_id', 'actual_vote_share']], 
        on='election_id', 
        how='inner'
    )
    
    if len(merged) == 0:
        raise ValueError("No matching elections found between forecasts and outcomes")
        
    logger.info(f"Merged {len(merged)} election records for evaluation")
    
    # Calculate metrics
    actual = merged['actual_vote_share']
    simple_avg_pred = merged['simple_avg_forecast']
    weighted_avg_pred = merged['weighted_avg_forecast']
    
    simple_avg_rmse = calculate_rmse(actual, simple_avg_pred)
    simple_avg_mae = calculate_mae(actual, simple_avg_pred)
    weighted_avg_rmse = calculate_rmse(actual, weighted_avg_pred)
    weighted_avg_mae = calculate_mae(actual, weighted_avg_pred)
    
    # Create per-election metrics DataFrame
    metrics_df = pd.DataFrame({
        'election_id': merged['election_id'],
        'actual_vote_share': actual,
        'simple_avg_forecast': simple_avg_pred,
        'weighted_avg_forecast': weighted_avg_pred,
        'simple_avg_error': (actual - simple_avg_pred).abs(),
        'weighted_avg_error': (actual - weighted_avg_pred).abs(),
        'simple_avg_squared_error': (actual - simple_avg_pred) ** 2,
        'weighted_avg_squared_error': (actual - weighted_avg_pred) ** 2
    })
    
    results = {
        'simple_avg_rmse': simple_avg_rmse,
        'simple_avg_mae': simple_avg_mae,
        'weighted_avg_rmse': weighted_avg_rmse,
        'weighted_avg_mae': weighted_avg_mae,
        'metrics_df': metrics_df,
        'n_evaluations': len(merged)
    }
    
    logger.info("Evaluation complete:")
    logger.info(f"  Simple Avg - RMSE: {simple_avg_rmse:.4f}, MAE: {simple_avg_mae:.4f}")
    logger.info(f"  Weighted Avg - RMSE: {weighted_avg_rmse:.4f}, MAE: {weighted_avg_mae:.4f}")
    
    return results


def calculate_coverage(
    forecasts_path: Optional[str] = None,
    outcomes_path: Optional[str] = None,
    lower_col: str = 'lower_95',
    upper_col: str = 'upper_95',
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Calculate credible interval coverage rate against actual outcomes.
    
    This function checks if the actual election outcome falls within the
    predicted credible interval for each election.
    
    Args:
        forecasts_path: Path to forecasts file with interval columns
        outcomes_path: Path to outcomes file
        lower_col: Name of the lower bound column (default: 'lower_95')
        upper_col: Name of the upper bound column (default: 'upper_95')
        confidence_level: Expected confidence level (default: 0.95 for 95%)
        
    Returns:
        Dictionary containing:
            - coverage_rate: Observed coverage rate
            - expected_coverage: Expected coverage rate
            - n_covered: Number of elections within interval
            - n_total: Total number of elections
            - coverage_df: Per-election coverage status
    """
    data_root = get_data_root()
    
    if forecasts_path is None:
        forecasts_path = str(data_root / "processed" / "bayesian_forecasts.csv")
    if outcomes_path is None:
        outcomes_path = str(data_root / "processed" / "outcomes.csv")
        
    forecasts_path = resolve_path(forecasts_path)
    outcomes_path = resolve_path(outcomes_path)
    
    logger.info(f"Loading forecasts from: {forecasts_path}")
    logger.info(f"Loading outcomes from: {outcomes_path}")
    
    if not Path(forecasts_path).exists():
        raise FileNotFoundError(f"Forecasts file not found: {forecasts_path}")
    if not Path(outcomes_path).exists():
        raise FileNotFoundError(f"Outcomes file not found: {outcomes_path}")
        
    forecasts_df = pd.read_csv(forecasts_path)
    outcomes_df = pd.read_csv(outcomes_path)
    
    # Validate required columns
    for col in [lower_col, upper_col, 'actual_vote_share']:
        if col not in forecasts_df.columns and col not in outcomes_df.columns:
            # Check if it's in either file
            if 'election_id' in forecasts_df.columns and 'election_id' in outcomes_df.columns:
                merged = pd.merge(forecasts_df, outcomes_df, on='election_id', how='inner')
                if col not in merged.columns:
                    raise ValueError(f"Missing required column: {col}")
                forecasts_df = merged
            else:
                raise ValueError(f"Missing required column: {col}")
    else:
        # If actual_vote_share is in outcomes, merge
        if 'actual_vote_share' in outcomes_df.columns and 'actual_vote_share' not in forecasts_df.columns:
            forecasts_df = pd.merge(forecasts_df, outcomes_df[['election_id', 'actual_vote_share']], on='election_id', how='inner')
        
    # Ensure we have the columns
    if lower_col not in forecasts_df.columns:
        raise ValueError(f"Lower bound column '{lower_col}' not found in forecasts")
    if upper_col not in forecasts_df.columns:
        raise ValueError(f"Upper bound column '{upper_col}' not found in forecasts")
    if 'actual_vote_share' not in forecasts_df.columns:
        raise ValueError("Actual vote share not found after merge")
        
    actual = forecasts_df['actual_vote_share']
    lower = forecasts_df[lower_col]
    upper = forecasts_df[upper_col]
    
    # Calculate coverage
    is_covered = (actual >= lower) & (actual <= upper)
    
    n_covered = is_covered.sum()
    n_total = len(is_covered)
    coverage_rate = n_covered / n_total if n_total > 0 else 0.0
    
    coverage_df = pd.DataFrame({
        'election_id': forecasts_df['election_id'] if 'election_id' in forecasts_df.columns else range(n_total),
        'actual_vote_share': actual,
        'lower_bound': lower,
        'upper_bound': upper,
        'is_covered': is_covered
    })
    
    results = {
        'coverage_rate': coverage_rate,
        'expected_coverage': confidence_level,
        'n_covered': int(n_covered),
        'n_total': int(n_total),
        'coverage_df': coverage_df,
        'coverage_percentage': coverage_rate * 100
    }
    
    logger.info(f"Credible Interval Coverage: {coverage_rate:.4f} ({coverage_rate*100:.2f}%)")
    logger.info(f"Expected: {confidence_level*100:.2f}% ({n_covered}/{n_total})")
    
    return results


def main():
    """
    Main entry point for metrics evaluation.
    
    Runs evaluation of frequentist forecasts and outputs results to CSV.
    """
    logger.info("Starting metrics evaluation...")
    
    try:
        # Evaluate frequentist forecasts
        results = evaluate_frequentist_forecasts()
        
        # Save metrics summary
        data_root = get_data_root()
        metrics_output_path = data_root / "processed" / "evaluation_metrics.csv"
        
        summary_data = {
            'method': ['simple_avg', 'weighted_avg'],
            'rmse': [results['simple_avg_rmse'], results['weighted_avg_rmse']],
            'mae': [results['simple_avg_mae'], results['weighted_avg_mae']]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(metrics_output_path, index=False)
        logger.info(f"Saved metrics summary to: {metrics_output_path}")
        
        # Save per-election metrics
        per_election_path = data_root / "processed" / "per_election_metrics.csv"
        results['metrics_df'].to_csv(per_election_path, index=False)
        logger.info(f"Saved per-election metrics to: {per_election_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("EVALUATION RESULTS SUMMARY")
        print("="*60)
        print(f"Simple Average Forecast:")
        print(f"  RMSE: {results['simple_avg_rmse']:.4f}")
        print(f"  MAE:  {results['simple_avg_mae']:.4f}")
        print(f"  N evaluations: {results['n_evaluations']}")
        print(f"\nWeighted Average Forecast:")
        print(f"  RMSE: {results['weighted_avg_rmse']:.4f}")
        print(f"  MAE:  {results['weighted_avg_mae']:.4f}")
        print(f"  N evaluations: {results['n_evaluations']}")
        print("="*60)
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Please ensure frequentist_forecasts.csv and outcomes.csv exist in data/processed/")
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    main()