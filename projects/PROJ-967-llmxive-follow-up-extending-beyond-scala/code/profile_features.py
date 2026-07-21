"""
Profile and optimize the feature engineering loop for CPU efficiency.

This script analyzes the performance of the feature engineering pipeline
by profiling execution time and memory usage, then applies optimizations
such as vectorization, parallel processing, and memory-efficient data structures.
"""

import argparse
import cProfile
import pstats
import io
import time
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

import numpy as np
import pandas as pd
from scipy import stats
from joblib import Parallel, delayed

# Import from existing modules
from features import (
    load_aligned_data,
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss,
    compute_all_features,
    save_features_to_json
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/profiling.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROFILING_OUTPUT_DIR = "results"
MEMORY_THRESHOLD_MB = 5000  # 5GB threshold

def setup_directories():
    """Ensure output directories exist."""
    Path(PROFILING_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

def profile_function(func, *args, **kwargs):
    """
    Profile a function and return execution statistics.
    
    Args:
        func: Function to profile
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Dict with profiling results (time, memory estimates, call counts)
    """
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    profiler.disable()
    
    # Get profiling stats
    stream = io.StringIO()
    stats_obj = pstats.Stats(profiler, stream=stream)
    stats_obj.sort_stats('cumulative')
    stats_obj.print_stats(20)  # Top 20 functions
    
    return {
        'execution_time_seconds': end_time - start_time,
        'profile_output': stream.getvalue(),
        'result': result
    }

def optimize_vectorization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize feature calculations using vectorization where possible.
    
    Args:
        df: DataFrame with aligned data
        
    Returns:
        Optimized DataFrame with vectorized calculations
    """
    logger.info("Applying vectorization optimizations...")
    
    # Vectorized variance calculation for teacher logits
    if 'teacher_logits' in df.columns:
        # Convert list of logits to numpy array for vectorized operations
        logits_array = np.array(df['teacher_logits'].tolist())
        df['variance_vectorized'] = np.var(logits_array, axis=1)
        df['range_vectorized'] = np.ptp(logits_array, axis=1)
    
    # Vectorized entropy calculation
    if 'teacher_logits' in df.columns:
        # Normalize logits to probabilities
        logits_array = np.array(df['teacher_logits'].tolist())
        exp_logits = np.exp(logits_array)
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        # Add small epsilon to avoid log(0)
        probs = np.clip(probs, 1e-10, 1.0)
        df['entropy_vectorized'] = -np.sum(probs * np.log(probs), axis=1)
    
    # Vectorized skewness and kurtosis
    if 'teacher_logits' in df.columns:
        logits_array = np.array(df['teacher_logits'].tolist())
        df['skewness_vectorized'] = stats.skew(logits_array, axis=1)
        df['kurtosis_vectorized'] = stats.kurtosis(logits_array, axis=1)
    
    return df

def optimize_parallel_processing(df: pd.DataFrame, n_jobs: int = -1) -> pd.DataFrame:
    """
    Optimize feature calculations using parallel processing.
    
    Args:
        df: DataFrame with aligned data
        n_jobs: Number of parallel jobs (-1 for all CPUs)
        
    Returns:
        DataFrame with parallel-computed features
    """
    logger.info(f"Applying parallel processing with {n_jobs} jobs...")
    
    # Prepare data for parallel processing
    samples = df.to_dict('records')
    
    def process_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single sample."""
        try:
            # Calculate per-sample stats
            stats_result = calculate_per_sample_stats(sample)
            return {**sample, **stats_result}
        except Exception as e:
            logger.warning(f"Error processing sample {sample.get('sample_id', 'unknown')}: {e}")
            return sample
    
    # Process samples in parallel
    processed_samples = Parallel(n_jobs=n_jobs, backend='loky')(
        delayed(process_sample)(sample) for sample in samples
    )
    
    # Convert back to DataFrame
    return pd.DataFrame(processed_samples)

def optimize_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage by downcasting numeric types and removing unused columns.
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Memory-optimized DataFrame
    """
    logger.info("Optimizing memory usage...")
    
    initial_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
    
    # Downcast numeric columns
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        if df[col].dtype == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif df[col].dtype == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Remove unnecessary columns if present
    columns_to_drop = [col for col in df.columns if col.startswith('_')]
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
    
    final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.info(f"Final memory usage: {final_memory:.2f} MB")
    logger.info(f"Memory reduction: {((initial_memory - final_memory) / initial_memory * 100):.2f}%")
    
    return df

def run_profiling_pipeline(data_path: str, output_path: str):
    """
    Run the full profiling and optimization pipeline.
    
    Args:
        data_path: Path to input data
        output_path: Path to output features
    """
    logger.info("Starting profiling and optimization pipeline...")
    
    # Load data
    logger.info("Loading aligned data...")
    df = load_aligned_data(data_path)
    logger.info(f"Loaded {len(df)} samples")
    
    # Profile baseline
    logger.info("Profiling baseline feature engineering...")
    baseline_result = profile_function(compute_all_features, df)
    baseline_time = baseline_result['execution_time_seconds']
    logger.info(f"Baseline execution time: {baseline_time:.2f} seconds")
    
    # Apply optimizations
    logger.info("Applying optimizations...")
    
    # Memory optimization
    df_optimized = optimize_memory_usage(df.copy())
    
    # Vectorization optimization
    df_vectorized = optimize_vectorization(df_optimized.copy())
    
    # Parallel processing optimization
    df_parallel = optimize_parallel_processing(df_optimized.copy())
    
    # Profile optimized version
    logger.info("Profiling optimized feature engineering...")
    optimized_result = profile_function(compute_all_features, df_parallel)
    optimized_time = optimized_result['execution_time_seconds']
    logger.info(f"Optimized execution time: {optimized_time:.2f} seconds")
    
    # Calculate improvement
    improvement = ((baseline_time - optimized_time) / baseline_time * 100)
    logger.info(f"Performance improvement: {improvement:.2f}%")
    
    # Save results
    results = {
        'baseline_time_seconds': baseline_time,
        'optimized_time_seconds': optimized_time,
        'improvement_percentage': improvement,
        'sample_count': len(df),
        'optimizations_applied': [
            'memory_downcasting',
            'vectorization',
            'parallel_processing'
        ],
        'profile_output': optimized_result['profile_output']
    }
    
    # Save profiling results
    profile_output_path = os.path.join(PROFILING_OUTPUT_DIR, 'profile_results.json')
    with open(profile_output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved profiling results to {profile_output_path}")
    
    # Save optimized features
    save_features_to_json(df_parallel, output_path)
    logger.info(f"Saved optimized features to {output_path}")
    
    return results

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Profile and optimize feature engineering loop for CPU efficiency'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/raw/zreward_dataset.csv',
        help='Path to input data file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/features_optimized.json',
        help='Path to output features file'
    )
    parser.add_argument(
        '--n-jobs',
        type=int,
        default=-1,
        help='Number of parallel jobs for optimization (-1 for all CPUs)'
    )
    return parser.parse_args()

def main():
    """Main entry point for profiling and optimization."""
    args = parse_args()
    
    setup_directories()
    
    try:
        results = run_profiling_pipeline(args.input, args.output)
        
        logger.info("=" * 60)
        logger.info("PROFILING AND OPTIMIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Baseline time: {results['baseline_time_seconds']:.2f}s")
        logger.info(f"Optimized time: {results['optimized_time_seconds']:.2f}s")
        logger.info(f"Improvement: {results['improvement_percentage']:.2f}%")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()