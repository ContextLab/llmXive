"""
Bootstrapping module for non-parametric confidence interval estimation.

Implements contingency logic: if sample size n < 20, switch to 
non-parametric bootstrapping with 1000 iterations to estimate 
confidence intervals for graph metrics vs cognitive recovery correlation.

Output: data/results/bootstrapped_ci.json
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

from config import get_config, is_synthetic
from logging_config import get_logger
from memory_monitor import get_current_ram_gb, is_limit_exceeded, check_and_warn

# Constants
BOOTSTRAP_ITERATIONS = 1000
CONFIDENCE_LEVEL = 0.95
MIN_SAMPLE_SIZE = 20
OUTPUT_PATH = Path("data/results/bootstrapped_ci.json")

logger = get_logger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load preprocessed graph metrics and cognitive scores.
    Expects data to be in data/processed/ or data/results/ from previous pipeline steps.
    """
    # Try common locations based on pipeline flow
    possible_paths = [
        Path("data/results/graph_metrics.csv"),
        Path("data/processed/graph_metrics.csv"),
        Path("data/processed/metrics.csv")
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading data from {path}")
            df = pd.read_csv(path)
            # Ensure required columns exist
            required_cols = ['subject_id', 'time_point', 'global_efficiency', 
                             'local_efficiency', 'modularity', 'cognitive_score']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if not missing_cols:
                return df
            else:
                logger.warning(f"Missing columns in {path}: {missing_cols}")
    
    raise FileNotFoundError(
        "Could not find preprocessed data with required columns. "
        "Ensure preprocessing pipeline has run successfully."
    )

def calculate_correlation(df: pd.DataFrame, metric_col: str, target_col: str = 'cognitive_score') -> float:
    """
    Calculate Pearson correlation between a graph metric and cognitive score.
    """
    # Drop NaN values
    valid_data = df[[metric_col, target_col]].dropna()
    if len(valid_data) < 2:
        return np.nan
    
    correlation, _ = np.corrcoef(valid_data[metric_col], valid_data[target_col])
    return correlation[0, 1]

def bootstrap_correlation(
    df: pd.DataFrame, 
    metric_col: str, 
    target_col: str = 'cognitive_score',
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform non-parametric bootstrapping to estimate confidence intervals
    for the correlation between a graph metric and cognitive score.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with graph metrics and cognitive scores
    metric_col : str
        Name of the graph metric column (e.g., 'global_efficiency')
    target_col : str
        Name of the cognitive score column
    n_iterations : int
        Number of bootstrap iterations (default: 1000)
    random_state : int, optional
        Random seed for reproducibility
    
    Returns
    -------
    dict
        Dictionary containing correlation estimates, confidence intervals,
        and metadata
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Check memory before starting
    current_ram = get_current_ram_gb()
    logger.info(f"Starting bootstrapping with current RAM: {current_ram:.2f} GB")
    
    if is_limit_exceeded():
        logger.error("Memory limit exceeded before bootstrapping. Aborting.")
        raise MemoryError("Memory limit exceeded")
    
    # Get valid data pairs
    valid_data = df[[metric_col, target_col]].dropna()
    n_samples = len(valid_data)
    
    if n_samples < 2:
        logger.warning(f"Not enough samples ({n_samples}) for bootstrapping")
        return {
            'metric': metric_col,
            'n_samples': n_samples,
            'error': 'Insufficient samples',
            'correlation': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'bootstrap_mean': np.nan,
            'bootstrap_std': np.nan,
            'iterations': 0
        }
    
    correlations = []
    start_time = time.time()
    
    logger.info(f"Running {n_iterations} bootstrap iterations for {metric_col}...")
    
    for i in range(n_iterations):
        # Check memory periodically
        if i % 100 == 0:
            current_ram = get_current_ram_gb()
            if is_limit_exceeded():
                logger.error(f"Memory limit exceeded at iteration {i}")
                raise MemoryError("Memory limit exceeded during bootstrapping")
            
            # Progress log
            elapsed = time.time() - start_time
            logger.debug(f"Bootstrap iteration {i}/{n_iterations} ({elapsed:.1f}s elapsed)")
        
        # Resample with replacement
        resampled_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_data = valid_data.iloc[resampled_indices]
        
        # Calculate correlation for this sample
        corr = calculate_correlation(resampled_data, metric_col, target_col)
        if not np.isnan(corr):
            correlations.append(corr)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    logger.info(f"Bootstrapping completed in {elapsed_time:.2f} seconds")
    
    # Calculate statistics
    correlations = np.array(correlations)
    mean_corr = np.mean(correlations)
    std_corr = np.std(correlations, ddof=1)
    
    # Calculate confidence intervals (percentile method)
    alpha = 1 - CONFIDENCE_LEVEL
    ci_lower = np.percentile(correlations, (alpha / 2) * 100)
    ci_upper = np.percentile(correlations, (1 - alpha / 2) * 100)
    
    # Original sample correlation
    original_corr = calculate_correlation(valid_data, metric_col, target_col)
    
    return {
        'metric': metric_col,
        'n_samples': n_samples,
        'original_correlation': float(original_corr),
        'bootstrap_mean': float(mean_corr),
        'bootstrap_std': float(std_corr),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'confidence_level': CONFIDENCE_LEVEL,
        'iterations': len(correlations),
        'elapsed_seconds': float(elapsed_time),
        'method': 'non-parametric percentile bootstrap'
    }

def run_full_bootstrapping(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run bootstrapping for all graph metrics and compile results.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with graph metrics and cognitive scores
    
    Returns
    -------
    dict
        Complete bootstrapping results for all metrics
    """
    metrics = ['global_efficiency', 'local_efficiency', 'modularity']
    results = {}
    
    for metric in metrics:
        if metric in df.columns:
            logger.info(f"Bootstrapping correlation for {metric}")
            results[metric] = bootstrap_correlation(df, metric)
        else:
            logger.warning(f"Metric {metric} not found in data, skipping")
            results[metric] = {
                'metric': metric,
                'error': 'Column not found',
                'n_samples': 0
            }
    
    # Add metadata
    results['metadata'] = {
        'total_subjects': len(df),
        'is_synthetic': is_synthetic(),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'bootstrapping_iterations': BOOTSTRAP_ITERATIONS,
        'confidence_level': CONFIDENCE_LEVEL,
        'min_sample_threshold': MIN_SAMPLE_SIZE
    }
    
    return results

def save_results(results: Dict[str, Any]) -> Path:
    """
    Save bootstrapping results to JSON file.
    
    Parameters
    ----------
    results : dict
        Bootstrapping results dictionary
    
    Returns
    -------
    Path
        Path to the saved JSON file
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Bootstrapping results saved to {OUTPUT_PATH}")
    return OUTPUT_PATH

def main():
    """
    Main entry point for bootstrapping analysis.
    
    This function:
    1. Loads preprocessed data
    2. Checks sample size (n < 20 triggers bootstrapping)
    3. Runs non-parametric bootstrapping if needed
    4. Saves results to data/results/bootstrapped_ci.json
    """
    logger.info("Starting bootstrapping analysis (Task T016)")
    
    try:
        # Load data
        df = load_preprocessed_data()
        logger.info(f"Loaded {len(df)} subjects with graph metrics and cognitive scores")
        
        # Check sample size
        n_subjects = len(df)
        logger.info(f"Sample size: {n_subjects}")
        
        if n_subjects >= MIN_SAMPLE_SIZE:
            logger.info(f"Sample size ({n_subjects}) >= {MIN_SAMPLE_SIZE}. "
                       "Bootstrapping still performed for robustness (FR-009).")
        else:
            logger.warning(f"Sample size ({n_subjects}) < {MIN_SAMPLE_SIZE}. "
                         "Non-parametric bootstrapping REQUIRED per FR-009.")
        
        # Run bootstrapping
        results = run_full_bootstrapping(df)
        
        # Save results
        output_path = save_results(results)
        
        # Log summary
        logger.info("Bootstrapping summary:")
        for metric in ['global_efficiency', 'local_efficiency', 'modularity']:
            if metric in results and 'original_correlation' in results[metric]:
                r = results[metric]
                logger.info(f"  {metric}: r={r['original_correlation']:.3f}, "
                           f"95% CI [{r['ci_lower']:.3f}, {r['ci_upper']:.3f}]")
        
        logger.info(f"Task T016 completed successfully. Output: {output_path}")
        return True
        
    except MemoryError as e:
        logger.error(f"Memory error during bootstrapping: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"Data loading error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during bootstrapping: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
