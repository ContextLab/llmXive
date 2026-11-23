"""
T043: Performance Optimization Pipeline
Ensures float32 usage and batch processing across all analysis stories.
"""
import os
import gc
import logging
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any

# Import existing utilities from the project
from analysis.optimization_utils import (
    ensure_float32,
    process_in_batches,
    optimize_memory_usage,
    load_connectivity_matrix_optimized,
    batch_process_subjects,
    validate_float32_compliance,
    cleanup_temporary_files,
    run_optimization_pipeline as utils_run_opt
)
from utils.logging import setup_logger, get_resource_usage
from utils.config import get_config

# Setup module logger
logger = setup_logger(__name__, level=logging.INFO)

def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downcast numeric columns to float32 to reduce memory usage.
    Preserves object/string columns.
    """
    logger.info(f"Optimizing dtypes for DataFrame with shape {df.shape}")
    initial_memory = df.memory_usage(deep=True).sum()
    
    for col in df.columns:
        if df[col].dtype.kind in ['f', 'i']: # float or int
            # Downcast to float32 or int32 where possible
            if df[col].dtype.kind == 'f':
                min_val, max_val = df[col].min(), df[col].max()
                if min_val >= np.finfo(np.float32).min and max_val <= np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
            elif df[col].dtype.kind == 'i':
                min_val, max_val = df[col].min(), df[col].max()
                if min_val >= np.iinfo(np.int32).min and max_val <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
    
    final_memory = df.memory_usage(deep=True).sum()
    logger.info(f"Memory reduced from {initial_memory/1e6:.2f} MB to {final_memory/1e6:.2f} MB")
    return df

def optimize_centrality_data(input_path: str, output_path: str) -> None:
    """
    Read centrality metrics, ensure float32 compliance, and save.
    """
    logger.info(f"Optimizing centrality data: {input_path}")
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}, skipping.")
        return

    df = pd.read_csv(input_path)
    df = optimize_dataframe_dtypes(df)
    
    # Ensure specific centrality columns are float32
    centrality_cols = ['degree', 'betweenness', 'eigenvector', 'global_centralty']
    for col in centrality_cols:
        if col in df.columns:
            df[col] = df[col].astype(np.float32)

    # Save to output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved optimized centrality data to {output_path}")

def optimize_behavioral_data(input_path: str, output_path: str) -> None:
    """
    Read behavioral scores, ensure float32 compliance, and save.
    """
    logger.info(f"Optimizing behavioral data: {input_path}")
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}, skipping.")
        return

    df = pd.read_csv(input_path)
    df = optimize_dataframe_dtypes(df)
    
    # Ensure numeric score columns are float32
    score_cols = ['pre_motor_score', 'post_motor_score', 'improvement_score', 'age']
    for col in score_cols:
        if col in df.columns:
            df[col] = df[col].astype(np.float32)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved optimized behavioral data to {output_path}")

def optimize_regression_data(input_path: str, output_path: str) -> None:
    """
    Read regression summary or model predictors, ensure float32, and save.
    """
    logger.info(f"Optimizing regression data: {input_path}")
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}, skipping.")
        return

    df = pd.read_csv(input_path)
    df = optimize_dataframe_dtypes(df)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved optimized regression data to {output_path}")

def run_full_optimization_pipeline() -> Dict[str, Any]:
    """
    Executes the T043 optimization tasks across all data artifacts.
    """
    config = get_config()
    start_time = time.time()
    
    # Define paths based on standard project structure
    # These correspond to the outputs of previous tasks (T023, T017, T028, etc.)
    paths_to_optimize = [
        (
            "data/processed/centrality/subject_id_metrics.csv",
            "data/processed/centrality/subject_id_metrics_optimized.csv",
            optimize_centrality_data
        ),
        (
            "data/processed/behavioral/subject_scores.csv",
            "data/processed/behavioral/subject_scores_optimized.csv",
            optimize_behavioral_data
        ),
        (
            "data/processed/regression/model_predictors.csv",
            "data/processed/regression/model_predictors_optimized.csv",
            optimize_regression_data
        ),
        (
            "data/processed/regression/linear_model_summary.csv",
            "data/processed/regression/linear_model_summary_optimized.csv",
            optimize_regression_data
        ),
        (
            "data/processed/validation/null_distribution.csv",
            "data/processed/validation/null_distribution_optimized.csv",
            optimize_regression_data
        )
    ]

    results = {
        "status": "success",
        "files_processed": 0,
        "files_skipped": 0,
        "total_time_seconds": 0,
        "details": []
    }

    for input_path, output_path, func in paths_to_optimize:
        full_input = Path(input_path)
        if full_input.exists():
            try:
                func(str(full_input), output_path)
                results["files_processed"] += 1
                results["details"].append({
                    "input": str(full_input),
                    "output": output_path,
                    "status": "optimized"
                })
            except Exception as e:
                logger.error(f"Failed to optimize {input_path}: {e}")
                results["details"].append({
                    "input": str(full_input),
                    "output": output_path,
                    "status": "error",
                    "error": str(e)
                })
        else:
            logger.info(f"Skipping {input_path} (not found)")
            results["files_skipped"] += 1
            results["details"].append({
                "input": str(full_input),
                "output": output_path,
                "status": "skipped",
                "reason": "file_not_found"
            })

    # Cleanup temp files if any
    cleanup_temporary_files()
    
    # Force garbage collection
    gc.collect()
    
    end_time = time.time()
    results["total_time_seconds"] = end_time - start_time
    
    # Log resource usage
    mem_usage = get_resource_usage()
    logger.info(f"Optimization pipeline completed. Memory usage: {mem_usage.get('ram_mb', 'N/A')} MB")
    
    return results

def main():
    """
    Entry point for T043: Performance Optimization.
    """
    logger.info("Starting T043: Performance Optimization Pipeline")
    try:
        results = run_full_optimization_pipeline()
        logger.info(f"T043 Completed. Processed: {results['files_processed']}, Skipped: {results['files_skipped']}")
        
        # Save optimization summary
        import json
        summary_path = "data/artifacts/optimization_summary.json"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved optimization summary to {summary_path}")
        
    except Exception as e:
        logger.error(f"T043 Failed: {e}")
        raise

if __name__ == "__main__":
    main()
