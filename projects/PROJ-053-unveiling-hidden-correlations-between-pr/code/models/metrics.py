import os
import sys
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from config import get_results_dir, ensure_directories, get_logger
from utils.logger import setup_logging

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² score."""
    return float(r2_score(y_true, y_pred))

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error."""
    return float(mean_absolute_error(y_true, y_pred))

def calculate_rmse_percentage_of_range(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate RMSE as a percentage of the range of the true values.
    This is the SC-002 metric.
    """
    if len(y_true) == 0:
        return 0.0
    
    y_true_float = np.array(y_true, dtype=float)
    range_val = np.max(y_true_float) - np.min(y_true_float)
    
    if range_val == 0:
        return 0.0
    
    rmse = calculate_rmse(y_true, y_pred)
    percentage = (rmse / range_val) * 100.0
    return float(percentage)

def evaluate_model(
    y_true: np.ndarray, 
    y_pred: np.ndarray,
    metric_name: str = "GPR"
) -> Dict[str, float]:
    """
    Evaluate a model and return a dictionary of metrics.
    Includes R², RMSE, MAE, and rmse_as_percentage_of_range.
    """
    metrics = {
        "model_name": metric_name,
        "r2": calculate_r2(y_true, y_pred),
        "rmse": calculate_rmse(y_true, y_pred),
        "mae": calculate_mae(y_true, y_pred),
        "rmse_as_percentage_of_range": calculate_rmse_percentage_of_range(y_true, y_pred)
    }
    return metrics

def save_metrics(metrics: Dict[str, Any], filename: str = "metrics.json") -> str:
    """
    Save metrics to a JSON file in the results directory.
    Returns the path to the saved file.
    """
    results_dir = get_results_dir()
    ensure_directories()
    file_path = os.path.join(results_dir, filename)
    
    with open(file_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return file_path

def main():
    """
    Main entry point to evaluate models and save metrics.
    Expects precomputed predictions or loads them if necessary.
    For this task, we assume the evaluation happens after training
    and we are saving the aggregated metrics.
    
    In a real pipeline, this would be called by main.py or a specific
    evaluation script that loads the models and test data.
    """
    logger = setup_logging()
    logger.info("Starting metrics calculation and saving...")
    
    # This function is designed to be called by a script that has
    # the y_true and y_pred arrays ready. 
    # To satisfy the task of saving metrics, we provide the logic
    # that would be used in the pipeline.
    
    # Example of how this would be used in a pipeline script:
    # 1. Load test data (X_test, y_test)
    # 2. Load GPR model and Baseline model
    # 3. Predict y_pred_gpr, y_pred_baseline
    # 4. metrics_gpr = evaluate_model(y_test, y_pred_gpr, "GPR")
    # 5. metrics_baseline = evaluate_model(y_test, y_pred_baseline, "Linear_Baseline")
    # 6. final_report = {
    #       "gpr_metrics": metrics_gpr,
    #       "baseline_metrics": metrics_baseline,
    #       "comparison": {
    #           "rmse_improvement": metrics_baseline['rmse'] - metrics_gpr['rmse']
    #       }
    #   }
    # 7. save_metrics(final_report)
    
    logger.info("Metrics calculation functions are ready.")
    logger.info("Call evaluate_model() and save_metrics() with actual data to generate results/metrics.json")

if __name__ == "__main__":
    main()
