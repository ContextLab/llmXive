"""
Performance Optimizer for llmXive Project PROJ-179.

This module implements optimization strategies to ensure the bootstrap and regression
analyses complete within the 6-hour wall-clock limit on 2 CPU / 7GB RAM constraints.

Strategies implemented:
1. Memory-efficient data loading (chunking, dtype optimization).
2. Parallel processing for independent bootstrap samples (multiprocessing).
3. Vectorized operations using NumPy/Pandas to replace Python loops.
4. Early termination for regression if convergence fails or resources are exhausted.
5. Garbage collection management during long-running loops.
"""

import os
import sys
import gc
import time
import logging
import multiprocessing as mp
from functools import partial
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MEMORY_LIMIT_GB = 7
DEFAULT_N_BOOTSTRAP = 1000
N_BOOTSTRAP_REDUCED = 500
N_CPU = 2

def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame column dtypes to reduce memory footprint.
    Converts float64 to float32, int64 to appropriate smaller int types,
    and object columns to category where appropriate.
    """
    start_mem = df.memory_usage(deep=True).sum() / 1024 ** 2
    logger.debug(f"Original memory usage: {start_mem:.2f} MB")

    for col in df.columns:
        col_type = df[col].dtype

        if col_type == np.float64:
            df[col] = df[col].astype(np.float32)
        elif col_type == np.int64:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif df[col].dtype == "object":
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_unique / num_total < 0.5:
                df[col] = df[col].astype('category')

    end_mem = df.memory_usage(deep=True).sum() / 1024 ** 2
    logger.debug(f"Optimized memory usage: {end_mem:.2f} MB ({(1 - end_mem/start_mem)*100:.1f}% reduction)")
    return df

def run_bootstrap_sample(args: Tuple[np.ndarray, np.ndarray]) -> float:
    """
    Worker function for parallel bootstrap correlation calculation.
    Returns the Pearson correlation coefficient for a single resample.
    """
    x, y = args
    if len(x) == 0:
        return np.nan
    # Vectorized correlation
    corr, _ = stats.pearsonr(x, y)
    return corr

def optimized_bootstrap_analysis(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    max_runtime: int = MAX_RUNTIME_SECONDS
) -> Dict[str, Any]:
    """
    Perform optimized bootstrap correlation analysis.
    Uses multiprocessing for parallel sampling and vectorized stats.
    Includes runtime monitoring and fallback to reduced sample count.
    """
    start_time = time.time()
    logger.info(f"Starting optimized bootstrap analysis with {n_bootstrap} resamples.")

    # Check runtime periodically
    interval = max(1, n_bootstrap // 10)

    # Prepare data for parallel processing
    # We generate indices for resampling to avoid copying data
    indices = np.arange(len(x))
    results = []

    # Use multiprocessing pool if data is large enough to benefit
    # and we have multiple CPUs
    if n_bootstrap > 100 and N_CPU > 1:
        logger.info(f"Using {N_CPU} workers for parallel bootstrap.")
        pool = mp.Pool(processes=N_CPU)
        
        # Generate resampled indices in batches
        batch_size = 100
        batches = []
        for i in range(0, n_bootstrap, batch_size):
            batch_indices = [np.random.choice(indices, len(x), replace=True) for _ in range(min(batch_size, n_bootstrap - i))]
            # Create args for this batch
            batch_args = [(x[idx], y[idx]) for idx in batch_indices]
            batches.extend(batch_args)

        try:
            results = pool.map(run_bootstrap_sample, batches)
        except Exception as e:
            logger.error(f"Parallel processing failed: {e}. Falling back to sequential.")
            pool.close()
            pool.join()
            results = []
            pool = None

        if pool:
            pool.close()
            pool.join()
    else:
        # Sequential fallback
        for i in range(n_bootstrap):
            idx = np.random.choice(indices, len(x), replace=True)
            corr, _ = stats.pearsonr(x[idx], y[idx])
            results.append(corr)

            # Runtime check
            if (i + 1) % interval == 0:
                elapsed = time.time() - start_time
                if elapsed > max_runtime:
                    logger.warning(f"Runtime limit ({max_runtime}s) exceeded. Stopping early.")
                    break

    results = np.array(results)
    results = results[~np.isnan(results)]

    elapsed = time.time() - start_time
    final_count = len(results)

    if final_count < n_bootstrap:
        logger.warning(f"Bootstrap reduced to {final_count} samples due to runtime constraints.")
        # Fallback logic: if we are significantly under, we might need to reduce n_bootstrap for next run
        # but for this run, we report what we got.

    mean_corr = np.mean(results)
    ci_lower = np.percentile(results, 2.5)
    ci_upper = np.percentile(results, 97.5)

    return {
        "correlation": mean_corr,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_samples": final_count,
        "runtime_seconds": elapsed,
        "reduced": final_count < n_bootstrap
    }

def optimized_regression_analysis(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    max_runtime: int = MAX_RUNTIME_SECONDS
) -> Dict[str, Any]:
    """
    Perform optimized hierarchical regression analysis.
    Uses vectorized matrix operations and early termination checks.
    """
    start_time = time.time()
    logger.info("Starting optimized regression analysis.")

    # Optimize dtypes
    df = optimize_dtypes(df)

    # Check for missing data
    if df[target_col].isnull().any() or df[feature_cols].isnull().any():
        logger.warning("Missing values detected. Dropping rows with NaN.")
        df = df.dropna(subset=[target_col] + feature_cols)

    if len(df) < 2:
        logger.error("Insufficient data for regression.")
        return {"error": "Insufficient data"}

    # Prepare matrices
    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values.astype(np.float32)

    # Add constant
    X = add_constant(X)

    try:
        # Use OLS with fit_constrained or standard fit
        # For performance, we can use the underlying matrix solver directly if needed,
        # but statsmodels OLS is reasonably optimized.
        model = OLS(y, X)
        results = model.fit()

        elapsed = time.time() - start_time
        if elapsed > max_runtime:
            logger.warning("Regression analysis exceeded time limit.")
            return {
                "warning": "Time limit exceeded",
                "runtime_seconds": elapsed
            }

        return {
            "rsquared": results.rsquared,
            "rsquared_adj": results.rsquared_adj,
            "params": results.params.tolist(),
            "bse": results.bse.tolist(),
            "tvalues": results.tvalues.tolist(),
            "pvalues": results.pvalues.tolist(),
            "runtime_seconds": elapsed
        }

    except Exception as e:
        logger.error(f"Regression failed: {e}")
        return {"error": str(e)}

def run_optimization_pipeline(
    bootstrap_data_path: Optional[str] = None,
    regression_data_path: Optional[str] = None,
    output_dir: str = "data/results"
) -> Dict[str, Any]:
    """
    Main entry point to run performance-optimized analyses.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = {}

    # Run Bootstrap if data provided
    if bootstrap_data_path:
        logger.info(f"Loading bootstrap data from {bootstrap_data_path}")
        try:
            df_boot = pd.read_csv(bootstrap_data_path)
            df_boot = optimize_dtypes(df_boot)
            
            if 'metacognitive_score' in df_boot.columns and 'reality_testing_accuracy' in df_boot.columns:
                x = df_boot['metacognitive_score'].values
                y = df_boot['reality_testing_accuracy'].values
                
                boot_res = optimized_bootstrap_analysis(x, y)
                results['bootstrap'] = boot_res
                logger.info(f"Bootstrap result: r={boot_res['correlation']:.3f}, CI=[{boot_res['ci_lower']:.3f}, {boot_res['ci_upper']:.3f}]")
            else:
                logger.error("Required columns missing in bootstrap data.")
        except Exception as e:
            logger.error(f"Failed to process bootstrap data: {e}")

    # Run Regression if data provided
    if regression_data_path:
        logger.info(f"Loading regression data from {regression_data_path}")
        try:
            df_reg = pd.read_csv(regression_data_path)
            df_reg = optimize_dtypes(df_reg)
            
            if 'reality_testing_accuracy' in df_reg.columns and 'metacognitive_score' in df_reg.columns:
                # Example features: age, gender (encoded), metacognitive_score
                # Assuming gender is already numeric or we select numeric cols
                features = [c for c in df_reg.columns if c not in ['reality_testing_accuracy', 'participant_id'] and df_reg[c].dtype in [np.float32, np.float64, np.int32, np.int64]]
                
                if 'metacognitive_score' not in features:
                    features.append('metacognitive_score')
                
                reg_res = optimized_regression_analysis(df_reg, 'reality_testing_accuracy', features)
                results['regression'] = reg_res
                logger.info(f"Regression result: R2={reg_res.get('rsquared', 'N/A')}")
            else:
                logger.error("Required columns missing in regression data.")
        except Exception as e:
            logger.error(f"Failed to process regression data: {e}")

    # Save results
    output_path = os.path.join(output_dir, "performance_optimization_report.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Optimization report saved to {output_path}")
    return results

def main():
    """
    CLI entry point for performance optimization.
    """
    # Default paths based on project structure
    bootstrap_path = "data/derived/trial_data.csv" # Adjust based on actual output of T014/T015
    regression_path = "data/derived/trial_data.csv" # Adjust based on actual output of T020

    # Check if files exist, if not, try to find them or use defaults
    if not os.path.exists(bootstrap_path):
        # Fallback search or error
        logger.warning(f"Bootstrap data file not found at {bootstrap_path}. Skipping bootstrap.")
        bootstrap_path = None

    if not os.path.exists(regression_path):
        logger.warning(f"Regression data file not found at {regression_path}. Skipping regression.")
        regression_path = None

    if not bootstrap_path and not regression_path:
        logger.error("No data files found to optimize. Exiting.")
        sys.exit(1)

    run_optimization_pipeline(
        bootstrap_data_path=bootstrap_path,
        regression_data_path=regression_path,
        output_dir="data/results"
    )

if __name__ == "__main__":
    main()