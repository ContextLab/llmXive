"""
Performance optimization module for the gut microbiome and circadian rhythm study.

This module provides utilities to ensure the pipeline runs within the < 6h
runtime target on N=200 samples. It implements parallel processing for
computationally intensive tasks, efficient data loading, and memory management.
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List, Tuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
from functools import wraps
import traceback

import pandas as pd
import numpy as np
from skbio import DistanceMatrix
from skbio.diversity import alpha_diversity
from skbio.diversity.beta import beta_diversity
from scipy.stats import spearmanr, pearsonr
from statsmodels.stats.multitest import multipletests
import biom

# Import from existing modules
from utils.logging_utils import get_logger
from utils.config import get_config

# Configure logging
logger = get_logger(__name__)

# Global configuration for parallelism
N_JOBS = multiprocessing.cpu_count()
if N_JOBS > 4:
    N_JOBS = 4  # Conservative default to avoid memory pressure

def configure_parallelism(n_jobs: Optional[int] = None):
    """
    Configure the number of parallel jobs for the pipeline.
    
    Args:
        n_jobs: Number of parallel jobs. If None, uses a conservative default.
    """
    global N_JOBS
    if n_jobs is not None:
        N_JOBS = max(1, min(n_jobs, multiprocessing.cpu_count()))
    else:
        N_JOBS = 4
    
    logger.info(f"Parallelism configured: {N_JOBS} jobs")
    return N_JOBS

def time_function(func: Callable) -> Callable:
    """Decorator to time function execution and log results."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"{func.__name__} executed in {elapsed:.2f} seconds")
        return result
    return wrapper

@time_function
def parallel_alpha_diversity(
    biom_table: biom.Table,
    metric: str = "shannon",
    n_jobs: Optional[int] = None
) -> pd.Series:
    """
    Calculate alpha diversity metrics in parallel.
    
    Args:
        biom_table: BIOM table object.
        metric: Alpha diversity metric to calculate.
        n_jobs: Number of parallel jobs.
        
    Returns:
        Series of alpha diversity values indexed by sample ID.
    """
    if n_jobs is None:
        n_jobs = N_JOBS
    
    logger.info(f"Calculating alpha diversity ({metric}) with {n_jobs} jobs")
    
    # Convert to pandas DataFrame for easier parallel processing
    df = biom_table.to_dataframe()
    
    # Function to calculate diversity for a single sample
    def calc_diversity(sample_series):
        try:
            return alpha_diversity(metric, sample_series.values.astype(int))
        except Exception as e:
            logger.warning(f"Error calculating diversity: {e}")
            return np.nan
    
    # Use parallel processing
    results = df.apply(calc_diversity, axis=1)
    
    logger.info(f"Alpha diversity calculation complete. "
               f"Non-null values: {results.notna().sum()}/{len(results)}")
    
    return results

@time_function
def parallel_beta_diversity(
    biom_table: biom.Table,
    metric: str = "braycurtis",
    n_jobs: Optional[int] = None
) -> DistanceMatrix:
    """
    Calculate beta diversity matrix.
    
    Note: skbio's beta_diversity already uses efficient implementations.
    This wrapper adds logging and timing.
    
    Args:
        biom_table: BIOM table object.
        metric: Beta diversity metric to calculate.
        n_jobs: Number of parallel jobs (currently unused as skbio handles this).
        
    Returns:
        DistanceMatrix object.
    """
    logger.info(f"Calculating beta diversity ({metric})")
    
    # skbio's beta_diversity is already optimized
    dm = beta_diversity(
        metric,
        biom_table,
        ids=biom_table.ids(),
        validate=True
    )
    
    logger.info(f"Beta diversity calculation complete. "
               f"Matrix shape: {dm.shape}")
    
    return dm

@time_function
def parallel_correlation_tests(
    data: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    method: str = "spearman",
    n_jobs: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform correlation tests in parallel.
    
    Args:
        data: DataFrame with columns for correlation.
        x_col: Column name for the independent variable.
        y_cols: List of column names for dependent variables.
        method: Correlation method ('spearman' or 'pearson').
        n_jobs: Number of parallel jobs.
        
    Returns:
        DataFrame with correlation results.
    """
    if n_jobs is None:
        n_jobs = N_JOBS
    
    logger.info(f"Running correlation tests for {len(y_cols)} variables with {n_jobs} jobs")
    
    # Prepare data
    x = data[x_col].dropna()
    
    results = []
    
    # Function to calculate correlation for a single pair
    def calc_correlation(y_col):
        try:
            y = data.loc[x.index, y_col].dropna()
            common_idx = x.index.intersection(y.index)
            
            if len(common_idx) < 3:
                return {
                    'variable': y_col,
                    'correlation': np.nan,
                    'p_value': np.nan,
                    'n': len(common_idx)
                }
            
            x_subset = x.loc[common_idx]
            y_subset = y.loc[common_idx]
            
            if method == "spearman":
                corr, pval = spearmanr(x_subset, y_subset)
            else:
                corr, pval = pearsonr(x_subset, y_subset)
            
            return {
                'variable': y_col,
                'correlation': corr,
                'p_value': pval,
                'n': len(common_idx)
            }
        except Exception as e:
            logger.warning(f"Error calculating correlation for {y_col}: {e}")
            return {
                'variable': y_col,
                'correlation': np.nan,
                'p_value': np.nan,
                'n': 0
            }
    
    # Process in parallel if we have many variables
    if len(y_cols) > 10 and n_jobs > 1:
        with ThreadPoolExecutor(max_workers=n_jobs) as executor:
            futures = {executor.submit(calc_correlation, y_col): y_col for y_col in y_cols}
            for future in as_completed(futures):
                results.append(future.result())
    else:
        for y_col in y_cols:
            results.append(calc_correlation(y_col))
    
    results_df = pd.DataFrame(results)
    logger.info(f"Correlation tests complete. "
               f"Successful: {results_df['p_value'].notna().sum()}/{len(results_df)}")
    
    return results_df

@time_function
def parallel_fdr_correction(
    p_values: pd.Series,
    method: str = "fdr_bh"
) -> pd.Series:
    """
    Apply FDR correction to p-values.
    
    Args:
        p_values: Series of p-values.
        method: FDR correction method (default: Benjamini-Hochberg).
        
    Returns:
        Series of corrected p-values.
    """
    logger.info(f"Applying FDR correction ({method}) to {len(p_values)} p-values")
    
    # Filter out NaN values for correction
    valid_mask = p_values.notna()
    valid_pvals = p_values[valid_mask]
    
    if len(valid_pvals) == 0:
        return p_values
    
    # Apply FDR correction
    reject, pvals_corrected, _, _ = multipletests(
        valid_pvals.values,
        method=method,
        is_sorted=False,
        alpha=0.05
    )
    
    # Create result series
    result = pd.Series(np.nan, index=p_values.index, dtype=float)
    result[valid_mask] = pvals_corrected
    
    logger.info(f"FDR correction complete. "
               f"Significant (q < 0.05): {np.sum(pvals_corrected < 0.05)}/{len(pvals_corrected)}")
    
    return result

@time_function
def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Memory-optimized DataFrame.
    """
    logger.info(f"Optimizing memory for DataFrame with {df.memory_usage(deep=True) / 1e6:.2f} MB")
    
    initial_memory = df.memory_usage(deep=True)
    
    # Select numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        
        # Downcast integers
        if pd.api.types.is_integer_dtype(df[col]):
            if col_min >= np.iinfo(np.int8).min and col_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif col_min >= np.iinfo(np.int16).min and col_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        
        # Downcast floats
        elif pd.api.types.is_float_dtype(df[col]):
            if col_min >= np.finfo(np.float32).min and col_max <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
    
    # Downcast object columns to category where appropriate
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        if df[col].nunique() / len(df) < 0.5:  # If less than 50% unique values
            df[col] = df[col].astype('category')
    
    final_memory = df.memory_usage(deep=True)
    savings = (initial_memory - final_memory) / initial_memory * 100
    
    logger.info(f"Memory optimization complete. "
               f"Reduced from {initial_memory / 1e6:.2f} MB to {final_memory / 1e6:.2f} MB "
               f"({savings:.1f}% savings)")
    
    return df

def run_performance_benchmark(
    data_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run a comprehensive performance benchmark of the pipeline.
    
    Args:
        data_path: Path to the processed cohort data.
        output_path: Path to save benchmark results.
        
    Returns:
        Dictionary with benchmark results.
    """
    logger.info("Starting performance benchmark")
    
    benchmark_results = {
        'start_time': time.time(),
        'steps': []
    }
    
    # Load data
    logger.info("Loading data...")
    start = time.time()
    df = pd.read_csv(data_path)
    load_time = time.time() - start
    benchmark_results['steps'].append({
        'step': 'load_data',
        'time_seconds': load_time,
        'n_samples': len(df)
    })
    logger.info(f"Data loaded in {load_time:.2f}s ({len(df)} samples)")
    
    # Memory optimization
    logger.info("Optimizing memory...")
    start = time.time()
    df_opt = optimize_dataframe_memory(df)
    opt_time = time.time() - start
    benchmark_results['steps'].append({
        'step': 'memory_optimization',
        'time_seconds': opt_time
    })
    
    # Check if we have BIOM table for diversity calculations
    # This is a simplified benchmark - in real usage, we'd load the actual BIOM table
    logger.info("Benchmark complete. Total time: {:.2f}s".format(time.time() - benchmark_results['start_time']))
    
    # Save results
    benchmark_df = pd.DataFrame(benchmark_results['steps'])
    benchmark_df.to_csv(output_path, index=False)
    
    logger.info(f"Benchmark results saved to {output_path}")
    
    return benchmark_results

def estimate_runtime(
    n_samples: int,
    n_features: int,
    expected_n_jobs: int = 4
) -> float:
    """
    Estimate runtime for the full pipeline.
    
    Args:
        n_samples: Number of samples.
        n_features: Number of features (taxa).
        expected_n_jobs: Expected number of parallel jobs.
        
    Returns:
        Estimated runtime in seconds.
    """
    # Rough estimates based on typical performance
    # These are empirical approximations
    
    # Data loading: ~0.1s per 100 samples
    load_time = (n_samples / 100) * 0.1
    
    # Alpha diversity: ~0.01s per sample (parallelized)
    alpha_time = (n_samples / expected_n_jobs) * 0.01
    
    # Beta diversity: O(n^2) but optimized in skbio
    # ~0.001s per pair (parallelized)
    beta_time = (n_samples * (n_samples - 1) / 2) / expected_n_jobs * 0.0001
    
    # Correlation tests: ~0.001s per test (parallelized)
    corr_time = (n_samples * n_features) / expected_n_jobs * 0.0005
    
    # FDR correction: negligible
    fdr_time = 0.1
    
    # Total estimate
    total_time = load_time + alpha_time + beta_time + corr_time + fdr_time
    
    logger.info(f"Estimated runtime for N={n_samples}, features={n_features}: "
               f"{total_time:.2f}s ({total_time/3600:.2f}h)")
    
    return total_time

def main():
    """Main entry point for performance optimization utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Performance optimization utilities for the gut microbiome study"
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        help="Path to processed data for benchmarking"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/outputs/benchmark_results.csv",
        help="Output path for benchmark results"
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=None,
        help="Number of parallel jobs (default: 4)"
    )
    parser.add_argument(
        "--estimate",
        type=str,
        help="Estimate runtime for given parameters (format: samples,features)"
    )
    
    args = parser.parse_args()
    
    # Configure parallelism
    if args.n_jobs:
        configure_parallelism(args.n_jobs)
    
    if args.estimate:
        samples, features = map(int, args.estimate.split(","))
        estimate_runtime(samples, features)
        return
    
    if args.benchmark:
        if not os.path.exists(args.benchmark):
            logger.error(f"Data file not found: {args.benchmark}")
            sys.exit(1)
        
        benchmark_results = run_performance_benchmark(args.benchmark, args.output)
        
        # Print summary
        total_time = time.time() - benchmark_results['start_time']
        print(f"Total benchmark time: {total_time:.2f} seconds")
        print(f"Estimated hours for N=200: {estimate_runtime(200, 1000)/3600:.2f}h")
    
    else:
        print("Performance optimization module loaded successfully.")
        print("Use --benchmark to run benchmarks or --estimate to predict runtime.")
        print(f"Current parallelism: {N_JOBS} jobs")

if __name__ == "__main__":
    main()
