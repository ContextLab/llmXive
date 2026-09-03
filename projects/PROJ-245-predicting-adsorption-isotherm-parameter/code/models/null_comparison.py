"""
Null Model Comparison Module.

Implements the robust null model baseline (T065) ensuring the null model is trained
on the exact same folds as the main models for fair comparison.
Also implements T024 requirements: paired statistical testing and confidence intervals.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from scipy import stats
import joblib

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_dirs(base_path: Path) -> None:
    """Ensure necessary directories exist."""
    validation_dir = base_path / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

def load_preprocessed_data(data_path: Path) -> pd.DataFrame:
    """Load the preprocessed dataset."""
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    logger.info(f"Loading preprocessed data from {data_path}")
    return pd.read_parquet(data_path)

def predict_mean_null_model(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame) -> pd.Series:
    """
    Null Model: Predicts the mean of the training target for all test samples.
    This is the baseline that must be beaten.
    """
    mean_value = y_train.mean()
    predictions = pd.Series([mean_value] * len(X_test), index=X_test.index)
    return predictions

def bootstrap_confidence_intervals(
    metric_values: List[float],
    n_iterations: int = 1000,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence intervals for a list of metric values.
    
    Args:
        metric_values: List of metric values (e.g., RMSEs from folds).
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level (default 0.95).
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not metric_values:
        raise ValueError("metric_values cannot be empty")
    
    arr = np.array(metric_values)
    n = len(arr)
    bootstrap_means = []
    
    for _ in range(n_iterations):
        sample = np.random.choice(arr, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))
    
    bootstrap_means = np.array(bootstrap_means)
    lower = np.percentile(bootstrap_means, (1 - confidence_level) / 2 * 100)
    upper = np.percentile(bootstrap_means, (1 + confidence_level) / 2 * 100)
    
    return lower, upper

def calculate_null_model_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    """Calculate metrics for the null model."""
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    return {
        "mse": float(mse),
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }

def calculate_trained_model_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    """Calculate metrics for the trained model."""
    return calculate_null_model_metrics(y_true, y_pred)

def run_cross_fold_comparison(
    data: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the null model vs trained model comparison using EXACT SAME FOLDS.
    
    This implements T065: ensuring the null model is trained on the exact same
    folds as the main models to ensure a fair comparison.
    """
    X = data[feature_cols]
    y = data[target_col]
    
    # Use KFold for regression (StratifiedKFold is for classification)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    null_metrics = {"rmse": [], "r2": [], "mae": []}
    trained_metrics = {"rmse": [], "r2": [], "mae": []}
    trained_model = LinearRegression()
    
    logger.info(f"Starting {n_splits}-fold cross-validation comparison...")
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        logger.info(f"Processing fold {fold_idx + 1}/{n_splits}")
        
        # Split data
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # 1. NULL MODEL: Predict mean of training set
        y_pred_null = predict_mean_null_model(X_train, y_train, X_test)
        metrics_null = calculate_null_model_metrics(y_test, y_pred_null)
        
        # 2. TRAINED MODEL: Train on same training set
        trained_model.fit(X_train, y_train)
        y_pred_trained = trained_model.predict(X_test)
        metrics_trained = calculate_trained_model_metrics(y_test, y_pred_trained)
        
        # Store metrics
        null_metrics["rmse"].append(metrics_null["rmse"])
        null_metrics["r2"].append(metrics_null["r2"])
        null_metrics["mae"].append(metrics_null["mae"])
        
        trained_metrics["rmse"].append(metrics_trained["rmse"])
        trained_metrics["r2"].append(metrics_trained["r2"])
        trained_metrics["mae"].append(metrics_trained["mae"])
    
    # Calculate aggregate metrics
    null_r2_mean = np.mean(null_metrics["r2"])
    trained_r2_mean = np.mean(trained_metrics["r2"])
    
    # Statistical Test: Paired t-test on RMSEs (since folds are paired)
    t_stat, p_value = stats.ttest_rel(null_metrics["rmse"], trained_metrics["rmse"])
    
    # Calculate improvement percentage
    rmse_improvement_pct = ((np.mean(null_metrics["rmse"]) - np.mean(trained_metrics["rmse"])) / 
                            np.mean(null_metrics["rmse"])) * 100
    
    # Bootstrap Confidence Intervals for R2
    null_r2_ci = bootstrap_confidence_intervals(null_metrics["r2"])
    trained_r2_ci = bootstrap_confidence_intervals(trained_metrics["r2"])
    
    # Determine significance
    is_significant = p_value < 0.05
    improvement_meets_threshold = rmse_improvement_pct > 20.0
    
    result = {
        "null_model": {
            "mean_r2": float(null_r2_mean),
            "mean_rmse": float(np.mean(null_metrics["rmse"])),
            "mean_mae": float(np.mean(null_metrics["mae"])),
            "r2_confidence_interval": {
                "lower": float(null_r2_ci[0]),
                "upper": float(null_r2_ci[1])
            },
            "fold_rmse_values": [float(x) for x in null_metrics["rmse"]]
        },
        "trained_model": {
            "mean_r2": float(trained_r2_mean),
            "mean_rmse": float(np.mean(trained_metrics["rmse"])),
            "mean_mae": float(np.mean(trained_metrics["mae"])),
            "r2_confidence_interval": {
                "lower": float(trained_r2_ci[0]),
                "upper": float(trained_r2_ci[1])
            },
            "fold_rmse_values": [float(x) for x in trained_metrics["rmse"]]
        },
        "comparison": {
            "rmse_improvement_pct": float(rmse_improvement_pct),
            "p_value": float(p_value),
            "t_statistic": float(t_stat),
            "is_significant": bool(is_significant),
            "improvement_meets_20pct_threshold": bool(improvement_meets_threshold),
            "method": "Paired t-test on RMSE across 5 folds"
        },
        "fold_count": n_splits
    }
    
    return result

def main():
    """Main entry point for null model comparison."""
    # Configuration
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "processed" / "final_dataset.parquet"
    output_path = base_path / "data" / "validation" / "null_model_comparison.json"
    target_col = "langmuir_capacity"
    
    # Define features (exclude target and identifiers)
    exclude_cols = ["material_id", "adsorbent_structure_id", "langmuir_capacity", "henry_constant"]
    
    ensure_dirs(base_path / "data" / "validation")
    
    try:
        # Load data
        df = load_preprocessed_data(data_path)
        
        # Identify feature columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if len(feature_cols) < 1:
            raise ValueError("No feature columns found after excluding target and identifiers.")
        
        logger.info(f"Using {len(feature_cols)} features for comparison.")
        
        # Run comparison
        results = run_cross_fold_comparison(
            data=df,
            target_col=target_col,
            feature_cols=feature_cols,
            n_splits=5,
            random_state=42
        )
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Null model comparison results saved to {output_path}")
        logger.info(f"RMSE Improvement: {results['comparison']['rmse_improvement_pct']:.2f}%")
        logger.info(f"Statistical Significance (p < 0.05): {results['comparison']['is_significant']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error running null model comparison: {e}")
        raise

if __name__ == "__main__":
    main()