"""
Evaluation module for molecular property prediction models.

Calculates metrics (RMSE, r), generates visualizations, and saves summaries.
"""
import os
import sys
import pickle
import logging
import json
import time
from pathlib import Path
from typing import Tuple, Dict, Any, List
import yaml

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import joblib

# Add parent directory to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import RANDOM_SEED
from utils.logging import get_logger, log_pipeline_step, start_monitoring, get_global_monitor
from utils.update_state import update_state, compute_file_hash
from data.preprocess import load_schema, validate_dataframe_against_schema

logger = get_logger(__name__)

def load_processed_data(csv_path: str) -> pd.DataFrame:
    """Load the processed molecules dataset."""
    logger.info(f"Loading processed data from {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Processed data not found at {csv_path}")
    return pd.read_csv(csv_path)

def load_model(path: str):
    """Load a model artifact."""
    logger.info(f"Loading model from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model artifact not found at {path}")
    return joblib.load(path)

def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate RMSE and Pearson correlation coefficient."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r, _ = pearsonr(y_true, y_pred)
    return {"rmse": rmse, "r": r}

def baseline_comparison(y_train: pd.Series, y_test: pd.Series) -> float:
    """
    Compute RMSE against a mean predictor baseline.
    Returns the RMSE of the mean of training set applied to test set.
    """
    mean_train = y_train.mean()
    predictions = np.full_like(y_test, mean_train, dtype=float)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    logger.info(f"Mean predictor baseline RMSE: {rmse:.4f}")
    return rmse

def plot_predicted_vs_experimental(y_true: pd.Series, y_pred: np.ndarray, output_path: str):
    """Generate scatter plot of predicted vs experimental values."""
    logger.info(f"Generating scatter plot: {output_path}")
    plt.figure(figsize=(10, 8))
    plt.scatter(y_true, y_pred, alpha=0.6, edgecolors='k')
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
    plt.xlabel("Experimental Values")
    plt.ylabel("Predicted Values")
    plt.title("Predicted vs Experimental Values")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")

def plot_feature_importance(importance_dict: Dict[str, Any], output_path: str):
    """Generate bar chart of feature importances."""
    logger.info(f"Generating feature importance plot: {output_path}")
    features = importance_dict["features"]
    importances = importance_dict["importances"]
    
    plt.figure(figsize=(12, 8))
    # Sort by importance (already sorted in dict, but ensure)
    indices = np.argsort(importances)[::-1]
    features = [features[i] for i in indices]
    importances = [importances[i] for i in indices]
    
    plt.barh(features, importances, align='center')
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")
    plt.title("Random Forest Feature Importance")
    plt.gca().invert_yaxis() # Most important at top
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Feature importance plot saved to {output_path}")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metrics_summary(summary: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate metrics summary against schema."""
    # Basic validation: check required keys
    required_keys = schema.get('required', [])
    for key in required_keys:
        if key not in summary:
            logger.error(f"Missing required key in metrics summary: {key}")
            return False
    return True

def save_metrics_summary(summary: Dict[str, Any], output_path: str):
    """Write final metrics to JSON."""
    logger.info(f"Saving metrics summary to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info("Metrics summary saved")

def main():
    """Main entry point for the evaluation pipeline."""
    log_pipeline_step("START_EVALUATION")
    start_time = time.perf_counter()
    monitor = get_global_monitor()
    if monitor:
        start_monitoring(monitor)

    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "processed"
    models_dir = project_root / "data" / "processed"
    
    processed_csv = data_dir / "molecules_processed.csv"
    lr_path = models_dir / "model_lr.pkl"
    rf_path = models_dir / "model_rf.pkl"
    importance_path = models_dir / "feature_importance.json"
    
    scatter_path = data_dir / "plot_scatter.png"
    importance_plot_path = data_dir / "plot_importance.png"
    metrics_summary_path = data_dir / "metrics_summary.json"
    
    # Load Data
    df = load_processed_data(str(processed_csv))
    target_col = 'target_value'
    if target_col not in df.columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            target_col = numeric_cols[-1]
    
    # Re-split data to get test set (using same seed as training)
    # Note: In a real pipeline, we would load the split indices or store the test set.
    # Here we re-split for evaluation consistency.
    from sklearn.model_selection import train_test_split
    df_temp = df.copy()
    df_temp['target_bin'] = pd.qcut(df_temp[target_col], q=10, duplicates='drop')
    X = df.drop(columns=[target_col, 'target_bin'])
    y = df[target_col]
    stratify = df_temp['target_bin']
    if 'target_bin' in X.columns:
        X = X.drop(columns=['target_bin'])
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=stratify
    )

    # Load Models
    lr_model = load_model(str(lr_path))
    rf_model = load_model(str(rf_path))
    
    # Predict
    y_pred_lr = lr_model.predict(X_test)
    y_pred_rf = rf_model.predict(X_test)
    
    # Calculate Metrics
    metrics_lr = calculate_metrics(y_test, y_pred_lr)
    metrics_rf = calculate_metrics(y_test, y_pred_rf)
    
    # Baseline Comparison
    baseline_rmse = baseline_comparison(y_train, y_test)
    
    logger.info(f"Linear Regression - RMSE: {metrics_lr['rmse']:.4f}, r: {metrics_lr['r']:.4f}")
    logger.info(f"Random Forest - RMSE: {metrics_rf['rmse']:.4f}, r: {metrics_rf['r']:.4f}")
    logger.info(f"Baseline RMSE: {baseline_rmse:.4f}")
    
    # Generate Plots
    plot_predicted_vs_experimental(y_test, y_pred_rf, str(scatter_path))
    
    # Load feature importance for plotting
    with open(importance_path, 'r') as f:
        importance_data = json.load(f)
    plot_feature_importance(importance_data, str(importance_plot_path))
    
    # Prepare Summary
    end_time = time.perf_counter()
    duration = end_time - start_time
    peak_mem = monitor.get_usage().get('peak_mb', 0) if monitor else 0
    
    summary = {
        "baseline_rmse": baseline_rmse,
        "model_lr_rmse": metrics_lr['rmse'],
        "model_rf_rmse": metrics_rf['rmse'],
        "model_lr_r": metrics_lr['r'],
        "model_rf_r": metrics_rf['r'],
        "pipeline_time_seconds": duration,
        "peak_memory_mb": peak_mem,
        "plot_scatter_path": str(scatter_path.relative_to(project_root)),
        "plot_importance_path": str(importance_plot_path.relative_to(project_root))
    }
    
    # Validate and Save
    schema_path = project_root / "code" / "contracts" / "model_output.schema.yaml"
    if os.path.exists(schema_path):
        schema = load_schema(str(schema_path))
        if not validate_metrics_summary(summary, schema):
            logger.error("Metrics summary failed validation")
            # Continue anyway but log error
    
    save_metrics_summary(summary, str(metrics_summary_path))
    
    # Update state
    artifacts = [
        str(scatter_path),
        str(importance_plot_path),
        str(metrics_summary_path)
    ]
    for art in artifacts:
        if os.path.exists(art):
            update_state(art, compute_file_hash(art))
    
    if monitor:
        monitor.stop()
    
    log_pipeline_step("END_EVALUATION")

if __name__ == "__main__":
    main()