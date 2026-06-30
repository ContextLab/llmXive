"""
Metrics computation module for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements F1 score and Mean Absolute Percentage Error (MAPE) with robust edge case handling.
"""
import numpy as np
from typing import Union, List, Optional
import logging
from src.utils.logging import get_logger

logger: logging.Logger = get_logger(__name__)


def compute_f1(y_true: Union[np.ndarray, List[float], List[int]], 
               y_pred: Union[np.ndarray, List[float], List[int]], 
               average: str = 'binary') -> float:
    """
    Compute the F1 score between true and predicted labels.
    
    Handles edge cases: empty arrays, division by zero, and binary/multi-class scenarios.
    For binary classification, assumes labels are 0/1 or False/True.
    
    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        average: Averaging strategy. 'binary' for binary classification, 
                 'macro' or 'weighted' for multi-class (if extended).
    
    Returns:
        float: F1 score. Returns 0.0 if metrics cannot be computed (e.g., no positive predictions).
    
    Raises:
        ValueError: If input arrays are empty or have mismatched lengths.
    """
    # Convert inputs to numpy arrays
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    
    # Edge case: Empty arrays
    if y_true_arr.size == 0 or y_pred_arr.size == 0:
        logger.warning("Empty input arrays provided to compute_f1. Returning 0.0.")
        return 0.0
    
    # Edge case: Mismatched lengths
    if y_true_arr.shape != y_pred_arr.shape:
        logger.error(f"Shape mismatch: y_true {y_true_arr.shape} vs y_pred {y_pred_arr.shape}")
        raise ValueError("y_true and y_pred must have the same shape.")
    
    # Flatten for safety if multi-dimensional
    y_true_flat = y_true_arr.flatten()
    y_pred_flat = y_pred_arr.flatten()
    
    # Determine unique labels to handle binary vs multi-class logic implicitly
    # Assuming binary classification for this specific task scope (0/1)
    # If multi-class is needed later, this logic can be expanded using sklearn.metrics.f1_score
    # But we implement manually here to avoid heavy dependencies if possible, 
    # though sklearn is in requirements. Let's use sklearn for robustness as per requirements.
    
    try:
        from sklearn.metrics import f1_score
        # sklearn handles empty arrays and shape checks, but we already did basic checks.
        # We pass the 'average' parameter.
        # If the data is 0/1, 'binary' is default if pos_label=1.
        # To be safe with the 'binary' argument specifically:
        if average == 'binary':
            # Ensure pos_label is 1 for standard binary
            return float(f1_score(y_true_flat, y_pred_flat, average='binary', pos_label=1))
        else:
            return float(f1_score(y_true_flat, y_pred_flat, average=average))
    except Exception as e:
        logger.error(f"Error computing F1 score with sklearn: {e}")
        # Fallback manual calculation if sklearn fails unexpectedly
        if average == 'binary':
            tp = np.sum((y_true_flat == 1) & (y_pred_flat == 1))
            fp = np.sum((y_true_flat == 0) & (y_pred_flat == 1))
            fn = np.sum((y_true_flat == 1) & (y_pred_flat == 0))
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            if precision + recall == 0:
                return 0.0
            return 2 * (precision * recall) / (precision + recall)
        return 0.0


def compute_mape(y_true: Union[np.ndarray, List[float]], 
                 y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Compute the Mean Absolute Percentage Error (MAPE).
    
    Handles edge cases: division by zero (when y_true is 0), and empty arrays.
    If y_true contains zeros, those samples are excluded from the calculation.
    If all y_true are zero, returns 0.0.
    
    Args:
        y_true: Ground truth values (continuous).
        y_pred: Predicted values (continuous).
    
    Returns:
        float: MAPE as a percentage (e.g., 0.05 for 5%). Returns 0.0 if calculation is not possible.
    
    Raises:
        ValueError: If input arrays are empty or have mismatched lengths.
    """
    # Convert inputs to numpy arrays
    y_true_arr = np.array(y_true, dtype=float)
    y_pred_arr = np.array(y_pred, dtype=float)
    
    # Edge case: Empty arrays
    if y_true_arr.size == 0 or y_pred_arr.size == 0:
        logger.warning("Empty input arrays provided to compute_mape. Returning 0.0.")
        return 0.0
    
    # Edge case: Mismatched lengths
    if y_true_arr.shape != y_pred_arr.shape:
        logger.error(f"Shape mismatch: y_true {y_true_arr.shape} vs y_pred {y_pred_arr.shape}")
        raise ValueError("y_true and y_pred must have the same shape.")
    
    # Flatten for safety
    y_true_flat = y_true_arr.flatten()
    y_pred_flat = y_pred_arr.flatten()
    
    # Identify valid indices where y_true is not zero to avoid division by zero
    mask = y_true_flat != 0
    valid_count = np.sum(mask)
    
    if valid_count == 0:
        logger.warning("All y_true values are zero. Cannot compute MAPE. Returning 0.0.")
        return 0.0
    
    # Calculate absolute percentage errors for valid entries
    abs_errors = np.abs(y_true_flat[mask] - y_pred_flat[mask])
    percent_errors = abs_errors / np.abs(y_true_flat[mask])
    
    mape = np.mean(percent_errors)
    
    return float(mape)
