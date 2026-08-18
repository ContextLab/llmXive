"""
Aggregator module for calculating empirical error rates and confidence intervals.

Reads p-values from raw CSV, groups by experimental conditions, calculates
Type I and Type II error rates, computes Wilson score intervals, and saves
the summary to a new CSV file.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import from existing API surface
from code.simulation.logging_config import get_logger, log_operation
from code.simulation.output_writer import load_p_values_raw, load_p_values_raw_safe

logger = get_logger(__name__)


def wilson_score_interval(
    successes: int,
    n: int,
    confidence: float = 0.95
) -> tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.
    
    Args:
        successes: Number of successful outcomes (e.g., rejections)
        n: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return 0.0, 1.0
        
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    
    denominator = 1 + z**2 / n
    centre_adjusted_probability = p_hat + z**2 / (2 * n)
    adjusted_standard_deviation = np.sqrt(
        (p_hat * (1 - p_hat) + z**2 / (4 * n)) / n
    )
    
    lower = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator
    
    # Clamp to [0, 1]
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))
    
    return float(lower), float(upper)


def calculate_error_rates(
    p_values_df: pd.DataFrame,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Calculate Type I and Type II error rates grouped by experimental conditions.
    
    Type I error: Rejecting null when it is true (p < alpha when hypothesis_state == 'H0')
    Type II error: Failing to reject null when alternative is true (p > alpha when hypothesis_state == 'H1')
    
    Args:
        p_values_df: DataFrame with columns including 'p_value', 'hypothesis_state',
                    'sample_size', 'effect_size', 'test_type'
        alpha: Significance threshold (default 0.05)
        
    Returns:
        DataFrame with aggregated error rates and confidence intervals
    """
    if p_values_df.empty:
        logger.log("aggregator_empty_input", message="No data to aggregate")
        return pd.DataFrame()
    
    # Ensure we have the required columns
    required_cols = ['p_value', 'hypothesis_state', 'sample_size', 'effect_size', 'test_type']
    missing_cols = [c for c in required_cols if c not in p_values_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Group by experimental conditions
    groupby_cols = ['test_type', 'sample_size', 'effect_size']
    
    results = []
    
    for (test_type, sample_size, effect_size), group in p_values_df.groupby(groupby_cols):
        # Count total iterations
        n = len(group)
        if n == 0:
            continue
        
        # Calculate Type I error (when H0 is true)
        h0_mask = group['hypothesis_state'] == 'H0'
        h0_group = group[h0_mask]
        n_h0 = len(h0_group)
        type1_rejections = 0
        if n_h0 > 0:
            type1_rejections = (h0_group['p_value'] < alpha).sum()
        
        # Calculate Type II error (when H1 is true)
        h1_mask = group['hypothesis_state'] == 'H1'
        h1_group = group[h1_mask]
        n_h1 = len(h1_group)
        type2_failures = 0
        if n_h1 > 0:
            type2_failures = (h1_group['p_value'] > alpha).sum()
        
        # Calculate rates
        type1_rate = type1_rejections / n_h0 if n_h0 > 0 else 0.0
        type2_rate = type2_failures / n_h1 if n_h1 > 0 else 0.0
        
        # Calculate Wilson score intervals
        ci_lower_1, ci_upper_1 = wilson_score_interval(type1_rejections, n_h0)
        ci_lower_2, ci_upper_2 = wilson_score_interval(type2_failures, n_h1)
        
        results.append({
            'test_type': test_type,
            'sample_size': sample_size,
            'effect_size': effect_size,
            'n_iterations': n,
            'n_h0': n_h0,
            'n_h1': n_h1,
            'type1_error_rate': type1_rate,
            'type2_error_rate': type2_rate,
            'type1_ci_lower': ci_lower_1,
            'type1_ci_upper': ci_upper_1,
            'type2_ci_lower': ci_lower_2,
            'type2_ci_upper': ci_upper_2,
            'type1_rejections': type1_rejections,
            'type2_failures': type2_failures
        })
    
    result_df = pd.DataFrame(results)
    return result_df


def save_aggregated_results(
    df: pd.DataFrame,
    output_path: str,
    alpha: float = 0.05
) -> None:
    """
    Save aggregated error rates to CSV file.
    
    Args:
        df: DataFrame with aggregated results
        output_path: Path to save the CSV file
        alpha: Significance threshold used for calculation
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Select and order columns for the output
    output_cols = [
        'test_type', 'sample_size', 'effect_size',
        'type1_error_rate', 'type2_error_rate',
        'ci_lower', 'ci_upper',
        'n_iterations', 'n_h0', 'n_h1'
    ]
    
    # Filter to only existing columns
    existing_cols = [c for c in output_cols if c in df.columns]
    
    # For the main summary, we need to decide which CI to use
    # The task asks for 'ci_lower' and 'ci_upper' - we'll use Type I CI as primary
    # but include both in the detailed output
    summary_cols = ['test_type', 'sample_size', 'effect_size', 
                   'type1_error_rate', 'type2_error_rate']
    
    # Add CI for Type I error as the primary CI
    if 'type1_ci_lower' in df.columns and 'type1_ci_upper' in df.columns:
        df['ci_lower'] = df['type1_ci_lower']
        df['ci_upper'] = df['type1_ci_upper']
        summary_cols.extend(['ci_lower', 'ci_upper'])
    
    # Add counts for verification
    summary_cols.extend(['n_iterations', 'n_h0', 'n_h1'])
    
    summary_df = df[summary_cols]
    
    # Write to CSV
    summary_df.to_csv(output_path, index=False)
    
    logger.log(
        "aggregator_results_saved",
        path=output_path,
        rows=len(summary_df),
        alpha=alpha
    )
    
    print(f"Aggregated error rates saved to: {output_path}")
    print(f"Total conditions: {len(summary_df)}")
    print(f"Columns: {list(summary_df.columns)}")


def load_error_rates(input_path: str) -> pd.DataFrame:
    """
    Load aggregated error rates from CSV file.
    
    Args:
        input_path: Path to the CSV file
        
    Returns:
        DataFrame with error rates
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Error rates file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.log("aggregator_loaded", path=input_path, rows=len(df))
    return df


@log_operation
def main(alpha: float = 0.05) -> None:
    """
    Main entry point for the aggregator.
    
    Reads p-values from raw CSV, calculates error rates, and saves the summary.
    
    Args:
        alpha: Significance threshold (default 0.05)
    """
    # Define paths
    raw_pvalues_path = "data/simulation/p_values_raw.csv"
    output_path = "data/simulation/error_rates_summary.csv"
    
    # Check if raw data exists
    if not os.path.exists(raw_pvalues_path):
        logger.log(
            "aggregator_missing_input",
            path=raw_pvalues_path,
            message="Raw p-values file not found. Run simulation first."
        )
        raise FileNotFoundError(
            f"Raw p-values file not found: {raw_pvalues_path}. "
            "Please run the simulation first to generate data/simulation/p_values_raw.csv"
        )
    
    # Load raw p-values
    print(f"Loading raw p-values from: {raw_pvalues_path}")
    p_values_df = load_p_values_raw_safe(raw_pvalues_path)
    
    if p_values_df is None or p_values_df.empty:
        logger.log(
            "aggregator_empty_data",
            path=raw_pvalues_path,
            message="Raw p-values file is empty or could not be loaded."
        )
        raise ValueError(
            f"Raw p-values file is empty or invalid: {raw_pvalues_path}"
        )
    
    print(f"Loaded {len(p_values_df)} p-values")
    print(f"Columns: {list(p_values_df.columns)}")
    
    # Calculate error rates
    print(f"Calculating error rates with alpha={alpha}...")
    error_rates_df = calculate_error_rates(p_values_df, alpha=alpha)
    
    if error_rates_df.empty:
        logger.log(
            "aggregator_no_results",
            message="No error rates could be calculated."
        )
        raise ValueError("No error rates could be calculated from the data.")
    
    print(f"Calculated error rates for {len(error_rates_df)} conditions")
    
    # Save results
    print(f"Saving aggregated results to: {output_path}")
    save_aggregated_results(error_rates_df, output_path, alpha=alpha)
    
    # Verify output
    if os.path.exists(output_path):
        output_df = pd.read_csv(output_path)
        print(f"\nVerification:")
        print(f"Output file exists: True")
        print(f"Output rows: {len(output_df)}")
        print(f"Output columns: {list(output_df.columns)}")
        
        # Check required columns
        required_cols = ['test_type', 'sample_size', 'effect_size', 
                       'type1_error_rate', 'type2_error_rate', 'ci_lower', 'ci_upper']
        missing = [c for c in required_cols if c not in output_df.columns]
        if missing:
            print(f"WARNING: Missing required columns: {missing}")
        else:
            print("All required columns present: True")
        
        # Print sample of results
        print("\nSample results (first 5 rows):")
        print(output_df.head())
    else:
        raise RuntimeError(f"Failed to write output file: {output_path}")
    
    logger.log(
        "aggregator_complete",
        input_path=raw_pvalues_path,
        output_path=output_path,
        alpha=alpha
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate p-values into error rates")
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default: 0.05)"
    )
    
    args = parser.parse_args()
    main(alpha=args.alpha)
