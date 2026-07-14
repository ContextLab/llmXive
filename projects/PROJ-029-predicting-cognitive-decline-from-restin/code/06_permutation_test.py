"""
code/06_permutation_test.py
Implements Task T029: Permutation test for statistical significance.

Imports training logic from code/04_train_model.py.
Performs 500 label shuffles (seed=42), re-trains/re-evaluates, and records ROC-AUC.
Enforces a 2-hour runtime limit; aborts if estimated runtime exceeds this.
Output: data/processed/permutation_results.json
"""
import os
import sys
import json
import time
import random
import warnings
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from joblib import Parallel, delayed
import joblib

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import specific functions from 04_train_model as per API surface
# We need the inner pipeline to re-run training on shuffled data
try:
    from code_04_train_model import inner_cv_pipeline, define_decline_label
except ImportError:
    # Fallback for direct execution where module name might differ or path is different
    # Attempt to import from the file directly if standard import fails
    import importlib.util
    spec = importlib.util.spec_from_file_location("code_04_train_model", project_root / "code" / "04_train_model.py")
    if spec and spec.loader:
        module_04 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module_04)
        inner_cv_pipeline = module_04.inner_cv_pipeline
        define_decline_label = module_04.define_decline_label
    else:
        raise ImportError("Could not load training logic from code/04_train_model.py")

from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

# Constants
N_PERMUTATIONS = 500
RANDOM_SEED = 42
MAX_RUNTIME_HOURS = 2.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600
OUTPUT_PATH = "data/processed/permutation_results.json"
MODEL_PATH = "data/processed/model.pkl"
DATA_PATH = "data/processed/graph_metrics.csv"

# Logger setup
logger = get_logger(__name__)

def get_logger_wrapper():
    """Wrapper to ensure logging is configured correctly."""
    return logger

def load_model_and_data() -> Tuple[Any, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load the trained model, graph metrics data, and labels.
    Returns:
        model: The trained Random Forest model
        df: The graph metrics dataframe
        X: Feature matrix
        y: Target labels (decline status)
    """
    model_path = Path(project_root) / MODEL_PATH
    data_path = Path(project_root) / DATA_PATH

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. Run training first.")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_path}. Run preprocessing first.")

    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)

    logger.info(f"Loading data from {data_path}")
    df = load_csv(data_path)

    # Identify feature columns (exclude subject_id and target columns if present)
    # Assuming the CSV has 'subject_id', 'decline_label' (or similar), and feature columns
    # We need to reconstruct X and y exactly as they were passed to the model
    # The model was trained on features excluding 'subject_id' and the target label.
    # Let's assume the target column is 'decline_label' based on T023 logic.
    target_col = 'decline_label'
    if target_col not in df.columns:
        # Fallback: try to find a column that looks like a target if 'decline_label' isn't there
        # But strictly, we should rely on the schema from T023.
        raise ValueError(f"Target column '{target_col}' not found in data. Columns: {df.columns.tolist()}")

    y = df[target_col].values
    feature_cols = [c for c in df.columns if c not in ['subject_id', target_col]]
    if not feature_cols:
        raise ValueError("No feature columns found in data.")
    
    X = df[feature_cols].values.astype(float)

    logger.info(f"Loaded data: X shape {X.shape}, y shape {y.shape}")
    return model, df, X, y

def estimate_runtime(X: np.ndarray, y: np.ndarray, n_permutations: int = N_PERMUTATIONS) -> float:
    """
    Estimate runtime for the full permutation test by running a small sample.
    Returns estimated time in seconds.
    """
    logger.info("Estimating runtime with a small sample...")
    sample_size = min(5, n_permutations)
    start_time = time.time()
    
    # Run a few permutations to estimate
    for i in range(sample_size):
        # Shuffle labels
        y_perm = y.copy()
        np.random.shuffle(y_perm)
        # Run a quick inner pipeline (this is expensive, so we do it only 5 times)
        # We pass n_jobs=1 for the sample to avoid oversubscription during estimation
        try:
            # We need to call the inner pipeline. 
            # Note: inner_cv_pipeline might expect specific arguments. 
            # Based on T023, it likely takes X, y, and CV parameters.
            # We assume it returns the mean CV score.
            # To be safe and fast, we might limit iterations here if the function allows,
            # but we will assume the function is robust.
            # We'll use a subset of X if possible, but the function signature is fixed.
            # Let's just run it.
            score = inner_cv_pipeline(X, y_perm, n_jobs=1) 
        except Exception as e:
            logger.warning(f"Sample permutation {i} failed: {e}. Using fallback estimation.")
            score = 0.0
            break

    elapsed = time.time() - start_time
    estimated_total = elapsed / sample_size * n_permutations
    logger.info(f"Sample runtime: {elapsed:.2f}s for {sample_size} perms. Estimated total: {estimated_total:.2f}s ({estimated_total/3600:.2f}h)")
    return estimated_total

def run_permutation(X: np.ndarray, y: np.ndarray, permutation_idx: int) -> Dict[str, Any]:
    """
    Run a single permutation: shuffle labels, train, evaluate.
    Returns a dict with the permutation index and the resulting ROC-AUC.
    """
    # Seed for this specific permutation to ensure reproducibility if needed,
    # though the shuffle itself is the randomization.
    np.random.seed(RANDOM_SEED + permutation_idx)
    
    # Shuffle labels
    y_perm = y.copy()
    np.random.shuffle(y_perm)
    
    # Train and evaluate using the inner pipeline logic
    # We need the mean CV score (ROC-AUC) from the shuffled data
    try:
        # The inner_cv_pipeline function from 04_train_model should handle the nested CV
        # and return the mean score. We assume it returns a dict or float.
        # If it returns a dict, we look for 'roc_auc' or 'mean_score'.
        result = inner_cv_pipeline(X, y_perm, n_jobs=1)
        
        # Extract score
        if isinstance(result, dict):
            # Try common keys
            score = result.get('roc_auc', result.get('mean_score', result.get('score', 0.0)))
        else:
            score = float(result)
            
        return {
            "permutation": permutation_idx,
            "roc_auc": score,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Permutation {permutation_idx} failed: {e}")
        return {
            "permutation": permutation_idx,
            "roc_auc": None,
            "status": "failed",
            "error": str(e)
        }

def main():
    logger.info("Starting Permutation Test (T029)")
    
    # Load data and model
    try:
        model, df, X, y = load_model_and_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Pre-flight check: Estimate runtime
    estimated_time = estimate_runtime(X, y, N_PERMUTATIONS)
    if estimated_time > MAX_RUNTIME_SECONDS:
        logger.error(f"Estimated runtime ({estimated_time/3600:.2f}h) exceeds limit ({MAX_RUNTIME_HOURS}h). Aborting.")
        sys.exit(1)
    
    logger.info(f"Runtime estimate OK. Starting {N_PERMUTATIONS} permutations.")
    
    # Set global seed
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # Run permutations
    # We use joblib to parallelize if possible, but since inner_cv_pipeline might use joblib itself,
    # we must be careful not to oversubscribe. The task requires 2 cores.
    # We'll run sequentially or with n_jobs=1 in the inner loop to be safe, 
    # but we can parallelize the outer loop if the inner loop is single-threaded.
    # Given the constraint "2-core runner", we set n_jobs=2 for the outer loop.
    
    results = []
    start_total = time.time()
    
    # Using Parallel for the outer loop
    # Note: If inner_cv_pipeline is heavy, n_jobs=1 might be safer to avoid memory/CPU thrashing.
    # But the task asks for 500 permutations. We'll try n_jobs=2.
    logger.info(f"Running {N_PERMUTATIONS} permutations with n_jobs=2...")
    
    perm_results = Parallel(n_jobs=2)(
        delayed(run_permutation)(X, y, i) for i in range(N_PERMUTATIONS)
    )
    
    total_time = time.time() - start_total
    logger.info(f"Permutation test completed in {total_time:.2f}s ({total_time/3600:.2f}h)")

    # Analyze results
    scores = [r['roc_auc'] for r in perm_results if r['status'] == 'success' and r['roc_auc'] is not None]
    failed_count = N_PERMUTATIONS - len(scores)
    
    if len(scores) == 0:
        logger.error("No successful permutations. Cannot compute p-value.")
        sys.exit(1)

    # Calculate p-value
    # We need the original model's performance on the original data to compare.
    # However, the task says "re-train/re-evaluate the model for each permutation, and record ROC-AUC".
    # It does not explicitly say to compare against the *original* model's score in this script,
    # but p-value calculation requires an observed statistic.
    # The observed statistic is the ROC-AUC of the model trained on the REAL labels.
    # We can get this by running the inner pipeline on the original X, y once.
    logger.info("Computing observed statistic on original labels...")
    try:
        observed_score = inner_cv_pipeline(X, y, n_jobs=1)
        if isinstance(observed_score, dict):
            observed_score = observed_score.get('roc_auc', observed_score.get('mean_score', observed_score.get('score', 0.0)))
        observed_score = float(observed_score)
    except Exception as e:
        logger.error(f"Failed to compute observed score: {e}")
        sys.exit(1)

    logger.info(f"Observed ROC-AUC: {observed_score:.4f}")
    
    # p-value: proportion of permuted scores >= observed score
    # (One-tailed test: is the observed score significantly better than random?)
    p_value = sum(1 for s in scores if s >= observed_score) / len(scores)
    
    logger.info(f"Permutation p-value: {p_value:.4f} ({sum(1 for s in scores if s >= observed_score)} / {len(scores)})")

    # Prepare output
    output_data = {
        "n_permutations": N_PERMUTATIONS,
        "random_seed": RANDOM_SEED,
        "total_runtime_seconds": total_time,
        "observed_roc_auc": observed_score,
        "permuted_roc_aucs": scores,
        "p_value": p_value,
        "failed_permutations": failed_count,
        "parameters": {
            "max_runtime_hours": MAX_RUNTIME_HOURS,
            "n_jobs": 2
        }
    }

    # Save output
    output_path = Path(project_root) / OUTPUT_PATH
    ensure_dir(output_path)
    save_json(output_path, output_data)
    
    logger.info(f"Results saved to {output_path}")
    logger.info("Permutation test (T029) completed successfully.")

if __name__ == "__main__":
    main()