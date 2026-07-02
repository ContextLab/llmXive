"""
Evaluation runner for HEA yield strength prediction models.

Computes R², MAE, and RMSE on held-out test sets for Linear Regression,
Random Forest, and Gradient Boosting models.
"""
import os
import sys
import json
import time
from typing import Dict, Any, Tuple, Optional, List

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Import from project modules
from utils.logging import get_logger
from models.train import (
    load_processed_data,
    prepare_features_target,
    create_stratified_split,
    train_linear_regression,
    train_random_forest,
    train_gradient_boosting,
)

logger = get_logger(__name__)


def compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Compute evaluation metrics: R², MAE, RMSE.
    
    Args:
        y_true: True target values.
        y_pred: Predicted target values.
        
    Returns:
        Dictionary with 'r2', 'mae', 'rmse' keys.
    """
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    return {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
    }


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str,
) -> Dict[str, float]:
    """
    Evaluate a trained model on the test set.
    
    Args:
        model: Trained scikit-learn model.
        X_test: Test features.
        y_test: Test targets.
        model_name: Name of the model for logging.
        
    Returns:
        Dictionary of metrics.
    """
    logger.info(f"Evaluating {model_name} on test set...")
    start_time = time.time()
    
    y_pred = model.predict(X_test)
    metrics = compute_metrics(y_test, y_pred)
    
    elapsed = time.time() - start_time
    logger.info(
        f"{model_name} evaluation complete in {elapsed:.2f}s. "
        f"R²={metrics['r2']:.4f}, MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}"
    )
    
    return metrics


def run_evaluation_pipeline(
    processed_data_path: str,
    split_info_path: str,
    output_dir: str,
) -> Dict[str, Dict[str, float]]:
    """
    Run the full evaluation pipeline: load data, load splits, train models, evaluate.
    
    This function orchestrates loading the processed data, retrieving the train/test
    split indices, training all models (Linear, RF, GB), and computing metrics on
    the held-out test set.
    
    Args:
        processed_data_path: Path to the processed CSV with descriptors.
        split_info_path: Path to the JSON file containing split indices.
        output_dir: Directory to save evaluation results.
        
    Returns:
        Dictionary mapping model names to their metric dictionaries.
    """
    logger.info("Starting evaluation pipeline...")
    
    # Load processed data
    logger.info(f"Loading processed data from {processed_data_path}")
    df = load_processed_data(processed_data_path)
    
    # Prepare features and target
    feature_cols, target_col = prepare_features_target(df)
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Load split info
    logger.info(f"Loading split info from {split_info_path}")
    with open(split_info_path, "r") as f:
        split_info = json.load(f)
    
    train_indices = split_info["train_indices"]
    test_indices = split_info["test_indices"]
    
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]
    
    logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    
    results = {}
    
    # 1. Evaluate Linear Regression
    logger.info("Training and evaluating Linear Regression baseline...")
    lr_model = train_linear_regression(X_train, y_train)
    results["linear_regression"] = evaluate_model(
        lr_model, X_test, y_test, "Linear Regression"
    )
    
    # 2. Evaluate Random Forest
    logger.info("Training and evaluating Random Forest...")
    rf_model = train_random_forest(X_train, y_train)
    results["random_forest"] = evaluate_model(
        rf_model, X_test, y_test, "Random Forest"
    )
    
    # 3. Evaluate Gradient Boosting
    logger.info("Training and evaluating Gradient Boosting...")
    gb_model = train_gradient_boosting(X_train, y_train)
    results["gradient_boosting"] = evaluate_model(
        gb_model, X_test, y_test, "Gradient Boosting"
    )
    
    logger.info("Evaluation pipeline complete.")
    return results


def main():
    """Main entry point for the evaluation script."""
    # Configuration paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    processed_data_path = os.path.join(base_dir, "data", "processed", "hea_descriptors.csv")
    split_info_path = os.path.join(base_dir, "output", "split_info.json")
    output_dir = os.path.join(base_dir, "output")
    
    if not os.path.exists(processed_data_path):
        logger.error(f"Processed data not found at {processed_data_path}")
        sys.exit(1)
        
    if not os.path.exists(split_info_path):
        logger.error(f"Split info not found at {split_info_path}")
        sys.exit(1)
    
    # Run evaluation
    results = run_evaluation_pipeline(
        processed_data_path=processed_data_path,
        split_info_path=split_info_path,
        output_dir=output_dir,
    )
    
    # Save results to JSON (T021 dependency, but we do it here to ensure output exists)
    metrics_output_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Metrics saved to {metrics_output_path}")
    return results


if __name__ == "__main__":
    main()