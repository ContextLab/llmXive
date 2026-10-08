"""
Optimized Predictive Modeling Pipeline for Gut Microbiome and Cognitive Decline Analysis.

This module implements performance optimizations for data loading and permutation loops
as required by Task T039. It leverages chunked loading, vectorized operations, and
parallel processing where applicable.

Dependencies:
- pandas, numpy, scikit-learn, scipy, utils.performance_utils
"""
import os
import sys
import logging
import json
import time
import random
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

# Import from local utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.performance_utils import (
    MemoryMonitor, load_parquet_chunked, batch_process,
    optimized_shuffle, gc_collect_if_needed, timed_operation
)
from utils.logging import get_logger, log_memory_usage
from utils.resource_guard import check_cpu_only, ResourceMonitor

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Constants
DATA_DIR = Path("data/processed")
MODELS_DIR = Path("data/models")
CLR_DATA_PATH = DATA_DIR / "corpus_clr.parquet"
COVARIATE_PATH = DATA_DIR / "merged_covariates.parquet"  # Assuming this exists from preprocessing
OUTPUT_THRESHOLD_PATH = DATA_DIR / "null_threshold.json"
OUTPUT_TOP_TAXA_PATH = DATA_DIR / "top_taxa_initial.json"
OUTPUT_TOP_TAXA_FINAL_PATH = DATA_DIR / "top_taxa_final.json"
OUTPUT_RESULTS_PATH = DATA_DIR / "model_results_optimized.json"
OUTPUT_MEMORY_LOG_PATH = DATA_DIR / "memory_log_optimized.txt"

def load_preprocessed_data_optimized() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load preprocessed CLR-transformed data and cognitive scores using chunked loading
    to optimize memory usage for large datasets.
    
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    logger.info("Starting optimized data loading...")
    monitor = MemoryMonitor()
    monitor.start()
    
    try:
        # Load CLR data in chunks if large, otherwise direct load
        # Assuming corpus_clr.parquet contains both features and a 'cognitive_score' column
        # or it is joined with covariates elsewhere.
        # For this implementation, we assume the file contains features and we need to fetch targets.
        
        # Strategy: Load features (CLR)
        if CLR_DATA_PATH.exists():
            # Check file size to decide strategy
            file_size_mb = CLR_DATA_PATH.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                logger.info(f"Loading large dataset ({file_size_mb:.1f} MB) in chunks.")
                features_df = load_parquet_chunked(CLR_DATA_PATH)
            else:
                logger.info(f"Loading dataset ({file_size_mb:.1f} MB) directly.")
                features_df = pd.read_parquet(CLR_DATA_PATH)
        else:
            raise FileNotFoundError(f"CLR data file not found at {CLR_DATA_PATH}")
        
        # Extract cognitive score (assuming column name 'cognitive_score' or similar)
        # If the target is in a separate file, load it here.
        # For this optimized module, we assume the target is in the same dataframe or 
        # we join it. Let's assume 'cognitive_score' is in features_df or we load it.
        
        # If target is separate (common in US1/US2 pipelines):
        if COVARIATE_PATH.exists():
            covariates_df = pd.read_parquet(CVARIATE_PATH)
            # Merge on sample_id if necessary
            # Assuming index alignment or 'sample_id' column exists
            if 'sample_id' in features_df.columns and 'sample_id' in covariates_df.columns:
                features_df = features_df.merge(covariates_df[['sample_id', 'cognitive_score']], on='sample_id')
            elif 'cognitive_score' not in features_df.columns:
                # Try to infer target column
                target_col = 'cognitive_score'
                if target_col in covariates_df.columns:
                    # Align by index if possible
                    features_df[target_col] = covariates_df[target_col].values[:len(features_df)]
                else:
                    raise ValueError("Target column 'cognitive_score' not found in data.")
        
        if 'cognitive_score' not in features_df.columns:
            # Fallback: look for common names
            possible_names = ['cognitive_score', 'cognitive', 'score', 'outcome']
            found = next((c for c in possible_names if c in features_df.columns), None)
            if found:
                features_df['cognitive_score'] = features_df[found]
            else:
                raise ValueError("Could not identify cognitive score column.")

        target = features_df['cognitive_score']
        # Drop target from features
        X = features_df.drop(columns=['cognitive_score'])
        
        logger.info(f"Loaded {X.shape[0]} samples and {X.shape[1]} features.")
        log_memory_usage(logger, "After loading data")
        
        return X, target
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def prepare_features_target_optimized(X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and target as numpy arrays for efficient computation.
    Handles NaN imputation and scaling if necessary.
    """
    logger.info("Preparing features and target...")
    
    # Impute any remaining NaNs with median
    X = X.fillna(X.median())
    y = y.fillna(y.median())
    
    # Convert to numpy for speed
    X_np = X.values.astype(np.float32) # float32 saves memory vs float64
    y_np = y.values.astype(np.float32)
    
    logger.info(f"Prepared arrays: X {X_np.shape}, y {y_np.shape}")
    return X_np, y_np

def train_single_random_forest(X: np.ndarray, y: np.ndarray, 
                               n_estimators: int = 100, 
                               max_depth: Optional[int] = None,
                               random_state: int = 42) -> Tuple[float, RandomForestRegressor]:
    """
    Train a single Random Forest model.
    Returns R2 score and the model.
    """
    # Use 5-fold CV as per spec
    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    scores = cross_val_score(
        RandomForestRegressor(
            n_estimators=n_estimators, 
            max_depth=max_depth, 
            random_state=random_state,
            n_jobs=1 # Handled by outer parallelism if needed, but sklearn uses threads
        ),
        X, y, 
        cv=kf, 
        scoring='r2'
    )
    mean_r2 = scores.mean()
    
    # Train final model on full data for feature importance
    model = RandomForestRegressor(
        n_estimators=n_estimators, 
        max_depth=max_depth, 
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    
    return mean_r2, model

def run_permutation_test_optimized(X: np.ndarray, y: np.ndarray, 
                                   n_permutations: int = 1000, 
                                   random_state: int = 42) -> List[float]:
    """
    Run permutation test with optimizations:
    1. Vectorized shuffling where possible.
    2. Chunked processing to manage memory.
    3. Parallel execution of permutation batches.
    """
    logger.info(f"Starting optimized permutation test with {n_permutations} permutations...")
    
    # Define a worker function for parallel execution
    def worker_batch(indices: List[int]) -> List[float]:
        batch_scores = []
        for i in indices:
            # Shuffle y
            y_shuffled = optimized_shuffle(y, random_state=random_state + i)
            # Train and score
            r2, _ = train_single_random_forest(X, y_shuffled, random_state=random_state + i)
            batch_scores.append(r2)
            if i % 100 == 0:
                logger.debug(f"Processed {i}/{n_permutations}")
        return batch_scores

    # Split permutations into batches for parallel processing
    # Use fewer processes than cores to leave room for sklearn's internal threading
    n_processes = max(1, multiprocessing.cpu_count() - 2)
    batch_size = max(1, n_permutations // n_processes)
    batches = [list(range(i, min(i + batch_size, n_permutations))) 
               for i in range(0, n_permutations, batch_size)]
    
    all_scores = []
    
    # Execute in parallel
    with ProcessPoolExecutor(max_workers=n_processes) as executor:
        futures = [executor.submit(worker_batch, batch) for batch in batches]
        for future in as_completed(futures):
            try:
                batch_scores = future.result()
                all_scores.extend(batch_scores)
            except Exception as exc:
                logger.error(f"Permutation batch generated an exception: {exc}")
    
    # Fallback if parallelism fails (e.g., single thread)
    if len(all_scores) < n_permutations:
        logger.warning("Parallel permutation test incomplete. Running sequentially fallback.")
        for i in range(len(all_scores), n_permutations):
            y_shuffled = optimized_shuffle(y, random_state=random_state + i)
            r2, _ = train_single_random_forest(X, y_shuffled, random_state=random_state + i)
            all_scores.append(r2)
    
    logger.info(f"Completed {len(all_scores)} permutations.")
    return all_scores

def calculate_null_threshold_optimized(null_scores: List[float], 
                                       percentile: float = 95) -> float:
    """
    Calculate the high-percentile threshold from null distribution.
    """
    if not null_scores:
        raise ValueError("Null scores list is empty.")
    threshold = np.percentile(null_scores, percentile)
    logger.info(f"Null distribution threshold ({percentile}%): {threshold:.4f}")
    return threshold

def identify_top_taxa_optimized(model: RandomForestRegressor, 
                                feature_names: List[str],
                                top_k: int = 10) -> List[Tuple[str, float]]:
    """
    Identify top predictive taxa by mean decrease in impurity (feature_importances_).
    """
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    top_features = [(feature_names[i], importances[i]) for i in indices[:top_k]]
    logger.info(f"Top {top_k} taxa identified.")
    return top_features

def calculate_vif_optimized(X: np.ndarray, feature_names: List[str], 
                            threshold: float = 5.0) -> List[str]:
    """
    Calculate VIF for top taxa and filter out collinear ones.
    Optimized for numpy operations.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Add constant for intercept
    X_const = np.column_stack([np.ones(X.shape[0]), X])
    vif_data = []
    
    # Calculate VIF for each feature
    for i in range(X.shape[1]):
        vif = variance_inflation_factor(X_const, i + 1) # +1 because of constant
        vif_data.append((feature_names[i], vif))
    
    # Filter
    filtered_features = [name for name, vif in vif_data if vif <= threshold]
    logger.info(f"VIF filtering: {len(filtered_features)} features remaining (threshold <= {threshold}).")
    return filtered_features

def save_results_optimized(results: Dict[str, Any], path: Path):
    """
    Save results to JSON with optimized serialization.
    """
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {path}")

def run_modeling_pipeline_optimized():
    """
    Main pipeline execution function with performance optimizations.
    """
    logger.info("=== Starting Optimized Predictive Modeling Pipeline ===")
    monitor = MemoryMonitor()
    monitor.start()
    
    try:
        # 1. Load Data
        X_df, y = load_preprocessed_data_optimized()
        feature_names = list(X_df.columns)
        X_np, y_np = prepare_features_target_optimized(X_df, y)
        
        # 2. Train Model
        logger.info("Training Random Forest...")
        r2_score_model, model = train_single_random_forest(X_np, y_np)
        logger.info(f"Model R2 Score: {r2_score_model:.4f}")
        
        # 3. Permutation Test
        null_scores = run_permutation_test_optimized(X_np, y_np, n_permutations=1000)
        threshold = calculate_null_threshold_optimized(null_scores, percentile=95)
        
        # 4. Verify Significance
        is_significant = r2_score_model > threshold
        logger.info(f"Model Significance: {'PASS' if is_significant else 'FAIL'} (R2={r2_score_model:.4f} > {threshold:.4f})")
        
        # 5. Identify Top Taxa
        top_taxa = identify_top_taxa_optimized(model, feature_names, top_k=20)
        top_taxa_names = [t[0] for t in top_taxa]
        
        # 6. VIF Filter
        X_subset = X_np[:, [feature_names.index(t) for t in top_taxa_names]]
        filtered_taxa = calculate_vif_optimized(X_subset, top_taxa_names)
        
        # 7. Save Results
        results = {
            "r2_score": float(r2_score_model),
            "null_threshold": float(threshold),
            "is_significant": bool(is_significant),
            "top_taxa_initial": top_taxa,
            "top_taxa_final": filtered_taxa,
            "null_distribution_stats": {
                "mean": float(np.mean(null_scores)),
                "std": float(np.std(null_scores)),
                "min": float(np.min(null_scores)),
                "max": float(np.max(null_scores))
            }
        }
        
        save_results_optimized(results, OUTPUT_RESULTS_PATH)
        
        # Save specific artifacts
        with open(OUTPUT_THRESHOLD_PATH, 'w') as f:
            json.dump({"threshold": float(threshold), "percentile": 95}, f)
        
        with open(OUTPUT_TOP_TAXA_PATH, 'w') as f:
            json.dump([{"taxon": t[0], "importance": t[1]} for t in top_taxa], f, indent=2)
        
        with open(OUTPUT_TOP_TAXA_FINAL_PATH, 'w') as f:
            json.dump(filtered_taxa, f, indent=2)
        
        # Log memory usage
        log_memory_usage(logger, "Pipeline Complete")
        with open(OUTPUT_MEMORY_LOG_PATH, 'w') as f:
            f.write(monitor.get_log())
        
        logger.info("=== Optimized Pipeline Complete ===")
        return results

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        monitor.stop()
        gc_collect_if_needed()

def main():
    """Entry point for script execution."""
    check_cpu_only()
    run_modeling_pipeline_optimized()

if __name__ == "__main__":
    main()
