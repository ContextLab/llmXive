"""
Partial Correlation Analysis Module for llmXive.

This module implements partial correlation analysis to ensure metric independence
from input parameters, specifically addressing SC-006.

It calculates the partial correlation between 'memory_depth' and 'diversity'
while controlling for other factors (coherence_score, step_latency, param_id).
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.NaN_and_explosion_guard import validate_metrics_no_nan
from src.data_models import MetricRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_partial_correlation(
    df: pd.DataFrame,
    target_var: str,
    control_var: str,
    control_vars: List[str],
    threshold: float = 0.05
) -> Tuple[float, bool, Dict[str, Any]]:
    """
    Calculate partial correlation between target_var and control_var,
    controlling for control_vars.

    Args:
        df: DataFrame containing the data
        target_var: The variable to correlate (e.g., 'diversity')
        control_var: The variable to control for partially (e.g., 'memory_depth')
        control_vars: List of variables to control for (e.g., ['coherence_score', 'step_latency'])
        threshold: The threshold for significance (default 0.05)

    Returns:
        Tuple of (partial_correlation_coefficient, is_independent, stats_dict)
    """
    # Validate inputs
    required_cols = [target_var, control_var] + control_vars
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in DataFrame: {missing_cols}")

    # Drop rows with NaN in relevant columns
    clean_df = df.dropna(subset=required_cols)
    if len(clean_df) < len(control_vars) + 2:
        raise ValueError(
            f"Insufficient data points for partial correlation calculation. "
            f"Need at least {len(control_vars) + 2} rows, got {len(clean_df)}."
        )

    # Extract variables
    y = clean_df[target_var].values
    x = clean_df[control_var].values
    Z = clean_df[control_vars].values

    # Calculate residuals for y and x against Z
    # Residuals = original - predicted_by_Z
    # Using OLS manually for residuals
    
    # Add intercept to Z
    Z_with_intercept = np.c_[np.ones(len(Z)), Z]
    
    # Calculate beta for y ~ Z
    # beta = (Z^T Z)^-1 Z^T y
    try:
        ZtZ_inv = np.linalg.inv(Z_with_intercept.T @ Z_with_intercept)
    except np.linalg.LinAlgError:
        # If singular, use pseudo-inverse
        ZtZ_inv = np.linalg.pinv(Z_with_intercept.T @ Z_with_intercept)
    
    beta_y = ZtZ_inv @ (Z_with_intercept.T @ y)
    beta_x = ZtZ_inv @ (Z_with_intercept.T @ x)
    
    # Calculate residuals
    y_resid = y - (Z_with_intercept @ beta_y)
    x_resid = x - (Z_with_intercept @ beta_x)
    
    # Partial correlation is correlation between residuals
    numerator = np.sum(x_resid * y_resid)
    denominator = np.sqrt(np.sum(x_resid**2) * np.sum(y_resid**2))
    
    if denominator == 0:
        logger.warning("Denominator is zero in partial correlation calculation. Returning 0.")
        partial_corr = 0.0
    else:
        partial_corr = numerator / denominator

    # Check independence
    is_independent = abs(partial_corr) < threshold

    # Prepare stats dict
    stats = {
        "partial_correlation": float(partial_corr),
        "threshold": threshold,
        "is_independent": is_independent,
        "n_observations": len(clean_df),
        "control_variables": control_vars,
        "target_variable": target_var,
        "control_variable": control_var
    }

    return partial_corr, is_independent, stats

def load_simulation_data(data_path: str) -> pd.DataFrame:
    """
    Load simulation data from a CSV file.
    
    Args:
        data_path: Path to the CSV file containing simulation metrics
        
    Returns:
        DataFrame with simulation metrics
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Validate no NaN in key metrics
    key_metrics = ['diversity', 'memory_depth', 'coherence_score', 'step_latency']
    available_metrics = [m for m in key_metrics if m in df.columns]
    if available_metrics:
        validate_metrics_no_nan(df, available_metrics)
    
    return df

def run_partial_correlation_analysis(
    input_path: str,
    output_path: str,
    target_var: str = 'diversity',
    control_var: str = 'memory_depth',
    control_vars: Optional[List[str]] = None,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Run the partial correlation analysis and save results.
    
    Args:
        input_path: Path to input CSV file with simulation data
        output_path: Path to save the JSON results
        target_var: Variable to test for independence
        control_var: Variable to partial out
        control_vars: Variables to control for
        threshold: Threshold for independence assertion
        
    Returns:
        Dictionary containing the analysis results
    """
    if control_vars is None:
        # Default control variables based on typical simulation metrics
        control_vars = ['coherence_score', 'step_latency']
    
    logger.info(f"Loading data from {input_path}")
    df = load_simulation_data(input_path)
    
    logger.info(f"Calculating partial correlation between '{control_var}' and '{target_var}' "
                f"controlling for {control_vars}")
    
    try:
        partial_corr, is_independent, stats = calculate_partial_correlation(
            df, target_var, control_var, control_vars, threshold
        )
        
        logger.info(f"Partial correlation coefficient: {partial_corr:.6f}")
        logger.info(f"Is independent (|r| < {threshold}): {is_independent}")
        
        if not is_independent:
            logger.warning(f"Partial correlation ({partial_corr:.6f}) exceeds threshold ({threshold}). "
                           f"Metrics may not be independent.")
        
        # Save results
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
        return stats
        
    except ValueError as e:
        logger.error(f"Analysis failed: {e}")
        raise

def main():
    """CLI entry point for partial correlation analysis."""
    parser = argparse.ArgumentParser(
        description="Calculate partial correlation between memory_depth and diversity"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input CSV file containing simulation metrics"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/processed/partial_corr_analysis.json",
        help="Path to save JSON results (default: data/processed/partial_corr_analysis.json)"
    )
    parser.add_argument(
        "--target", "-t",
        type=str,
        default="diversity",
        help="Target variable for correlation (default: diversity)"
    )
    parser.add_argument(
        "--control", "-c",
        type=str,
        default="memory_depth",
        help="Control variable to partial out (default: memory_depth)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Threshold for independence assertion (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_partial_correlation_analysis(
            input_path=args.input,
            output_path=args.output,
            target_var=args.target,
            control_var=args.control,
            threshold=args.threshold
        )
        
        # Print summary
        print("\n" + "="*50)
        print("PARTIAL CORRELATION ANALYSIS RESULTS")
        print("="*50)
        print(f"Target Variable: {args.target}")
        print(f"Control Variable: {args.control}")
        print(f"Controlled For: {result['control_variables']}")
        print(f"Partial Correlation: {result['partial_correlation']:.6f}")
        print(f"Threshold: {result['threshold']}")
        print(f"Is Independent: {result['is_independent']}")
        print(f"Observations: {result['n_observations']}")
        print("="*50)
        
        if not result['is_independent']:
            print("WARNING: Metrics may not be independent!")
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
