"""
Metrics module for assessing reproducibility of machine-learned reaction yield models.

Implements MAE, R², Spearman ρ, and the Deviation Index (S) calculation per FR-009.
"""
import numpy as np
from scipy.stats import spearmanr
from typing import Tuple, Optional, Union

# Define epsilon for numerical stability
EPSILON = 1e-6

def calculate_mae(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> float:
    """
    Calculate Mean Absolute Error (MAE).
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        
    Returns:
        float: The MAE value.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {y_true.shape} and {y_pred.shape}")
        
    if y_true.size == 0:
        return 0.0
        
    return float(np.mean(np.abs(y_true - y_pred)))

def calculate_r2(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> float:
    """
    Calculate Coefficient of Determination (R²).
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        
    Returns:
        float: The R² value.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {y_true.shape} and {y_pred.shape}")
        
    if y_true.size == 0:
        return 0.0
        
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
        
    return float(1 - (ss_res / ss_tot))

def calculate_spearman_rho(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> float:
    """
    Calculate Spearman's rank correlation coefficient (ρ).
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        
    Returns:
        float: The Spearman ρ value.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {y_true.shape} and {y_pred.shape}")
        
    if y_true.size < 2:
        return 0.0
        
    rho, _ = spearmanr(y_true, y_pred)
    
    # Handle NaN if constant input
    if np.isnan(rho):
        return 0.0
        
    return float(rho)

def calculate_deviation_index(
    mae_obs: float,
    r2_obs: float,
    rho_obs: float,
    mae_ref: float,
    r2_ref: float,
    rho_ref: float,
    epsilon: float = EPSILON
) -> float:
    """
    Calculate the Deviation Index (S) as defined in FR-009.
    
    Formula: S = 1 – (|ΔMAE|/(|MAE_ref|+ε) + |ΔR2|/(|R2_ref|+ε) + |Δρ|/(|ρ_ref|+ε))/3
    
    Args:
        mae_obs: Observed Mean Absolute Error.
        r2_obs: Observed R².
        rho_obs: Observed Spearman ρ.
        mae_ref: Reference (reported) MAE.
        r2_ref: Reference (reported) R².
        rho_ref: Reference (reported) Spearman ρ.
        epsilon: Small constant to prevent division by zero (default 1e-6).
        
    Returns:
        float: The Deviation Index S, where 1.0 indicates perfect agreement.
    """
    delta_mae = abs(mae_obs - mae_ref)
    delta_r2 = abs(r2_obs - r2_ref)
    delta_rho = abs(rho_obs - rho_ref)
    
    term_mae = delta_mae / (abs(mae_ref) + epsilon)
    term_r2 = delta_r2 / (abs(r2_ref) + epsilon)
    term_rho = delta_rho / (abs(rho_ref) + epsilon)
    
    s = 1.0 - (term_mae + term_r2 + term_rho) / 3.0
    
    return float(s)

def calculate_all_metrics(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list],
    mae_ref: Optional[float] = None,
    r2_ref: Optional[float] = None,
    rho_ref: Optional[float] = None
) -> dict:
    """
    Calculate all metrics (MAE, R², Spearman ρ) and optionally the Deviation Index.
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        mae_ref: Reference MAE for deviation calculation (optional).
        r2_ref: Reference R² for deviation calculation (optional).
        rho_ref: Reference Spearman ρ for deviation calculation (optional).
        
    Returns:
        dict: Dictionary containing calculated metrics.
    """
    mae = calculate_mae(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)
    rho = calculate_spearman_rho(y_true, y_pred)
    
    result = {
        "mae": mae,
        "r2": r2,
        "spearman_rho": rho
    }
    
    if mae_ref is not None and r2_ref is not None and rho_ref is not None:
        s = calculate_deviation_index(mae, r2, rho, mae_ref, r2_ref, rho_ref)
        result["deviation_index"] = s
        
    return result

if __name__ == "__main__":
    # Simple self-test when run directly
    import json
    
    # Mock data for testing
    y_true_test = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pred_test = [1.1, 2.1, 2.9, 4.2, 4.8]
    
    # Mock reference values (perfect match for testing)
    mae_ref_test = calculate_mae(y_true_test, y_pred_test)
    r2_ref_test = calculate_r2(y_true_test, y_pred_test)
    rho_ref_test = calculate_spearman_rho(y_true_test, y_pred_test)
    
    metrics = calculate_all_metrics(
        y_true_test, y_pred_test,
        mae_ref_test, r2_ref_test, rho_ref_test
    )
    
    print("Metrics calculation test:")
    print(json.dumps(metrics, indent=2))
    
    # Verify S is close to 1.0 when observed matches reference
    assert 0.99 < metrics["deviation_index"] <= 1.0, "Deviation index should be near 1.0 for perfect match"
    print("Self-test passed.")
