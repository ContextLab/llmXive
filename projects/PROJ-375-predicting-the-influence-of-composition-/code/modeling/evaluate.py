import os
import sys
import json
import logging
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.inspection import permutation_importance

# Import from project utils
from utils.io import setup_logging, compute_sha256
from utils.config import get_env_var
from modeling.train import load_metrics, save_metrics

# Ensure logging is configured
logger = setup_logging()

def load_test_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the test set features (X) and target (y) from the processed data.
    Assumes data was saved by T022 to data/processed/clean_mg_data.parquet.
    """
    import pandas as pd
    data_path = Path("data/processed/clean_mg_data.parquet")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found at {data_path}. Run T022 first.")
    
    df = pd.read_parquet(data_path)
    
    # Determine feature columns (exclude target and metadata)
    target_col = "cte"
    exclude_cols = {target_col, "composition", "alloy_family", "source", "amorphous_state_flag"}
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in dataset.")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return X, y

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R2, MAE, RMSE."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {"r2": float(r2), "mae": float(mae), "rmse": float(rmse)}

def run_permutation_test(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    scoring: str = "r2",
    n_jobs: int = 2
) -> Dict[str, Any]:
    """
    Run permutation test to evaluate model significance.
    Returns p-value and permutation scores.
    """
    logger.info(f"Running permutation test with {n_permutations} iterations...")
    start_time = time.time()
    
    # Get original score
    y_pred_orig = model.predict(X)
    original_score = r2_score(y, y_pred_orig)
    
    # Run permutation
    perm_result = permutation_importance(
        model, X, y,
        n_permutations=n_permutations,
        scoring=scoring,
        n_jobs=n_jobs,
        random_state=42
    )
    
    # Calculate p-value: proportion of permuted scores >= original score
    # permutation_importance returns scores for each permutation (negative R2 usually)
    # We need to check how many permuted models performed as well as the original
    # Since permutation_importance returns (original_score - permuted_score), 
    # a positive value means original was better.
    # We want p-value = P(perm_score >= orig_score)
    # If perm_importance > 0, then orig > perm.
    # We want count where perm_score >= orig_score -> perm_importance <= 0
    
    perm_scores = perm_result.importances_mean
    # The permutation_importance function computes: original_score - permuted_score
    # So if permuted_score >= original_score, then importances <= 0
    # We count how many times the permuted model was as good or better than original
    better_or_equal_count = np.sum(perm_scores <= 0)
    p_value = better_or_equal_count / n_permutations
    
    elapsed = time.time() - start_time
    logger.info(f"Permutation test completed in {elapsed:.2f}s. P-value: {p_value:.4f}")
    
    return {
        "p_value": float(p_value),
        "original_score": float(original_score),
        "n_permutations": n_permutations,
        "execution_time": elapsed,
        "status": "completed"
    }

def evaluate_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Main evaluation function: calculates metrics and runs permutation test.
    """
    y_pred = model.predict(X)
    metrics = calculate_metrics(y, y_pred)
    
    # Run permutation test
    perm_result = run_permutation_test(model, X, y, n_permutations=n_permutations)
    
    # Determine significance
    is_significant = perm_result["p_value"] < 0.05
    null_result_flag = not is_significant or metrics["r2"] <= 0.3
    
    evaluation_results = {
        "metrics": metrics,
        "permutation_test": perm_result,
        "significance": {
            "is_significant": is_significant,
            "null_result_flag": null_result_flag,
            "reason": "Performance does not exceed random chance (p > 0.05 or R2 <= 0.3)" if null_result_flag else "Model performance is statistically significant"
        }
    }
    
    return evaluation_results

def main():
    """
    Entry point for the evaluation script.
    Handles N < 20 case as per T035a.
    """
    logger.info("Starting evaluation pipeline...")
    
    # Load test data
    try:
        X, y = load_test_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    N = len(y)
    logger.info(f"Loaded {N} samples for evaluation.")
    
    # Check N < 20 condition (T035a)
    if N < 20:
        logger.warning("N < 20: Permutation test skipped.")
        
        # Load existing metrics from training (T032) if available
        metrics_path = Path("results/metrics.json")
        current_metrics = {}
        if metrics_path.exists():
            with open(metrics_path, "r") as f:
                current_metrics = json.load(f)
        
        # Update metrics with permutation status
        current_metrics["permutation_status"] = "skipped_low_n"
        current_metrics["permutation_reason"] = "Dataset size N < 20 is insufficient for permutation testing (FR-005 requirement)."
        
        # Save updated metrics
        save_metrics(current_metrics)
        
        logger.info(f"Updated results/metrics.json with permutation_status: skipped_low_n")
        return 0
    
    # Load the trained model (from T031)
    model_path = Path("models/latest_model.pkl")
    if not model_path.exists():
        logger.error("Trained model not found. Run T031 first.")
        return 1
    
    import pickle
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    # Run evaluation
    results = evaluate_model(model, X, y, n_permutations=1000)
    
    # Load existing metrics and update
    metrics_path = Path("results/metrics.json")
    current_metrics = {}
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            current_metrics = json.load(f)
    
    # Update with evaluation results
    current_metrics["evaluation"] = results
    current_metrics["permutation_status"] = "completed"
    current_metrics["sc003_match_status"] = "pending_divergence_analysis" # To be updated by T039
    
    if results["significance"]["null_result_flag"]:
        current_metrics["sc003_match_status"] = "insufficient_data_for_significance"
    
    save_metrics(current_metrics)
    
    logger.info(f"Evaluation complete. R2: {results['metrics']['r2']:.4f}, P-value: {results['permutation_test']['p_value']:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())