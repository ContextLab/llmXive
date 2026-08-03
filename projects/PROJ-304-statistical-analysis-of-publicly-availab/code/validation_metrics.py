"""
T030: Implement performance metric calculation (RMSE, R², AIC) for each fold and model type.

This module calculates the performance metrics (RMSE, R², AIC) for spatial cross-validation results.
It expects input data structured as a list of dictionaries, where each dictionary represents
a fold's results containing true values, predicted values, and the model type.
"""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from logger import get_logger, get_project_root

logger = get_logger(__name__)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Root Mean Squared Error.

    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.

    Returns:
        RMSE value.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        logger.warning("Empty arrays provided for RMSE calculation")
        return float('nan')

    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (Coefficient of Determination).

    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.

    Returns:
        R² value.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        logger.warning("Empty arrays provided for R² calculation")
        return float('nan')

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        logger.warning("Zero variance in y_true, R² is undefined")
        return float('nan')

    return float(1 - (ss_res / ss_tot))

def calculate_aic(n: int, rss: float, k: int) -> float:
    """
    Calculate Akaike Information Criterion.
    
    Note: This uses the standard OLS-based AIC formula: n*ln(RSS/n) + 2k.
    For spatial models, this is an approximation. The exact AIC depends on the
    likelihood function used by the specific spatial model estimator.
    However, for comparative purposes across models trained on the same data,
    this metric is often used.

    Args:
        n: Number of observations.
        rss: Residual Sum of Squares.
        k: Number of parameters (including intercept).

    Returns:
        AIC value.
    """
    if n == 0 or rss == 0:
        logger.warning("Invalid parameters for AIC calculation")
        return float('nan')

    # Avoid log(0)
    if rss / n <= 0:
        logger.warning("Non-positive RSS/n for AIC calculation")
        return float('nan')

    return float(n * np.log(rss / n) + 2 * k)

def calculate_metrics_for_fold(
    fold_results: Dict[str, Any],
    k_params: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate RMSE, R², and AIC for a single fold's results.

    Args:
        fold_results: Dictionary containing 'y_true', 'y_pred', 'model_type', 
                      and optionally 'n_params' for AIC calculation.
        k_params: Number of parameters if not provided in fold_results.

    Returns:
        Dictionary with calculated metrics: {'rmse', 'r2', 'aic'}.
    """
    y_true = np.array(fold_results['y_true'])
    y_pred = np.array(fold_results['y_pred'])
    model_type = fold_results.get('model_type', 'unknown')
    
    # Determine number of parameters for AIC
    n_params = fold_results.get('n_params', k_params)
    if n_params is None:
        # Default to a small number if unknown, but log a warning
        logger.warning(f"Number of parameters not provided for {model_type}, using default 3")
        n_params = 3

    metrics = {
        'model_type': model_type,
        'fold_index': fold_results.get('fold_index', -1),
        'rmse': calculate_rmse(y_true, y_pred),
        'r2': calculate_r2(y_true, y_pred),
        'aic': float('nan') # Initialize AIC
    }

    # Calculate AIC only if we have valid RSS
    rss = np.sum((y_true - y_pred) ** 2)
    if not np.isnan(metrics['rmse']) and rss > 0:
        metrics['aic'] = calculate_aic(len(y_true), rss, n_params)

    logger.info(
        f"Calculated metrics for {model_type} (Fold {metrics['fold_index']}): "
        f"RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}, AIC={metrics['aic']:.4f}"
    )

    return metrics

def aggregate_metrics_across_folds(
    fold_metrics_list: List[Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate metrics across all folds for each model type.
    
    Calculates mean and standard deviation for RMSE, R², and AIC per model type.

    Args:
        fold_metrics_list: List of metric dictionaries from calculate_metrics_for_fold.

    Returns:
        Dictionary mapping model_type to aggregated stats:
        {
            'model_type': {
                'rmse_mean': float, 'rmse_std': float,
                'r2_mean': float, 'r2_std': float,
                'aic_mean': float, 'aic_std': float,
                'n_folds': int
            },
            ...
        }
    """
    if not fold_metrics_list:
        logger.warning("No fold metrics provided for aggregation")
        return {}

    # Group by model type
    model_metrics = {}
    for metrics in fold_metrics_list:
        model_type = metrics['model_type']
        if model_type not in model_metrics:
            model_metrics[model_type] = {
                'rmse': [],
                'r2': [],
                'aic': []
            }
        
        if not np.isnan(metrics['rmse']):
            model_metrics[model_type]['rmse'].append(metrics['rmse'])
        if not np.isnan(metrics['r2']):
            model_metrics[model_type]['r2'].append(metrics['r2'])
        if not np.isnan(metrics['aic']):
            model_metrics[model_type]['aic'].append(metrics['aic'])

    aggregated = {}
    for model_type, values in model_metrics.items():
        n_folds = len(values['rmse']) if values['rmse'] else 0
        
        aggregated[model_type] = {
            'n_folds': n_folds,
            'rmse_mean': float(np.mean(values['rmse'])) if values['rmse'] else float('nan'),
            'rmse_std': float(np.std(values['rmse'])) if values['rmse'] else float('nan'),
            'r2_mean': float(np.mean(values['r2'])) if values['r2'] else float('nan'),
            'r2_std': float(np.std(values['r2'])) if values['r2'] else float('nan'),
            'aic_mean': float(np.mean(values['aic'])) if values['aic'] else float('nan'),
            'aic_std': float(np.std(values['aic'])) if values['aic'] else float('nan')
        }
        
        logger.info(
            f"Aggregated metrics for {model_type} over {n_folds} folds: "
            f"RMSE={aggregated[model_type]['rmse_mean']:.4f}±{aggregated[model_type]['rmse_std']:.4f}, "
            f"R²={aggregated[model_type]['r2_mean']:.4f}±{aggregated[model_type]['r2_std']:.4f}"
        )

    return aggregated

def main():
    """
    Main entry point for T030.
    
    This function is intended to be called by the validation pipeline (T029)
    to calculate and aggregate metrics. In a real execution context, it would
    receive the results from run_spatial_cross_validation and write the
    aggregated results to a file.
    
    For this task implementation, we demonstrate the logic with mock data
    to ensure the functions work correctly.
    """
    logger.info("Starting T030: Performance metric calculation")
    
    # Simulate results from 5-fold cross-validation for 3 model types
    # In a real scenario, this data comes from run_spatial_cross_validation
    mock_fold_results = [
        {'model_type': 'OLS', 'fold_index': 0, 'y_true': [1, 2, 3, 4, 5], 'y_pred': [1.1, 2.2, 2.8, 4.1, 4.9], 'n_params': 3},
        {'model_type': 'OLS', 'fold_index': 1, 'y_true': [2, 3, 4, 5, 6], 'y_pred': [2.1, 3.0, 4.2, 4.8, 6.1], 'n_params': 3},
        {'model_type': 'Spatial Lag', 'fold_index': 0, 'y_true': [1, 2, 3, 4, 5], 'y_pred': [1.05, 1.95, 3.1, 3.9, 5.05], 'n_params': 4},
        {'model_type': 'Spatial Lag', 'fold_index': 1, 'y_true': [2, 3, 4, 5, 6], 'y_pred': [2.02, 2.98, 4.05, 5.1, 5.95], 'n_params': 4},
        {'model_type': 'Spatial Error', 'fold_index': 0, 'y_true': [1, 2, 3, 4, 5], 'y_pred': [1.08, 2.1, 2.9, 4.05, 4.95], 'n_params': 4},
        {'model_type': 'Spatial Error', 'fold_index': 1, 'y_true': [2, 3, 4, 5, 6], 'y_pred': [1.95, 3.05, 4.1, 4.9, 6.05], 'n_params': 4},
    ]

    # Calculate metrics for each fold
    fold_metrics = []
    for result in mock_fold_results:
        metrics = calculate_metrics_for_fold(result)
        fold_metrics.append(metrics)

    # Aggregate across folds
    aggregated = aggregate_metrics_across_folds(fold_metrics)

    logger.info("T030 completed. Metrics calculated and aggregated.")
    
    # In a real pipeline, we would write 'aggregated' to data/processed/metrics.json
    # For this task, we return the result to show it works
    return aggregated

if __name__ == '__main__':
    main()
