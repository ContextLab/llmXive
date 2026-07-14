import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

def expected_calibration_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    uncertainty: np.ndarray,
    bins: int = 10
) -> float:
    """
    Calculate Expected Calibration Error (ECE) using quantile binning.
    
    Args:
        y_true: True target values.
        y_pred: Predicted mean values.
        uncertainty: Predicted standard deviations (or square root of variance).
        bins: Number of bins for quantile binning.
        
    Returns:
        ECE value as a float.
    """
    if len(y_true) != len(y_pred) or len(y_true) != len(uncertainty):
        raise ValueError("Input arrays must have the same length")
        
    # Calculate residuals
    residuals = np.abs(y_true - y_pred)
    
    # Bin by uncertainty (quantile binning)
    # We want to check if predicted uncertainty matches actual error
    try:
        bins_edges = np.quantile(uncertainty, np.linspace(0, 1, bins + 1))
    except Exception:
        # Fallback to uniform binning if quantile fails
        bins_edges = np.linspace(uncertainty.min(), uncertainty.max() + 1e-10, bins + 1)
        
    ece = 0.0
    total_samples = len(y_true)
    
    for i in range(bins):
        lower, upper = bins_edges[i], bins_edges[i + 1]
        
        if i == bins - 1:
            mask = (uncertainty >= lower) & (uncertainty <= upper)
        else:
            mask = (uncertainty >= lower) & (uncertainty < upper)
            
        if np.sum(mask) == 0:
            continue
            
        # Average uncertainty in this bin
        avg_uncertainty = np.mean(uncertainty[mask])
        # Average absolute error in this bin
        avg_error = np.mean(residuals[mask])
        
        # Contribution to ECE: weight by bin size * difference between avg error and avg uncertainty
        ece += (np.sum(mask) / total_samples) * np.abs(avg_error - avg_uncertainty)
        
    return float(ece)


def interval_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    uncertainty: np.ndarray,
    alpha: float = 0.1
) -> float:
    """
    Calculate Interval Score for a given confidence level (1-alpha).
    
    The interval score penalizes intervals that are too wide or do not contain the true value.
    For 90% confidence interval (alpha=0.1):
    - Lower bound: y_pred - 1.645 * uncertainty
    - Upper bound: y_pred + 1.645 * uncertainty
    
    Args:
        y_true: True target values.
        y_pred: Predicted mean values.
        uncertainty: Predicted standard deviations.
        alpha: Significance level (e.g., 0.1 for 90% CI).
        
    Returns:
        Mean interval score as a float.
    """
    # Z-score for the given alpha (two-tailed)
    from scipy.stats import norm
    z_score = norm.ppf(1 - alpha / 2)
    
    lower_bound = y_pred - z_score * uncertainty
    upper_bound = y_pred + z_score * uncertainty
    
    # Interval width
    width = upper_bound - lower_bound
    
    # Penalty for missing the true value
    penalty = np.maximum(
        0,
        np.maximum(lower_bound - y_true, y_true - upper_bound)
    ) * (2 * z_score / alpha)
    
    # Interval score = width + penalty
    scores = width + penalty
    
    return float(np.mean(scores))


def sharpness(uncertainty: np.ndarray) -> float:
    """
    Calculate Sharpness (average predicted uncertainty).
    Lower sharpness indicates more confident (narrower) predictions.
    
    Args:
        uncertainty: Predicted standard deviations.
        
    Returns:
        Mean uncertainty as a float.
    """
    return float(np.mean(uncertainty))


def decompose_uncertainty(
    predictions: pd.DataFrame,
    method_col: str = 'method',
    pred_col: str = 'prediction',
    var_col: str = 'variance'
) -> Tuple[float, float, float]:
    """
    Separate aleatoric and epistemic uncertainty from model predictions.
    
    According to task T022a:
    - Epistemic variance = variance of means across samples (captures model uncertainty)
    - Aleatoric variance = mean of predicted variances (captures data noise)
    - Total variance = epistemic + aleatoric
    
    This function computes these metrics for a given method's predictions.
    
    Args:
        predictions: DataFrame containing predictions with columns for method, 
                    prediction (mean), and variance.
        method_col: Column name for the method identifier.
        pred_col: Column name for predicted means.
        var_col: Column name for predicted variances.
        
    Returns:
        Tuple of (aleatoric_variance, epistemic_variance, total_variance)
    """
    # Ensure we have the required columns
    if method_col not in predictions.columns:
        raise ValueError(f"Column '{method_col}' not found in predictions")
    if pred_col not in predictions.columns:
        raise ValueError(f"Column '{pred_col}' not found in predictions")
    if var_col not in predictions.columns:
        raise ValueError(f"Column '{var_col}' not found in predictions")
        
    # Extract means and variances
    means = predictions[pred_col].values
    variances = predictions[var_col].values
    
    # Aleatoric variance: mean of predicted variances
    aleatoric_var = float(np.mean(variances))
    
    # Epistemic variance: variance of means
    # This captures the uncertainty in the model's estimate of the mean
    epistemic_var = float(np.var(means, ddof=1))  # ddof=1 for sample variance
    
    # Total variance: sum of both components
    total_var = aleatoric_var + epistemic_var
    
    return aleatoric_var, epistemic_var, total_var


def calculate_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    uncertainty: np.ndarray,
    alpha: float = 0.1
) -> Dict[str, float]:
    """
    Calculate all UQ metrics at once for convenience.
    
    Args:
        y_true: True target values.
        y_pred: Predicted mean values.
        uncertainty: Predicted standard deviations.
        alpha: Significance level for interval score.
        
    Returns:
        Dictionary with ECE, Interval Score, and Sharpness.
    """
    return {
        'ece': expected_calibration_error(y_true, y_pred, uncertainty),
        'interval_score': interval_score(y_true, y_pred, uncertainty, alpha),
        'sharpness': sharpness(uncertainty)
    }


def main():
    """
    Main function to demonstrate the metrics calculation.
    This is typically called by the pipeline orchestrator.
    """
    # Example usage with dummy data for demonstration
    # In production, this would be called with real data from the pipeline
    np.random.seed(42)
    n_samples = 1000
    
    y_true = np.random.randn(n_samples)
    y_pred = y_true + np.random.randn(n_samples) * 0.5
    uncertainty = np.abs(np.random.randn(n_samples)) + 0.1
    
    metrics = calculate_all_metrics(y_true, y_pred, uncertainty)
    
    print("UQ Metrics Calculation Results:")
    print(f"  ECE: {metrics['ece']:.4f}")
    print(f"  Interval Score (90%): {metrics['interval_score']:.4f}")
    print(f"  Sharpness: {metrics['sharpness']:.4f}")
    
    # Demonstrate uncertainty decomposition
    df = pd.DataFrame({
        'method': ['test_method'] * n_samples,
        'prediction': y_pred,
        'variance': uncertainty ** 2
    })
    
    aleatoric, epistemic, total = decompose_uncertainty(df)
    print("\nUncertainty Decomposition:")
    print(f"  Aleatoric Variance: {aleatoric:.4f}")
    print(f"  Epistemic Variance: {epistemic:.4f}")
    print(f"  Total Variance: {total:.4f}")


if __name__ == '__main__':
    main()