import os
import sys
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import KFold, nested_cv, cross_validate
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import pearsonr
import joblib

from utils import set_global_seed, setup_logging, assert_duration_limit
from config import ensure_directories

# Ensure logging is configured
setup_logging()
logger = logging.getLogger(__name__)

def calculate_observed_metric(
    X: np.ndarray,
    y: np.ndarray,
    seed: int = 42,
    k_outer: int = 5,
    k_inner: int = 5
) -> Tuple[float, float, float, np.ndarray]:
    """
    Calculates the observed Pearson correlation (r) using nested cross-validation.
    
    Implements Elastic Net (alpha=0.5) with nested k-fold CV.
    Returns: (mean_r, std_r, mae, best_coefs)
    """
    set_global_seed(seed)
    ensure_directories()
    
    n_samples, n_features = X.shape
    logger.info(f"Starting nested CV on {n_samples} samples, {n_features} features")

    outer_cv = KFold(n_splits=k_outer, shuffle=True, random_state=seed)
    inner_cv = KFold(n_splits=k_inner, shuffle=True, random_state=seed)

    r_scores = []
    mae_scores = []
    coefs_list = []

    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Inner loop: Hyperparameter tuning (fixed alpha=0.5 per spec, but tune lambda via CV)
        # We use a simple grid for lambda (1/C) since alpha is fixed at 0.5
        # ElasticNet in sklearn uses alpha as the constant multiplying the l1 and l2 norms.
        # To tune the regularization strength, we vary the 'alpha' parameter.
        # Spec says "Elastic Net (α=0.5)" which usually refers to the mix ratio.
        # We will tune the 'alpha' (strength) parameter while keeping 'l1_ratio' fixed at 0.5.
        
        best_score = -np.inf
        best_alpha = 0.1
        
        # Simple grid search for alpha (regularization strength)
        alphas = [0.1, 0.01, 0.001, 0.0001]
        
        for a in alphas:
            inner_scores = []
            for inner_train_idx, inner_test_idx in inner_cv.split(X_train):
                x_it, x_val = X_train[inner_train_idx], X_train[inner_test_idx]
                y_it, y_val = y_train[inner_train_idx], y_train[inner_test_idx]
                
                model = ElasticNet(alpha=a, l1_ratio=0.5, max_iter=10000, random_state=seed)
                model.fit(x_it, y_it)
                pred = model.predict(x_val)
                score = pearsonr(y_val, pred)[0]
                inner_scores.append(score)
            
            avg_inner = np.mean(inner_scores)
            if avg_inner > best_score:
                best_score = avg_inner
                best_alpha = a

        # Train final model on outer train set with best alpha
        final_model = ElasticNet(alpha=best_alpha, l1_ratio=0.5, max_iter=10000, random_state=seed)
        final_model.fit(X_train, y_train)
        
        # Evaluate on outer test set
        y_pred = final_model.predict(X_test)
        r_val = pearsonr(y_test, y_pred)[0]
        mae_val = mean_absolute_error(y_test, y_pred)
        
        r_scores.append(r_val)
        mae_scores.append(mae_val)
        coefs_list.append(final_model.coef_)

    mean_r = np.mean(r_scores)
    std_r = np.std(r_scores)
    mean_mae = np.mean(mae_scores)
    
    # Aggregate coefficients (average across folds)
    best_coefs = np.mean(coefs_list, axis=0)

    logger.info(f"Nested CV Result: r={mean_r:.4f} (std={std_r:.4f}), MAE={mean_mae:.4f}")
    return mean_r, std_r, mean_mae, best_coefs

def run_global_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42,
    k_outer: int = 5,
    k_inner: int = 5
) -> Tuple[np.ndarray, float]:
    """
    Performs a global permutation test.
    Shuffles labels globally for each iteration, then runs the full nested CV loop.
    Returns: (null_distribution, empirical_p_value)
    """
    set_global_seed(seed)
    logger.info(f"Running global permutation test with {n_permutations} iterations")
    
    observed_r, _, _, _ = calculate_observed_metric(X, y, seed=seed, k_outer=k_outer, k_inner=k_inner)
    
    null_distribution = []
    
    for i in range(n_permutations):
        # Shuffle y globally
        y_shuffled = y.copy()
        np.random.shuffle(y_shuffled)
        
        # Run nested CV on shuffled data
        perm_r, _, _, _ = calculate_observed_metric(
            X, y_shuffled, seed=seed + i + 1, 
            k_outer=k_outer, k_inner=k_inner
        )
        null_distribution.append(perm_r)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations} completed. Current r: {perm_r:.4f}")

    null_array = np.array(null_distribution)
    
    # Calculate empirical p-value
    # p = (count(perm_r >= observed_r) + 1) / (n_permutations + 1)
    # For two-tailed or one-tailed? Typically we test if observed is significantly better than null.
    # Since we expect positive correlation, we use one-tailed: P(Null >= Observed)
    p_value = (np.sum(null_array >= observed_r) + 1) / (n_permutations + 1)
    
    logger.info(f"Global Permutation Test: Observed r={observed_r:.4f}, Null mean={np.mean(null_array):.4f}, p={p_value:.4f}")
    return null_array, p_value

def run_bootstrap_ci(
    X: np.ndarray,
    y: np.ndarray,
    n_bootstraps: int = 1000,
    seed: int = 42,
    k_outer: int = 5,
    k_inner: int = 5,
    percentile: float = 0.95
) -> Tuple[float, float]:
    """
    Calculates bootstrap confidence interval for Pearson r.
    Returns: (lower_ci, upper_ci)
    """
    set_global_seed(seed)
    logger.info(f"Running bootstrap CI with {n_bootstraps} iterations")
    
    bootstrapped_r = []
    n_samples = X.shape[0]
    
    for i in range(n_bootstraps):
        # Sample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_boot = X[indices]
        y_boot = y[indices]
        
        r_val, _, _, _ = calculate_observed_metric(
            X_boot, y_boot, seed=seed + i,
            k_outer=k_outer, k_inner=k_inner
        )
        bootstrapped_r.append(r_val)
    
    bootstrapped_r = np.array(bootstrapped_r)
    
    lower_idx = int((1 - percentile) / 2 * 100)
    upper_idx = int((1 + percentile) / 2 * 100)
    
    lower_ci = np.percentile(bootstrapped_r, lower_idx)
    upper_ci = np.percentile(bootstrapped_r, upper_idx)
    
    logger.info(f"Bootstrap CI ({percentile*100}%): [{lower_ci:.4f}, {upper_ci:.4f}]")
    return lower_ci, upper_ci

def run_modeling_pipeline(
    feature_matrix_path: str,
    target_column: str,
    output_dir: str = "artifacts",
    n_permutations: int = 1000,
    n_bootstraps: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Orchestrates the full modeling pipeline: Nested CV, Permutation Test, Bootstrap CI.
    Saves results to JSON.
    """
    set_global_seed(seed)
    ensure_directories()
    
    logger.info(f"Loading data from {feature_matrix_path}")
    df = pd.read_csv(feature_matrix_path)
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in {feature_matrix_path}")
    
    X = df.drop(columns=[target_column]).values
    y = df[target_column].values
    
    logger.info(f"Data shape: {X.shape}, Target shape: {y.shape}")
    
    # 1. Observed Metric
    observed_r, obs_std, obs_mae, best_coefs = calculate_observed_metric(X, y, seed=seed)
    
    # 2. Global Permutation Test
    null_dist, p_value = run_global_permutation_test(X, y, n_permutations=n_permutations, seed=seed)
    
    # 3. Bootstrap CI
    lower_ci, upper_ci = run_bootstrap_ci(X, y, n_bootstraps=n_bootstraps, seed=seed)
    
    # 4. Compile Results
    results = {
        "observed_pearson_r": float(observed_r),
        "observed_std": float(obs_std),
        "observed_mae": float(obs_mae),
        "p_value_global_permutation": float(p_value),
        "bootstrap_ci_95": [float(lower_ci), float(upper_ci)],
        "n_permutations": n_permutations,
        "n_bootstraps": n_bootstraps,
        "seed": seed,
        "feature_importance_coefs": best_coefs.tolist()
    }
    
    output_path = Path(output_dir) / "model_result.json"
    joblib.dump(results, str(output_path))
    logger.info(f"Model results saved to {output_path}")
    
    return results

def main():
    # Example execution entry point
    # In production, arguments would be passed via CLI or config
    try:
        import pandas as pd
        run_modeling_pipeline(
            feature_matrix_path="data/processed/feature_matrix.csv",
            target_column="heat_pain_threshold",
            output_dir="artifacts"
        )
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
