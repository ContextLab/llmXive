"""
Performance optimization utilities for the accessibility study pipeline.

This module provides profiling and optimization helpers to identify bottlenecks
in data processing and statistical analysis, ensuring the pipeline remains
responsive for large datasets (N > 1000).

Key optimizations:
1. Vectorized Pandas operations instead of row-wise iteration.
2. Caching for expensive statistical computations.
3. Memory-efficient chunking for large CSV/JSON loads.
"""

import os
import time
import functools
import tracemalloc
from typing import Callable, Any, Dict, Optional, List
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats

from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


def profile_execution(func: Callable) -> Callable:
    """
    Decorator to profile execution time and memory usage of a function.
    Logs results to the configured logger.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        tracemalloc.start()

        try:
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            elapsed = time.perf_counter() - start_time
            logger.info(
                f"Performance Profile: {func.__name__} took {elapsed:.4f}s "
                f"(Peak Memory: {peak / 1024:.2f} KB)"
            )
            return result
        except Exception as e:
            tracemalloc.stop()
            logger.error(f"Performance Profile failed for {func.__name__}: {e}")
            raise
    return wrapper


def optimize_dataframe_loading(file_path: str, chunk_size: int = 1000) -> pd.DataFrame:
    """
    Loads large CSV/JSON files in chunks to prevent memory spikes.
    Automatically infers dtypes to reduce memory footprint.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Optimizing load for: {file_path}")

    if path.suffix == '.csv':
        # Use dtype inference and chunking
        df_iter = pd.read_csv(file_path, chunksize=chunk_size)
        chunks = []
        for chunk in df_iter:
            # Optional: downcast numeric types here if needed
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    elif path.suffix == '.json':
        # JSON is harder to chunk efficiently without specific structure,
        # but we can load and then optimize dtypes
        df = pd.read_json(file_path)
    else:
        # Fallback to standard load
        if path.suffix == '.parquet':
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)

    # Generic memory optimization: downcast numeric columns
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer' if df[col].dtype == np.int64 else 'float')

    logger.info(f"Loaded {len(df)} rows with optimized memory footprint.")
    return df


class StatisticalCache:
    """
    Simple in-memory cache for expensive statistical computations.
    Key is generated from input data hash and function name.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def _make_key(self, func_name: str, data_hash: str) -> str:
        return f"{func_name}:{data_hash}"

    def get(self, func_name: str, data: pd.DataFrame, default: Optional[Any] = None) -> Optional[Any]:
        # Simple hash of the dataframe content for caching
        # In production, consider a more robust hashing strategy for large data
        data_hash = hash(data.to_json())
        key = self._make_key(func_name, str(data_hash))
        return self._cache.get(key, default)

    def set(self, func_name: str, data: pd.DataFrame, value: Any) -> None:
        data_hash = hash(data.to_json())
        key = self._make_key(func_name, str(data_hash))
        self._cache[key] = value
        logger.debug(f"Cached result for {func_name}")

    def clear(self) -> None:
        self._cache.clear()
        logger.info("Statistical cache cleared.")


# Global cache instance
stat_cache = StatisticalCache()


@profile_execution
def run_vectorized_statistical_tests(df: pd.DataFrame, metric_col: str, group_col: str) -> Dict[str, float]:
    """
    Optimized statistical testing using vectorized operations.
    Replaces slow row-wise or group-by-apply loops with direct vectorized calls.

    Args:
        df: Input DataFrame.
        metric_col: Column name for the metric to test.
        group_col: Column name for the grouping variable (e.g., interface type).

    Returns:
        Dictionary with test statistics and p-values.
    """
    if metric_col not in df.columns or group_col not in df.columns:
        raise ValueError(f"Columns {metric_col} or {group_col} not found in DataFrame.")

    results = {}
    groups = df[group_col].unique()

    if len(groups) < 2:
        logger.warning("Less than 2 groups found, skipping ANOVA.")
        return {"error": "Insufficient groups"}

    # Extract groups into lists for scipy
    group_data = [df[df[group_col] == g][metric_col].dropna().values for g in groups]

    # Repeated Measures ANOVA approximation (One-way for simplicity if structure allows)
    # Note: For true repeated measures, we need subject IDs. Assuming independent for this generic optimizer
    # or if the data is already shaped for within-subject comparison.
    # If subject ID exists, we should pivot first.
    
    try:
        f_stat, p_val = stats.f_oneway(*group_data)
        results['f_statistic'] = float(f_stat)
        results['p_value'] = float(p_val)
        
        # Effect size (Eta-squared)
        # Eta^2 = SS_between / SS_total
        # Approximation for simple ANOVA
        grand_mean = np.mean(np.concatenate(group_data))
        ss_total = sum(np.sum((x - grand_mean)**2) for x in group_data)
        ss_between = sum(len(x) * (np.mean(x) - grand_mean)**2 for x in group_data)
        
        if ss_total > 0:
            results['eta_squared'] = float(ss_between / ss_total)
        else:
            results['eta_squared'] = 0.0

    except Exception as e:
        logger.error(f"Statistical test failed: {e}")
        results['error'] = str(e)

    return results


def main():
    """
    Entry point for running performance optimization benchmarks.
    Reads settings, loads sample data (if available), and runs optimized tests.
    """
    settings = get_settings()
    data_dir = settings.data_processed_dir
    raw_dir = settings.data_raw_dir

    logger.info("Starting Performance Optimization Benchmark...")

    # Check for processed metrics summary
    metrics_file = Path(data_dir) / "metrics_summary.csv"
    if metrics_file.exists():
        logger.info(f"Loading metrics from {metrics_file}...")
        try:
            df = optimize_dataframe_loading(str(metrics_file))
            
            # Run vectorized stats if columns exist
            if 'metric_name' in df.columns and 'interface_type' in df.columns:
                results = run_vectorized_statistical_tests(df, 'mean', 'interface_type')
                logger.info(f"Optimized Test Results: {results}")
            else:
                logger.warning("Expected columns not found in metrics_summary.csv for vectorized test.")
        except Exception as e:
            logger.error(f"Benchmark failed during execution: {e}")
    else:
        logger.info("No processed metrics found to benchmark against. Skipping data load test.")
    
    logger.info("Performance optimization benchmark complete.")


if __name__ == "__main__":
    main()
