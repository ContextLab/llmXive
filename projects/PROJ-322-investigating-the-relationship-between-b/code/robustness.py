"""
Robustness Validation Module (US3)

Implements permutation testing to calculate empirical p-values for the relationship
between brain network reconfiguration (graph metrics) and cognitive recovery.

Requirements:
- FR-004: Permutation testing with sufficient iterations
- SC-002: CPU-only, no deep learning

This script reads preprocessed data from the statistical model pipeline,
performs permutation testing, and outputs empirical p-values.
"""

import os
import json
import logging
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats

# Import from project modules
from config import get_config, is_synthetic, get_runtime_limit_hours, get_memory_limit_gb
from memory_monitor import get_current_ram_gb, is_limit_exceeded, check_and_warn
from logging_config import get_logger, initialize_logging, log_memory_warning
from statistical_model import load_preprocessed_data

# Constants
DEFAULT_PERMUTATION_ITERATIONS = 5000
MIN_PERMUTATION_ITERATIONS = 1000
OUTPUT_DIR = Path("data/results")
OUTPUT_FILE = OUTPUT_DIR / "permutation_results.json"

# Setup logging
logger = get_logger(__name__)

def load_statistical_results() -> Optional[pd.DataFrame]:
    """
    Load preprocessed data and statistical model results.
    
    Returns:
        DataFrame with graph metrics and cognitive scores, or None if not available.
    """
    try:
        data_path = Path("data/processed") / "processed_metrics.csv"
        if not data_path.exists():
            logger.warning(f"Processed metrics file not found at {data_path}. "
                         "This may indicate that US2 (statistical_model.py) has not been run yet.")
            return None
        
        df = pd.read_csv(data_path)
        
        # Verify required columns exist
        required_cols = ['subject_id', 'time_point', 'global_efficiency', 
                       'local_efficiency', 'modularity', 'cognitive_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.error(f"Missing required columns in processed metrics: {missing_cols}")
            return None
        
        logger.info(f"Loaded {len(df)} rows from {data_path}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading statistical results: {e}")
        return None

def calculate_observed_correlation(df: pd.DataFrame, 
                                  metric_col: str, 
                                  outcome_col: str = 'cognitive_score') -> float:
    """
    Calculate the observed correlation between a graph metric and cognitive score.
    
    Args:
        df: DataFrame with metrics and outcomes
        metric_col: Name of the graph metric column
        outcome_col: Name of the outcome variable (default: cognitive_score)
    
    Returns:
        Pearson correlation coefficient
    """
    # Drop rows with missing values
    clean_data = df[[metric_col, outcome_col]].dropna()
    
    if len(clean_data) < 2:
        raise ValueError("Insufficient data points for correlation calculation")
    
    corr, _ = stats.pearsonr(clean_data[metric_col], clean_data[outcome_col])
    return corr

def perform_permutation_test(df: pd.DataFrame,
                            metric_col: str,
                            outcome_col: str = 'cognitive_score',
                            n_iterations: int = DEFAULT_PERMUTATION_ITERATIONS,
                            random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform permutation testing to calculate empirical p-value.
    
    The null hypothesis is that there is no relationship between the graph metric
    and cognitive recovery. We permute the outcome variable and recalculate the
    correlation to build a null distribution.
    
    Args:
        df: DataFrame with metrics and outcomes
        metric_col: Name of the graph metric column
        outcome_col: Name of the outcome variable
        n_iterations: Number of permutation iterations
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary containing:
            - observed_correlation: The actual correlation from unpermuted data
            - empirical_p_value: Proportion of permuted correlations >= observed
            - null_distribution: Array of correlation coefficients from permutations
            - n_iterations: Number of iterations performed
            - is_significant: Whether p < 0.05
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Calculate observed correlation
    observed_corr = calculate_observed_correlation(df, metric_col, outcome_col)
    logger.info(f"Observed correlation ({metric_col} vs {outcome_col}): {observed_corr:.4f}")
    
    # Extract clean data
    clean_data = df[[metric_col, outcome_col]].dropna()
    X = clean_data[metric_col].values
    y = clean_data[outcome_col].values
    
    n_samples = len(X)
    if n_samples < 2:
        raise ValueError("Insufficient data points for permutation testing")
    
    # Permutation test
    null_distribution = np.zeros(n_iterations)
    
    logger.info(f"Starting permutation test with {n_iterations} iterations...")
    start_time = time.time()
    
    for i in range(n_iterations):
        # Check memory and runtime limits
        if i % 500 == 0 and i > 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            remaining = (n_iterations - i) / rate if rate > 0 else 0
            logger.info(f"Permutation {i}/{n_iterations} complete. "
                      f"Rate: {rate:.1f} iters/sec. Est. remaining: {remaining:.1f}s")
            
            # Check memory
            check_and_warn()
            if is_limit_exceeded():
                logger.error("Memory limit exceeded during permutation test. Stopping.")
                break
        
        # Permute the outcome variable
        y_permuted = np.random.permutation(y)
        
        # Calculate correlation with permuted data
        if np.std(y_permuted) > 1e-10:  # Avoid division by zero
            corr, _ = stats.pearsonr(X, y_permuted)
        else:
            corr = 0.0
        
        null_distribution[i] = corr
    
    # Calculate empirical p-value (two-tailed)
    # Count how many permuted correlations are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(null_distribution) >= np.abs(observed_corr))
    empirical_p_value = (extreme_count + 1) / (n_iterations + 1)  # Add 1 for observed value
    
    elapsed = time.time() - start_time
    logger.info(f"Permutation test complete in {elapsed:.2f}s")
    logger.info(f"Empirical p-value: {empirical_p_value:.4f}")
    
    return {
        'observed_correlation': float(observed_corr),
        'empirical_p_value': float(empirical_p_value),
        'null_distribution': null_distribution.tolist(),
        'n_iterations': int(n_iterations),
        'is_significant': bool(empirical_p_value < 0.05),
        'runtime_seconds': float(elapsed),
        'metric_name': metric_col
    }

def run_robustness_analysis(n_iterations: int = DEFAULT_PERMUTATION_ITERATIONS,
                           metrics: Optional[List[str]] = None,
                           random_state: Optional[int] = None) -> Dict[str, Any]:
    """
    Run full robustness analysis with permutation testing on multiple metrics.
    
    Args:
        n_iterations: Number of permutation iterations per metric
        metrics: List of graph metrics to test (default: all available)
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary containing results for all tested metrics
    """
    # Load data
    df = load_statistical_results()
    if df is None:
        logger.error("Could not load data for robustness analysis. "
                    "Please ensure US2 (statistical_model.py) has been run first.")
        return {'error': 'Data not available'}
    
    # Determine which metrics to test
    available_metrics = ['global_efficiency', 'local_efficiency', 'modularity']
    if metrics is None:
        metrics_to_test = [m for m in available_metrics if m in df.columns]
    else:
        metrics_to_test = [m for m in metrics if m in df.columns]
    
    if not metrics_to_test:
        logger.error("No valid metrics found for testing")
        return {'error': 'No metrics available'}
    
    logger.info(f"Testing metrics: {metrics_to_test}")
    
    # Run permutation tests for each metric
    results = {
        'metrics_tested': metrics_to_test,
        'n_iterations': n_iterations,
        'permutation_results': {},
        'summary': {}
    }
    
    for metric in metrics_to_test:
        try:
            metric_result = perform_permutation_test(
                df=df,
                metric_col=metric,
                outcome_col='cognitive_score',
                n_iterations=n_iterations,
                random_state=random_state if random_state is not None else None
            )
            results['permutation_results'][metric] = metric_result
            
            # Summary statistics
            results['summary'][metric] = {
                'observed_correlation': metric_result['observed_correlation'],
                'empirical_p_value': metric_result['empirical_p_value'],
                'is_significant': metric_result['is_significant']
            }
            
        except Exception as e:
            logger.error(f"Error testing metric {metric}: {e}")
            results['permutation_results'][metric] = {'error': str(e)}
    
    # Add metadata
    results['config'] = {
        'is_synthetic': is_synthetic(),
        'memory_limit_gb': get_memory_limit_gb(),
        'runtime_limit_hours': get_runtime_limit_hours()
    }
    
    return results

def save_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save permutation test results to JSON file.
    
    Args:
        results: Dictionary of results from run_robustness_analysis
        output_path: Path to output file (default: data/results/permutation_results.json)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    # (Already handled in perform_permutation_test, but double-check)
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(i) for i in obj]
        else:
            return obj
    
    serializable_results = convert_to_serializable(results)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for robustness analysis.
    
    Runs permutation testing with default or specified parameters,
    saves results, and logs summary.
    """
    logger.info("=" * 60)
    logger.info("Starting Robustness Analysis (Permutation Testing)")
    logger.info("=" * 60)
    
    # Initialize logging and memory monitoring
    initialize_logging()
    
    # Check initial memory state
    initial_ram = get_current_ram_gb()
    logger.info(f"Initial RAM usage: {initial_ram:.2f} GB")
    
    # Configuration
    n_iterations = DEFAULT_PERMUTATION_ITERATIONS
    random_state = 42  # For reproducibility
    
    logger.info(f"Running {n_iterations} permutation iterations")
    logger.info(f"Random state: {random_state}")
    
    # Run analysis
    start_time = time.time()
    results = run_robustness_analysis(
        n_iterations=n_iterations,
        random_state=random_state
    )
    
    # Check for errors
    if 'error' in results:
        logger.error(f"Robustness analysis failed: {results['error']}")
        return 1
    
    # Save results
    output_path = save_results(results)
    
    # Log summary
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Robustness Analysis Summary")
    logger.info("=" * 60)
    logger.info(f"Total runtime: {elapsed:.2f} seconds")
    logger.info(f"Final RAM usage: {get_current_ram_gb():.2f} GB")
    
    if 'summary' in results:
        for metric, summary in results['summary'].items():
            sig_marker = "***" if summary['is_significant'] else ""
            logger.info(f"{metric}: r={summary['observed_correlation']:.4f}, "
                      f"p={summary['empirical_p_value']:.4f} {sig_marker}")
    
    logger.info(f"Results saved to: {output_path}")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    exit(main())