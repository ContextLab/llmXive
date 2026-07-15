"""
Performance optimization for model fitting: batching, memory management, and efficient processing.

This module provides tools to handle large datasets within RAM constraints by:
1. Estimating and downcasting memory usage
2. Splitting data into memory-safe batches
3. Fitting models in batches with garbage collection
4. Running batched model fitting with progress tracking
"""
import gc
import logging
import multiprocessing as mp
import os
import sys
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from utils.config import get_memory_limit_bytes, get_max_ram_gb

logger = logging.getLogger(__name__)

# Constants for memory management
MEMORY_SAFETY_FACTOR = 0.7  # Use only 70% of available RAM for safety
BATCH_SIZE_ROWS = 50000  # Default batch size if not calculated dynamically
MIN_BATCH_SIZE_ROWS = 10000
MAX_BATCH_SIZE_ROWS = 200000

def estimate_dataframe_memory(df: pd.DataFrame) -> int:
    """
    Estimate the memory usage of a DataFrame in bytes.
    
    Args:
        df: pandas DataFrame to estimate
        
    Returns:
        Estimated memory usage in bytes
    """
    return df.memory_usage(deep=True).sum()

def downcast_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downcast numeric columns to reduce memory usage.
    
    Converts int64 to smallest possible int type, float64 to float32,
    and optimizes object/string columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with optimized dtypes
    """
    logger.info("Downcasting DataFrame dtypes to reduce memory usage...")
    initial_memory = estimate_dataframe_memory(df)
    
    # Numeric downcasting
    for col in df.select_dtypes(include=['int64']).columns:
        min_val = df[col].min()
        max_val = df[col].max()
        
        if min_val >= 0:
            if max_val <= np.iinfo(np.uint8).max:
                df[col] = df[col].astype(np.uint8)
            elif max_val <= np.iinfo(np.uint16).max:
                df[col] = df[col].astype(np.uint16)
            elif max_val <= np.iinfo(np.uint32).max:
                df[col] = df[col].astype(np.uint32)
        else:
            if min_val >= np.iinfo(np.int8).min and max_val <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif min_val >= np.iinfo(np.int16).min and max_val <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif min_val >= np.iinfo(np.int32).min and max_val <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
    
    for col in df.select_dtypes(include=['float64']).columns:
        if df[col].isna().any():
            # Check if float32 can represent the values
            if df[col].min() >= np.finfo(np.float32).min and df[col].max() <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
        else:
            if df[col].min() >= np.finfo(np.float32).min and df[col].max() <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
    
    # String/object optimization
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df[col]) < 0.5:  # Only convert if low cardinality
            df[col] = df[col].astype('category')
    
    final_memory = estimate_dataframe_memory(df)
    reduction = (1 - final_memory / initial_memory) * 100
    logger.info(f"Memory reduced from {initial_memory / 1e6:.2f}MB to {final_memory / 1e6:.2f}MB ({reduction:.1f}% reduction)")
    
    return df

def split_dataframe_by_memory(
    df: pd.DataFrame, 
    max_memory_bytes: Optional[int] = None,
    target_batch_rows: Optional[int] = None
) -> List[pd.DataFrame]:
    """
    Split a DataFrame into batches that fit within memory constraints.
    
    Args:
        df: Input DataFrame
        max_memory_bytes: Maximum memory per batch (defaults to calculated safe limit)
        target_batch_rows: Desired rows per batch (overrides memory calculation)
        
    Returns:
        List of DataFrame batches
    """
    if max_memory_bytes is None:
        max_ram = get_max_ram_gb() * 1e9
        max_memory_bytes = int(max_ram * MEMORY_SAFETY_FACTOR * 0.5)  # Leave room for model objects
    
    total_memory = estimate_dataframe_memory(df)
    total_rows = len(df)
    
    if total_memory <= max_memory_bytes:
        logger.info(f"DataFrame fits in memory ({total_memory / 1e6:.2f}MB < {max_memory_bytes / 1e6:.2f}MB). No splitting needed.")
        return [df]
    
    # Calculate batch size
    if target_batch_rows:
        batch_size = min(target_batch_rows, MAX_BATCH_SIZE_ROWS)
        batch_size = max(batch_size, MIN_BATCH_SIZE_ROWS)
    else:
        # Estimate rows per batch based on memory ratio
        memory_ratio = max_memory_bytes / total_memory
        batch_size = max(int(total_rows * memory_ratio), MIN_BATCH_SIZE_ROWS)
        batch_size = min(batch_size, MAX_BATCH_SIZE_ROWS)
    
    num_batches = (total_rows + batch_size - 1) // batch_size
    logger.info(f"Splitting {total_rows:,} rows into {num_batches} batches of ~{batch_size:,} rows each")
    
    batches = []
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, total_rows)
        batch = df.iloc[start_idx:end_idx].copy()
        batch = downcast_dataframe(batch)
        batches.append(batch)
        logger.debug(f"Batch {i+1}/{num_batches}: {len(batch):,} rows, {estimate_dataframe_memory(batch) / 1e6:.2f}MB")
    
    return batches

def fit_model_batch(
    df_batch: pd.DataFrame,
    formula: str,
    group_col: str,
    batch_id: int,
    model_type: str = 'mixedlm'
) -> Dict[str, Any]:
    """
    Fit a model on a single batch of data.
    
    Args:
        df_batch: DataFrame batch to fit
        formula: Model formula string
        group_col: Column name for grouping (random effects)
        batch_id: Identifier for this batch
        model_type: Type of model to fit ('mixedlm', 'ols', etc.)
        
    Returns:
        Dictionary with model results and metadata
    """
    start_time = time.time()
    result = {
        'batch_id': batch_id,
        'n_rows': len(df_batch),
        'n_groups': df_batch[group_col].nunique(),
        'success': False,
        'error': None,
        'fit_time': 0,
        'params': None,
        'pvalues': None,
        'log_likelihood': None
    }
    
    try:
        # Force garbage collection before fitting
        gc.collect()
        
        if model_type == 'mixedlm':
            # Mixed Effects Model
            try:
                model = smf.mixedlm(formula, df_batch, groups=df_batch[group_col])
                fitted = model.fit(reml=False, maxiter=1000)
                
                result['params'] = fitted.params.to_dict()
                result['pvalues'] = fitted.pvalues.to_dict()
                result['log_likelihood'] = fitted.llf
                result['success'] = True
            except Exception as e:
                # Fallback to OLS if mixed model fails
                logger.warning(f"MixedLM failed for batch {batch_id}: {str(e)}. Trying OLS.")
                model = smf.ols(formula, df_batch)
                fitted = model.fit()
                
                result['params'] = fitted.params.to_dict()
                result['pvalues'] = fitted.pvalues.to_dict()
                result['log_likelihood'] = fitted.llf
                result['success'] = True
                result['model_type_used'] = 'ols_fallback'
        else:
            # OLS Model
            model = smf.ols(formula, df_batch)
            fitted = model.fit()
            
            result['params'] = fitted.params.to_dict()
            result['pvalues'] = fitted.pvalues.to_dict()
            result['log_likelihood'] = fitted.llf
            result['success'] = True
    
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Model fitting failed for batch {batch_id}: {str(e)}")
    
    result['fit_time'] = time.time() - start_time
    logger.info(f"Batch {batch_id} completed: {result['success']}, {result['fit_time']:.2f}s")
    
    return result

def run_batched_model_fitting(
    df: pd.DataFrame,
    formula: str,
    group_col: str,
    max_memory_bytes: Optional[int] = None,
    model_type: str = 'mixedlm',
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run model fitting on a large dataset using batching.
    
    This function:
    1. Splits the data into memory-safe batches
    2. Fits the model on each batch
    3. Aggregates results (simple averaging of parameters)
    4. Saves results if output_path is provided
    
    Args:
        df: Full dataset
        formula: Model formula
        group_col: Grouping column for random effects
        max_memory_bytes: Memory limit per batch
        model_type: Model type to fit
        output_path: Optional path to save results
        
    Returns:
        Aggregated results dictionary
    """
    logger.info(f"Starting batched model fitting for {len(df):,} rows")
    logger.info(f"Formula: {formula}")
    logger.info(f"Group column: {group_col}")
    
    # Downcast and split
    df_optimized = downcast_dataframe(df.copy())
    batches = split_dataframe_by_memory(df_optimized, max_memory_bytes)
    
    logger.info(f"Created {len(batches)} batches")
    
    # Fit models on each batch
    batch_results = []
    total_start = time.time()
    
    for i, batch in enumerate(batches):
        result = fit_model_batch(batch, formula, group_col, i, model_type)
        batch_results.append(result)
        
        # Explicit garbage collection after each batch
        gc.collect()
    
    total_time = time.time() - total_start
    
    # Aggregate results (simple averaging of parameters)
    all_params = {}
    all_pvalues = {}
    successful_batches = [r for r in batch_results if r['success']]
    
    if successful_batches:
        # Average parameters across batches
        param_keys = set()
        for res in successful_batches:
            if res['params']:
                param_keys.update(res['params'].keys())
        
        for key in param_keys:
            values = [r['params'][key] for r in successful_batches if r['params'] and key in r['params']]
            if values:
                all_params[key] = np.mean(values)
        
        # Average p-values
        pvalue_keys = set()
        for res in successful_batches:
            if res['pvalues']:
                pvalue_keys.update(res['pvalues'].keys())
        
        for key in pvalue_keys:
            values = [r['pvalues'][key] for r in successful_batches if r['pvalues'] and key in r['pvalues']]
            if values:
                all_pvalues[key] = np.mean(values)
    
    aggregated_result = {
        'total_rows': len(df),
        'total_batches': len(batches),
        'successful_batches': len(successful_batches),
        'total_fit_time': total_time,
        'avg_fit_time_per_batch': total_time / len(batches) if batches else 0,
        'params': all_params,
        'pvalues': all_pvalues,
        'batch_details': batch_results
    }
    
    # Save results if path provided
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(i) for i in obj]
            return obj
        
        serializable_result = convert_numpy(aggregated_result)
        
        with open(output_path, 'w') as f:
            json.dump(serializable_result, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
    
    return aggregated_result

def calculate_memory_requirements(df: pd.DataFrame, model_complexity: float = 1.5) -> Dict[str, int]:
    """
    Calculate memory requirements for model fitting.
    
    Args:
        df: Input DataFrame
        model_complexity: Multiplier for model object memory (default 1.5x data size)
        
    Returns:
        Dictionary with memory requirements
    """
    data_memory = estimate_dataframe_memory(df)
    model_memory = int(data_memory * model_complexity)
    total_required = data_memory + model_memory
    available = get_max_ram_gb() * 1e9 * MEMORY_SAFETY_FACTOR
    
    return {
        'data_memory_bytes': data_memory,
        'estimated_model_memory_bytes': model_memory,
        'total_required_bytes': total_required,
        'available_safe_bytes': int(available),
        'fits_in_memory': total_required <= available,
        'memory_utilization_percent': (total_required / available) * 100 if available > 0 else 100
    }

def main():
    """
    Main entry point for performance optimization demonstration.
    
    This function:
    1. Loads processed data
    2. Calculates memory requirements
    3. Runs batched model fitting
    4. Outputs results
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    from utils.config import get_processed_data_dir
    from pathlib import Path
    
    # Load data
    data_dir = get_processed_data_dir()
    input_path = data_dir / "merged_sample.parquet"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("Please run the data pipeline first to generate merged_sample.parquet")
        return
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df):,} rows")
    
    # Calculate memory requirements
    memory_reqs = calculate_memory_requirements(df)
    logger.info(f"Memory requirements: {memory_reqs['total_required_bytes'] / 1e6:.2f}MB needed, "
               f"{memory_reqs['available_safe_bytes'] / 1e6:.2f}MB available")
    
    if not memory_reqs['fits_in_memory']:
        logger.info("Data does not fit in memory. Using batched approach.")
    else:
        logger.info("Data fits in memory. Can process directly or use batching for consistency.")
    
    # Define model formula (example - should match actual model from model.py)
    formula = "food_security_index ~ csa_index + digital_access + finance_access + " \
             "conservation_tillage + crop_diversity + irrigation_efficiency + " \
             "household_size + education_years + age"
    group_col = "country"
    
    # Run batched fitting
    output_path = Path("data/processed/batched_model_results.json")
    
    results = run_batched_model_fitting(
        df=df,
        formula=formula,
        group_col=group_col,
        model_type='mixedlm',
        output_path=output_path
    )
    
    logger.info(f"Batched fitting completed in {results['total_fit_time']:.2f}s")
    logger.info(f"Successful batches: {results['successful_batches']}/{results['total_batches']}")
    logger.info(f"Results saved to {output_path}")
    
    # Print summary
    print("\n=== Model Fitting Summary ===")
    print(f"Total rows: {results['total_rows']:,}")
    print(f"Batches: {results['total_batches']}")
    print(f"Successful: {results['successful_batches']}")
    print(f"Total time: {results['total_fit_time']:.2f}s")
    print(f"Avg time/batch: {results['avg_fit_time_per_batch']:.2f}s")
    
    if results['params']:
        print("\nTop 5 parameters by magnitude:")
        sorted_params = sorted(results['params'].items(), key=lambda x: abs(x[1]), reverse=True)
        for param, value in sorted_params[:5]:
            pval = results['pvalues'].get(param, 'N/A')
            print(f"  {param}: {value:.4f} (p={pval})")

if __name__ == "__main__":
    main()