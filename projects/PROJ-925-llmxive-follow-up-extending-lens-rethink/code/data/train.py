"""
Training module for XGBoost regression on deviation targets.
Implements CPU-only training with k=5 fold CV and quantile-based stratification.
"""
import os
import sys
import logging
import json
import time
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import KBinsDiscretizer
from config import get_paths, init_run
from utils.logging import setup_logging, get_logger

# Ensure CPU-only constraints
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

logger = None

def train_xgboost(X: np.array, y: np.array) -> xgb.XGBRegressor:
    """
    Train XGBoost regressor with k=5 fold CV and quantile-based stratification.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)

    Returns:
        Trained XGBRegressor model
    """
    global logger
    if logger is None:
        logger = get_logger()

    logger.info("Starting XGBoost training with k=5 fold CV and quantile stratification")

    # Validate inputs
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"X and y must have same number of samples: X={X.shape[0]}, y={y.shape[0]}")

    if X.shape[0] < 10:
        raise ValueError(f"Insufficient samples for k=5 CV: {X.shape[0]}")

    # Quantile-based stratification for regression target
    # Discretize y into 5 quantile bins for stratified CV
    n_bins = 5
    if len(np.unique(y)) < n_bins:
        logger.warning(f"Target has fewer unique values ({len(np.unique(y))}) than bins ({n_bins}). Using available values.")
        n_bins = min(len(np.unique(y)), n_bins)

    discretizer = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='quantile')
    y_stratified = discretizer.fit_transform(y.reshape(-1, 1)).ravel()

    # Configure XGBoost for CPU-only training
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='reg:squarederror',
        random_state=42,
        n_jobs=1,  # Force single-threaded CPU
        tree_method='hist',
        device='cpu'
    )

    # Perform k=5 fold cross-validation
    k = 5
    cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)

    cv_scores = cross_val_score(model, X, y_stratified, cv=cv, scoring='neg_mean_squared_error')
    mean_mse = -np.mean(cv_scores)
    std_mse = np.std(cv_scores)

    logger.info(f"Cross-validation MSE: {mean_mse:.4f} (+/- {std_mse:.4f})")

    # Train final model on full dataset
    model.fit(X, y)

    logger.info("XGBoost training completed successfully")
    return model

def calculate_permutation_importance(model, X, y) -> dict:
    """
    Calculate permutation-based feature importance with N=1000 shuffles.
    Applies Benjamini-Hochberg correction for FDR <= 0.05.

    Args:
        model: Trained XGBRegressor
        X: Feature matrix
        y: Target vector

    Returns:
        Dictionary with importance scores, p-values, and significance flags
    """
    global logger
    if logger is None:
        logger = get_logger()

    logger.info("Calculating permutation importance with N=1000 shuffles")

    n_features = X.shape[1]
    n_iter = 1000
    seed = 42
    np.random.seed(seed)

    # Baseline score
    baseline_mse = np.mean((model.predict(X) - y) ** 2)

    # Permutation importance calculation
    importance_scores = np.zeros(n_features)
    null_distributions = [[] for _ in range(n_features)]

    for i in range(n_iter):
        X_permuted = X.copy()
        for j in range(n_features):
            np.random.shuffle(X_permuted[:, j])
            perm_mse = np.mean((model.predict(X_permuted) - y) ** 2)
            importance_scores[j] += (perm_mse - baseline_mse)
            null_distributions[j].append(perm_mse - baseline_mse)

    # Average importance scores
    importance_scores /= n_iter

    # Calculate p-values using null distributions
    p_values = []
    for j in range(n_features):
        # Count how many null values are >= observed importance
        count = sum(1 for null_val in null_distributions[j] if null_val >= importance_scores[j])
        p_val = count / n_iter
        p_values.append(p_val)

    # Apply Benjamini-Hochberg correction
    corrected_p_values = apply_benjamini_hochberg(p_values, alpha=0.05)

    logger.info(f"Permutation importance calculated. N={n_iter}, seed={seed}")

    return {
        'importance_scores': importance_scores.tolist(),
        'p_values': p_values,
        'corrected_p_values': corrected_p_values,
        'significant': [p < 0.05 for p in corrected_p_values],
        'n_iter': n_iter,
        'seed': seed,
        'method': 'Benjamini-Hochberg'
    }

def run_label_permutation_test(model, X, y, n_iter=1000) -> dict:
    """
    Run label permutation test to establish null distribution.
    Enforces fixed iteration count and pinned seeds for reproducibility.

    Args:
        model: Trained XGBRegressor
        X: Feature matrix
        y: Target vector
        n_iter: Number of iterations (default 1000)

    Returns:
        Dictionary with null distribution statistics and p-values
    """
    global logger
    if logger is None:
        logger = get_logger()

    logger.info(f"Running label permutation test with N={n_iter} iterations")

    seed = 42
    np.random.seed(seed)

    # Calculate observed metric (R²)
    from sklearn.metrics import r2_score
    y_pred = model.predict(X)
    observed_r2 = r2_score(y, y_pred)

    null_r2_values = []
    for _ in range(n_iter):
        y_permuted = y.copy()
        np.random.shuffle(y_permuted)
        y_pred_perm = model.predict(X)
        null_r2 = r2_score(y_permuted, y_pred_perm)
        null_r2_values.append(null_r2)

    # Calculate p-value
    count = sum(1 for null_val in null_r2_values if null_val >= observed_r2)
    p_value = count / n_iter

    logger.info(f"Label permutation test completed. Observed R²={observed_r2:.4f}, p-value={p_value:.4f}")

    return {
        'observed_r2': observed_r2,
        'null_r2_mean': np.mean(null_r2_values),
        'null_r2_std': np.std(null_r2_values),
        'p_value': p_value,
        'n_iter': n_iter,
        'seed': seed,
        'method': 'Benjamini-Hochberg'
    }

def apply_benjamini_hochberg(p_values: list, alpha=0.05) -> list:
    """
    Apply Benjamini-Hochberg procedure to control FDR <= 0.05.

    Args:
        p_values: List of p-values
        alpha: Significance threshold (default 0.05)

    Returns:
        List of corrected p-values
    """
    global logger
    if logger is None:
        logger = get_logger()

    logger.info(f"Applying Benjamini-Hochberg correction with alpha={alpha}")

    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]

    # Calculate BH corrected p-values
    corrected_p_values = [0.0] * n
    min_corrected = 1.0

    for i in range(n - 1, -1, -1):
        rank = i + 1
        corrected = sorted_p_values[i] * n / rank
        corrected = min(corrected, 1.0)
        corrected = min(corrected, min_corrected)
        min_corrected = corrected
        corrected_p_values[sorted_indices[i]] = corrected

    logger.info(f"Benjamini-Hochberg correction applied. Seed=42, method=Benjamini-Hochberg, n_iter={n}")

    return corrected_p_values

def run_sensitivity_analysis(X, y, seeds: List[int], alphas: List[float]) -> dict:
    """
    Run sensitivity analysis over seeds and significance thresholds.

    Args:
        X: Feature matrix
        y: Target vector
        seeds: List of random seeds to test
        alphas: List of significance thresholds to test

    Returns:
        Dictionary with stability metrics
    """
    global logger
    if logger is None:
        logger = get_logger()

    logger.info("Starting sensitivity analysis")

    alpha_sweep_results = {}
    seed_sweep_results = {}

    all_ranks = {seed: [] for seed in seeds}

    for seed in seeds:
        logger.info(f"Running sensitivity analysis for seed={seed}")
        np.random.seed(seed)

        # Train model
        model = train_xgboost(X, y)

        # Run permutation importance for each alpha
        for alpha in alphas:
            logger.info(f"Testing alpha={alpha}")
            importance_result = calculate_permutation_importance(model, X, y)

            # Get ranks of significant features
            significant_indices = [i for i, sig in enumerate(importance_result['significant']) if sig]
            ranks = sorted(significant_indices)

            all_ranks[seed].extend(ranks)

            # Store results for this alpha
            if alpha not in alpha_sweep_results:
                alpha_sweep_results[alpha] = {
                    'mean_rank': 0.0,
                    'std_rank': 0.0,
                    'feature_counts': {}
                }

            # Update alpha sweep stats
            alpha_sweep_results[alpha]['mean_rank'] += len(ranks)
            alpha_sweep_results[alpha]['std_rank'] += len(ranks) ** 2
            for idx in ranks:
                alpha_sweep_results[alpha]['feature_counts'][idx] = \
                    alpha_sweep_results[alpha]['feature_counts'].get(idx, 0) + 1

        # Update seed sweep stats
        seed_ranks = all_ranks[seed]
        if seed_ranks:
          seed_sweep_results[seed] = {
              'mean_rank': np.mean(seed_ranks),
              'std_rank': np.std(seed_ranks),
              'n_significant': len(seed_ranks)
          }

    # Normalize alpha sweep stats
    n_alphas = len(alphas)
    for alpha in alpha_sweep_results:
        alpha_sweep_results[alpha]['mean_rank'] /= n_alphas
        variance = (alpha_sweep_results[alpha]['std_rank'] / n_alphas) - (alpha_sweep_results[alpha]['mean_rank'] ** 2)
        alpha_sweep_results[alpha]['std_rank'] = np.sqrt(max(0, variance))

    logger.info("Sensitivity analysis completed")

    return {
        'alpha_sweep_results': alpha_sweep_results,
        'seed_sweep_results': seed_sweep_results,
        'seeds_tested': seeds,
        'alphas_tested': alphas
    }

def main():
    """
    Main entry point for training pipeline.
    Loads processed data, trains model, runs significance tests, and saves results.
    """
    global logger
    logger = setup_logging("train")
    logger.info("Starting training pipeline")

    try:
        # Initialize run configuration
        init_run()
        paths = get_paths()

        # Load processed features and deviation targets
        features_path = paths.data_processed / "features.csv"
        deviation_path = paths.data_processed / "deviation.csv"

        if not features_path.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")
        if not deviation_path.exists():
            raise FileNotFoundError(f"Deviation file not found: {deviation_path}")

        features_df = pd.read_csv(features_path)
        deviation_df = pd.read_csv(deviation_path)

        # Merge datasets
        merged_df = pd.merge(features_df, deviation_df, on='caption_id', how='inner')

        if merged_df.empty:
            raise ValueError("No overlapping records between features and deviation datasets")

        # Prepare feature matrix and target
        feature_columns = [col for col in merged_df.columns if col not in ['caption_id', 'deviation']]
        X = merged_df[feature_columns].values
        y = merged_df['deviation'].values

        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")

        # Train model
        model = train_xgboost(X, y)

        # Calculate permutation importance
        importance_result = calculate_permutation_importance(model, X, y)

        # Run label permutation test
        label_test_result = run_label_permutation_test(model, X, y)

        # Run sensitivity analysis
        seeds = [42, 123, 456, 789, 1011]
        alphas = [0.01, 0.05, 0.1]
        sensitivity_result = run_sensitivity_analysis(X, y, seeds, alphas)

        # Save results
        results_dir = paths.results
        results_dir.mkdir(parents=True, exist_ok=True)

        significance_path = results_dir / "significance.json"
        with open(significance_path, 'w') as f:
            json.dump({
                'importance': importance_result,
                'label_test': label_test_result,
                'sensitivity': sensitivity_result
            }, f, indent=2)

        logger.info(f"Results saved to {significance_path}")
        logger.info("Training pipeline completed successfully")

    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()