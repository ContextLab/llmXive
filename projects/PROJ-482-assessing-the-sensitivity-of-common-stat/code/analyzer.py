"""
Analyzer module for aggregating simulation results and computing statistics.

This module has been refactored to separate aggregation logic from visualization logic.
Aggregation functions are defined here; visualization is delegated to the visualizer module.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
from scipy import stats

logger = logging.getLogger(__name__)

def load_simulation_results(file_path: str) -> pd.DataFrame:
    """
    Load simulation results from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing simulation results.
        
    Returns:
        DataFrame with simulation results.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Simulation results file not found: {file_path}")
    
    logger.info(f"Loading simulation results from {file_path}")
    df = pd.read_csv(file_path)
    return df

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate simulation results by sample size, distribution, and test type.
    
    Computes:
    - Error rates (Type I and Type II)
    - 95% Bootstrap confidence intervals
    - Stability variance metrics
    
    Args:
        df: DataFrame with raw simulation results (one row per replicate).
        
    Returns:
        DataFrame with aggregated metrics grouped by (n, distribution, test).
    """
    logger.info("Aggregating simulation results...")
    
    # Ensure required columns exist
    required_cols = ['sample_size', 'distribution', 'test_type', 'rejected', 'effect_size']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Group by scenario
    grouped = df.groupby(['sample_size', 'distribution', 'test_type'])
    
    # Calculate error rates
    agg_dict = {
        'rejected': ['mean', 'count'],
        'effect_size': 'first'  # Get the effect size for the group
    }
    
    result = grouped.agg(agg_dict).reset_index()
    result.columns = ['sample_size', 'distribution', 'test_type', 'error_rate', 'n_replicates', 'effect_size']
    
    # Calculate bootstrap confidence intervals for error rates
    ci_results = []
    for idx, row in result.iterrows():
        # Extract the subset of replicates for this group
        subset = df[
            (df['sample_size'] == row['sample_size']) &
            (df['distribution'] == row['distribution']) &
            (df['test_type'] == row['test_type'])
        ]['rejected']
        
        ci_lower, ci_upper = compute_bootstrap_ci(subset.values, confidence=0.95)
        
        ci_results.append({
            'sample_size': row['sample_size'],
            'distribution': row['distribution'],
            'test_type': row['test_type'],
            'error_rate': row['error_rate'],
            'n_replicates': row['n_replicates'],
            'effect_size': row['effect_size'],
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })
    
    result_with_ci = pd.DataFrame(ci_results)
    logger.info(f"Aggregation complete. {len(result_with_ci)} scenarios processed.")
    return result_with_ci

def compute_bootstrap_ci(data: np.ndarray, confidence: float = 0.95, n_bootstraps: int = 1000) -> Tuple[float, float]:
    """
    Compute bootstrap confidence intervals for a given dataset.
    
    Args:
        data: Array of binary outcomes (0 or 1) indicating rejection.
        confidence: Confidence level (default 0.95).
        n_bootstraps: Number of bootstrap samples.
        
    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval.
    """
    if len(data) == 0:
        return (0.0, 0.0)
    
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    boot_means = []
    
    for _ in range(n_bootstraps):
        sample = rng.choice(data, size=len(data), replace=True)
        boot_means.append(np.mean(sample))
    
    boot_means = np.array(boot_means)
    alpha = 1 - confidence
    lower = np.percentile(boot_means, 100 * alpha / 2)
    upper = np.percentile(boot_means, 100 * (1 - alpha / 2))
    
    return (lower, upper)

def calculate_stability_variance(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the variance of Type I error rates across sample sizes.
    
    This measures stability as per SC-002: lower variance indicates more stable
    error rates across sample sizes.
    
    Args:
        df: Aggregated DataFrame with error rates.
        
    Returns:
        Dictionary with variance metrics per test type and distribution.
    """
    logger.info("Calculating stability variance...")
    
    # Filter for null hypothesis (effect_size = 0) to get Type I error rates
    null_df = df[df['effect_size'] == 0]
    
    if null_df.empty:
        logger.warning("No null hypothesis scenarios found for stability calculation.")
        return {}
    
    stability_metrics = {}
    
    for test_type in null_df['test_type'].unique():
        test_df = null_df[null_df['test_type'] == test_type]
        
        for distribution in test_df['distribution'].unique():
            dist_df = test_df[test_df['distribution'] == distribution]
            
            if len(dist_df) > 1:
                variance = dist_df['error_rate'].var()
                key = f"{test_type}_{distribution}"
                stability_metrics[key] = variance
            else:
                logger.warning(f"Insufficient data points for {test_type} on {distribution} distribution.")
    
    logger.info(f"Stability variance calculated for {len(stability_metrics)} scenarios.")
    return stability_metrics

def export_results_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Export aggregated results to a CSV file.
    
    Args:
        df: DataFrame with aggregated results.
        output_path: Path for the output CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Results exported to {output_path}")

def analyze_and_export(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Main entry point for analysis: load, aggregate, and export results.
    
    This function orchestrates the aggregation pipeline. Visualization
    is handled separately in the visualizer module.
    
    Args:
        input_path: Path to the raw simulation results CSV.
        output_path: Path for the aggregated results CSV.
        
    Returns:
        DataFrame with aggregated results.
    """
    logger.info(f"Starting analysis pipeline for {input_path}")
    
    # Load data
    raw_df = load_simulation_results(input_path)
    
    # Aggregate
    aggregated_df = aggregate_results(raw_df)
    
    # Calculate stability metrics
    stability = calculate_stability_variance(aggregated_df)
    if stability:
        logger.info(f"Stability metrics: {stability}")
    
    # Export
    export_results_to_csv(aggregated_df, output_path)
    
    logger.info("Analysis pipeline complete.")
    return aggregated_df
