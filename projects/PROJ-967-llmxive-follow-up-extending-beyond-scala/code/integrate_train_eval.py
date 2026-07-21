"""
Integrate training and evaluation for US3.

Reads features from data/processed/features.json, trains a Random Forest model,
runs 5-fold cross-validation, performs a permutation test, and writes final metrics
to results/results.json.

Dependencies:
  - T027a: Random Forest training setup (load_features, prepare_data)
  - T028: 5-fold cross-validation logic
  - T030a: Permutation test logic
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path

import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.utils import shuffle

# Import from existing sibling modules
from train import load_features, prepare_data, save_results as train_save_results
from evaluate import calculate_baseline_mae, perform_permutation_test, save_results as eval_save_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/integration.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

def train_model(X_train, y_train, n_estimators=100, max_depth=None, random_state=42, n_jobs=2):
    """Train a Random Forest regressor."""
    logger.info(f"Training Random Forest with n_estimators={n_estimators}, max_depth={max_depth}")
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=n_jobs
    )
    model.fit(X_train, y_train)
    return model

def run_cross_validation(model, X, y, n_splits=5, random_state=42):
    """Run k-fold cross-validation and return mean R² and std dev."""
    logger.info(f"Running {n_splits}-fold cross-validation")
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    scores = cross_val_score(model, X, y, cv=kf, scoring='r2', n_jobs=2)
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores)
    logger.info(f"CV R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
    return mean_r2, std_r2

def run_full_pipeline(
    features_path="data/processed/features.json",
    results_path="results/results.json",
    model_path="results/model.pkl",
    n_estimators=100,
    max_depth=None,
    random_state=42,
    n_splits=5,
    n_permutations=1000,
    test_size=0.2,
    alpha=0.05
):
    """
    End-to-end pipeline: load features, train model, run CV, run permutation test, save results.
    """
    logger.info(f"Loading features from {features_path}")
    features = load_features(features_path)
    
    if not features:
        raise ValueError("No features loaded. Check if features.json is empty or missing.")
    
    logger.info(f"Loaded {len(features)} samples")
    
    # Prepare data
    X, y, feature_names = prepare_data(features)
    logger.info(f"Prepared data: X shape={X.shape}, y shape={y.shape}")
    
    if len(X) == 0:
        raise ValueError("No valid samples after data preparation.")
    
    # Train model
    model = train_model(X, y, n_estimators=n_estimators, max_depth=max_depth, random_state=random_state)
    
    # Save model
    logger.info(f"Saving model to {model_path}")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    
    # Cross-validation
    cv_r2_mean, cv_r2_std = run_cross_validation(model, X, y, n_splits=n_splits, random_state=random_state)
    
    # Evaluate on test set (train/test split)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    model_test = train_model(X_train, y_train, n_estimators=n_estimators, max_depth=max_depth, random_state=random_state)
    y_pred = model_test.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    logger.info(f"Test MAE: {mae:.4f}, Test R²: {r2:.4f}")
    
    # Permutation test
    logger.info("Running permutation test")
    baseline_mae = calculate_baseline_mae(y_test)
    p_value = perform_permutation_test(
        model_test, X_test, y_test, n_permutations=n_permutations, alpha=alpha, random_state=random_state
    )
    
    logger.info(f"Baseline MAE: {baseline_mae:.4f}, Permutation p-value: {p_value:.4f}")
    
    # Compile results
    results = {
        "cv_r2_mean": float(cv_r2_mean),
        "cv_r2_std": float(cv_r2_std),
        "test_mae": float(mae),
        "test_r2": float(r2),
        "baseline_mae": float(baseline_mae),
        "permutation_p_value": float(p_value),
        "n_samples": len(features),
        "n_features": X.shape[1],
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "random_state": random_state,
        "n_splits": n_splits,
        "n_permutations": n_permutations
    }
    
    # Save results
    logger.info(f"Saving results to {results_path}")
    eval_save_results(results, results_path)
    
    logger.info("Pipeline completed successfully")
    return results

def parse_args():
    parser = argparse.ArgumentParser(description="Integrate training and evaluation pipeline")
    parser.add_argument("--features_path", type=str, default="data/processed/features.json", help="Path to features JSON")
    parser.add_argument("--results_path", type=str, default="results/results.json", help="Path to output results JSON")
    parser.add_argument("--model_path", type=str, default="results/model.pkl", help="Path to save model")
    parser.add_argument("--n_estimators", type=int, default=100, help="Number of estimators")
    parser.add_argument("--max_depth", type=int, default=None, help="Max depth of tree")
    parser.add_argument("--random_state", type=int, default=42, help="Random state")
    parser.add_argument("--n_splits", type=int, default=5, help="Number of CV splits")
    parser.add_argument("--n_permutations", type=int, default=1000, help="Number of permutations")
    parser.add_argument("--test_size", type=float, default=0.2, help="Test set size")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    return parser.parse_args()

def main():
    args = parse_args()
    results = run_full_pipeline(
        features_path=args.features_path,
        results_path=args.results_path,
        model_path=args.model_path,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.random_state,
        n_splits=args.n_splits,
        n_permutations=args.n_permutations,
        test_size=args.test_size,
        alpha=args.alpha
    )
    logger.info("Final results: %s", json.dumps(results, indent=2))

if __name__ == "__main__":
    main()