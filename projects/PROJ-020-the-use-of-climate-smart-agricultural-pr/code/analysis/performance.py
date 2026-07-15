"""
Performance optimization module for model fitting.
Implements batching, memory-efficient data handling, and parallel processing
to handle large datasets within RAM constraints.
"""
import gc
import logging
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Generator

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from tqdm import tqdm

from utils.config import get_max_ram_gb, get_memory_limit_bytes
from utils.refactor_utils import calculate_memory_usage

logger = logging.getLogger(__name__)


def estimate_dataframe_memory(df: pd.DataFrame) -> int:
    """
    Estimate the memory usage of a DataFrame in bytes.
    
    Args:
        df: The DataFrame to estimate memory for.
        
    Returns:
        Estimated memory usage in bytes.
    """
    return df.memory_usage(deep=True).sum()


def downcast_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downcast numeric columns to reduce memory usage.
    
    Converts float64 to float32, int64 to int32/16/8 where possible,
    and categorizes low-cardinality object columns.
    
    Args:
        df: The DataFrame to downcast.
        
    Returns:
        A new DataFrame with reduced memory usage.
    """
    df_optimized = df.copy()
    
    # Select numeric columns
    numeric_cols = df_optimized.select_dtypes(include=['int64', 'float64']).columns
    
    for col in numeric_cols:
        col_data = df_optimized[col]
        min_val = col_data.min()
        max_val = col_data.max()
        
        # Downcast integers
        if col_data.dtype == 'int64':
            if min_val >= np.iinfo(np.int8).min and max_val <= np.iinfo(np.int8).max:
                df_optimized[col] = col_data.astype(np.int8)
            elif min_val >= np.iinfo(np.int16).min and max_val <= np.iinfo(np.int16).max:
                df_optimized[col] = col_data.astype(np.int16)
            elif min_val >= np.iinfo(np.int32).min and max_val <= np.iinfo(np.int32).max:
                df_optimized[col] = col_data.astype(np.int32)
        
        # Downcast floats
        elif col_data.dtype == 'float64':
            if min_val >= np.finfo(np.float32).min and max_val <= np.finfo(np.float32).max:
                df_optimized[col] = col_data.astype(np.float32)
    
    # Downcast object columns to category if low cardinality
    object_cols = df_optimized.select_dtypes(include=['object']).columns
    for col in object_cols:
        if df_optimized[col].nunique() / len(df_optimized) < 0.5:
            df_optimized[col] = df_optimized[col].astype('category')
    
    return df_optimized


def split_dataframe_by_memory(
    df: pd.DataFrame, 
    max_memory_gb: Optional[float] = None,
    target_batches: int = 4
) -> List[pd.DataFrame]:
    """
    Split a DataFrame into multiple chunks based on memory constraints.
    
    Args:
        df: The DataFrame to split.
        max_memory_gb: Maximum memory per batch in GB. If None, uses config.
        target_batches: Target number of batches to create.
        
    Returns:
        List of DataFrame chunks.
    """
    if max_memory_gb is None:
        max_memory_gb = get_max_ram_gb() * 0.7  # Use 70% of max RAM
    
    total_memory = estimate_dataframe_memory(df)
    max_memory_bytes = int(max_memory_gb * 1024**3)
    
    # If already within limits, return as single batch
    if total_memory <= max_memory_bytes:
        return [df]
    
    # Calculate split ratio
    split_ratio = max_memory_bytes / total_memory
    num_batches = max(2, int(1 / split_ratio))
    num_batches = min(num_batches, target_batches)
    
    # Split by rows
    total_rows = len(df)
    rows_per_batch = total_rows // num_batches
    
    batches = []
    for i in range(num_batches):
        start_idx = i * rows_per_batch
        end_idx = rows_per_batch if i == num_batches - 1 else (i + 1) * rows_per_batch
        batch = df.iloc[start_idx:end_idx].reset_index(drop=True)
        batches.append(downcast_dataframe(batch))
    
    logger.info(f"Split DataFrame into {len(batches)} batches. "
               f"Original size: {total_rows:,} rows, {total_memory / 1024**3:.2f} GB")
    
    return batches


def fit_model_batch(
    data: pd.DataFrame,
    formula: str,
    group_col: str,
    batch_id: int = 0
) -> Dict[str, Any]:
    """
    Fit a mixed-effects model on a single batch of data.
    
    Args:
        data: DataFrame containing the batch data.
        formula: Model formula string.
        group_col: Column name for random effects grouping.
        batch_id: Identifier for the batch.
        
    Returns:
        Dictionary containing model results and metadata.
    """
    start_time = time.time()
    
    try:
        # Fit the model
        model = smf.mixedlm(formula, data, groups=data[group_col])
        result = model.fit(reml=False, maxiter=100)
        
        elapsed_time = time.time() - start_time
        
        return {
            'batch_id': batch_id,
            'status': 'success',
            'elapsed_time': elapsed_time,
            'n_obs': len(data),
            'n_groups': data[group_col].nunique(),
            'coefficients': result.params.to_dict(),
            'pvalues': result.pvalues.to_dict(),
            'aic': result.aic,
            'bic': result.bic,
            'loglike': result.llf
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Batch {batch_id} failed: {str(e)}")
        
        return {
            'batch_id': batch_id,
            'status': 'failed',
            'error': str(e),
            'elapsed_time': elapsed_time,
            'n_obs': len(data) if data is not None else 0,
            'n_groups': 0
        }


def run_batched_model_fitting(
    data: pd.DataFrame,
    formula: str,
    group_col: str,
    max_memory_gb: Optional[float] = None,
    use_multiprocessing: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run model fitting on batches of data with memory optimization.
    
    Args:
        data: Full DataFrame to fit the model on.
        formula: Model formula string.
        group_col: Column name for random effects grouping.
        max_memory_gb: Maximum memory per batch in GB.
        use_multiprocessing: Whether to use multiprocessing for parallel batches.
        
    Returns:
        Tuple of (list of batch results, summary statistics).
    """
    start_time = time.time()
    
    # Optimize memory first
    logger.info("Optimizing DataFrame memory...")
    data_optimized = downcast_dataframe(data)
    initial_memory = estimate_dataframe_memory(data_optimized)
    
    # Split into batches if necessary
    batches = split_dataframe_by_memory(data_optimized, max_memory_gb)
    num_batches = len(batches)
    
    logger.info(f"Processing {num_batches} batches...")
    
    results = []
    
    if use_multiprocessing and num_batches > 1:
        # Parallel processing
        logger.info(f"Using multiprocessing with {mp.cpu_count()} workers")
        
        with mp.Pool(processes=min(num_batches, mp.cpu_count())) as pool:
            tasks = [
                (batch, formula, group_col, i) 
                for i, batch in enumerate(batches)
            ]
            
            # Use imap to process batches and update progress
            for result in tqdm(
                pool.starmap(fit_model_batch, tasks),
                total=num_batches,
                desc="Fitting batches"
            ):
                results.append(result)
                # Force garbage collection between batches
                gc.collect()
    else:
        # Sequential processing
        for i, batch in enumerate(tqdm(batches, desc="Fitting batches")):
            result = fit_model_batch(batch, formula, group_col, i)
            results.append(result)
            gc.collect()
    
    # Calculate summary statistics
    total_time = time.time() - start_time
    successful_batches = [r for r in results if r['status'] == 'success']
    
    summary = {
        'total_time': total_time,
        'num_batches': num_batches,
        'successful_batches': len(successful_batches),
        'failed_batches': num_batches - len(successful_batches),
        'initial_memory_gb': initial_memory / 1024**3,
        'avg_time_per_batch': total_time / num_batches if num_batches > 0 else 0,
        'total_observations': sum(r.get('n_obs', 0) for r in results),
        'total_groups': max((r.get('n_groups', 0) for r in results), default=0)
    }
    
    logger.info(f"Batched fitting completed in {total_time:.2f}s. "
               f"Success rate: {len(successful_batches)}/{num_batches}")
    
    return results, summary


def calculate_memory_requirements(
    df: pd.DataFrame,
    formula: str,
    group_col: str
) -> Dict[str, float]:
    """
    Calculate memory requirements for model fitting.
    
    Args:
        df: DataFrame to analyze.
        formula: Model formula.
        group_col: Grouping column.
        
    Returns:
        Dictionary with memory estimates.
    """
    df_opt = downcast_dataframe(df)
    data_memory = estimate_dataframe_memory(df_opt)
    
    # Estimate model matrix memory (rough approximation)
    # Model matrix size ~ (n_obs * n_predictors * 8 bytes)
    n_obs = len(df_opt)
    # Count predictors from formula (simplified)
    formula_parts = formula.split('+')
    n_predictors = len([p for p in formula_parts if p.strip() and p.strip() != '1'])
    
    model_matrix_memory = n_obs * n_predictors * 8  # float64
    
    total_memory = data_memory + model_matrix_memory
    
    return {
        'data_memory_gb': data_memory / 1024**3,
        'model_matrix_memory_gb': model_matrix_memory / 1024**3,
        'total_memory_gb': total_memory / 1024**3,
        'recommended_batch_size_gb': min(2.0, total_memory / 1024**3 * 0.7)
    }


def main():
    """
    Main entry point for performance optimization testing.
    
    Demonstrates memory-efficient model fitting on large datasets.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting performance optimization demonstration...")
    
    # Load example data (in real usage, this would come from data/processed/)
    try:
        data_path = Path("data/processed/merged_sample.parquet")
        if not data_path.exists():
            logger.warning(f"Data file not found at {data_path}. "
                         "Skipping demonstration. Please run the data pipeline first.")
            return
        
        data = pd.read_parquet(data_path)
        logger.info(f"Loaded {len(data):,} rows. "
                   f"Memory: {calculate_memory_usage(data):.2f} MB")
        
    except FileNotFoundError:
        logger.error("Processed data file not found. Run data pipeline first.")
        return
    
    # Define model formula (example)
    formula = "food_security_index ~ csa_index + digital_access + finance_access + " \
             "crop_diversity + irrigation + household_size"
    group_col = "region"
    
    # Calculate memory requirements
    memory_reqs = calculate_memory_requirements(data, formula, group_col)
    logger.info(f"Memory requirements: {memory_reqs['total_memory_gb']:.2f} GB total")
    
    # Run batched fitting
    results, summary = run_batched_model_fitting(
        data=data,
        formula=formula,
        group_col=group_col,
        use_multiprocessing=True
    )
    
    # Log summary
    logger.info(f"=== Performance Summary ===")
    logger.info(f"Total time: {summary['total_time']:.2f}s")
    logger.info(f"Batches processed: {summary['num_batches']}")
    logger.info(f"Success rate: {summary['successful_batches']}/{summary['num_batches']}")
    logger.info(f"Average time per batch: {summary['avg_time_per_batch']:.2f}s")
    
    # Save results
    output_dir = Path("state")
    output_dir.mkdir(exist_ok=True)
    
    results_path = output_dir / "performance_results.json"
    import json
    with open(results_path, 'w') as f:
        json.dump({
            'summary': summary,
            'memory_requirements': memory_reqs,
            'batch_results': results
        }, f, indent=2, default=str)
    
    logger.info(f"Results saved to {results_path}")
    
    return results, summary


if __name__ == "__main__":
    main()