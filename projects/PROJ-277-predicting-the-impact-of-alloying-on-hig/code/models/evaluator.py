import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats

from config import get_config_from_args
from utils.logger import get_logger, log_gap_analysis_result

logger = get_logger(__name__)


def calculate_statistical_power(n: int, effect_size: float = 0.5, alpha: float = 0.05) -> float:
    """
    Calculate the statistical power for a paired t-test given sample size and effect size.
    
    Args:
        n: Sample size
        effect_size: Cohen's d (standardized effect size)
        alpha: Significance level
        
    Returns:
        Statistical power (probability of correctly rejecting null hypothesis)
    """
    if n < 2:
        return 0.0
    
    # Approximation for power of paired t-test
    # Using non-central t-distribution approximation
    df = n - 1
    noncent_param = effect_size * np.sqrt(n)
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power calculation (approximation)
    # Power = P(T > t_crit | noncent_param) + P(T < -t_crit | noncent_param)
    power = 1 - stats.nct.cdf(t_crit, df, noncent_param) + stats.nct.cdf(-t_crit, df, noncent_param)
    
    return float(power)


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Root Mean Squared Error.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        RMSE value
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        return 0.0
        
    mse = np.mean((np.array(y_true) - np.array(y_pred)) ** 2)
    return float(np.sqrt(mse))


def identify_sensitive_samples(
    errors: np.ndarray,
    sample_ids: List[str],
    threshold_multiplier: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Identify samples with 'High Microstructural Sensitivity'.
    
    A sample is considered highly sensitive if its absolute prediction error
    (composition-only model) exceeds `threshold_multiplier` times the median
    absolute error of the dataset.
    
    Args:
        errors: Array of prediction errors (y_true - y_pred)
        sample_ids: List of sample identifiers corresponding to errors
        threshold_multiplier: Multiplier for median error to define sensitivity
        
    Returns:
        List of dictionaries containing sensitive sample details:
        - id: Sample ID
        - error: Absolute error value
        - median_error: Median error of the dataset
        - ratio: Ratio of sample error to median error
    """
    if len(errors) == 0:
        logger.warning("No errors provided to identify_sensitive_samples")
        return []
    
    abs_errors = np.abs(errors)
    median_error = np.median(abs_errors)
    
    if median_error == 0:
        # If median is 0, we can't calculate a ratio. 
        # Flag samples with any non-zero error as sensitive if we have at least one.
        # This is an edge case handling.
        sensitive = []
        for i, (err, sid) in enumerate(zip(abs_errors, sample_ids)):
            if err > 0:
                sensitive.append({
                    "id": sid,
                    "error": float(err),
                    "median_error": 0.0,
                    "ratio": float('inf')
                })
        return sensitive
    
    threshold = median_error * threshold_multiplier
    sensitive_indices = np.where(abs_errors > threshold)[0]
    
    sensitive_samples = []
    for idx in sensitive_indices:
        sensitive_samples.append({
            "id": sample_ids[idx],
            "error": float(abs_errors[idx]),
            "median_error": float(median_error),
            "ratio": float(abs_errors[idx] / median_error)
        })
    
    logger.info(f"Identified {len(sensitive_samples)} highly sensitive samples "
                f"(threshold: {threshold_multiplier}x median error = {threshold:.4f})")
    
    return sensitive_samples


def evaluate_gap_analysis(
    composition_only_errors: np.ndarray,
    augmented_errors: np.ndarray,
    sample_ids: List[str]
) -> Dict[str, Any]:
    """
    Perform comparative error analysis between composition-only and augmented models.
    
    Args:
        composition_only_errors: Errors from composition-only model
        augmented_errors: Errors from model augmented with microstructural features
        sample_ids: List of sample identifiers
        
    Returns:
        Dictionary containing:
        - composition_only_rmse: RMSE of composition-only model
        - augmented_rmse: RMSE of augmented model
        - error_reduction_pct: Percentage reduction in RMSE
        - sensitive_samples: List of high sensitivity samples from composition-only errors
        - is_conclusive: Boolean indicating if analysis is statistically conclusive
    """
    if len(composition_only_errors) != len(augmented_errors):
        raise ValueError("Error arrays must have the same length")
    
    comp_rmse = calculate_rmse(np.zeros_like(composition_only_errors), composition_only_errors)
    # Note: RMSE is calculated as sqrt(mean((y_true - y_pred)^2)). 
    # If we pass errors directly (y_true - y_pred), then RMSE(errors, 0) is the same as RMSE(y_true, y_pred).
    # However, standard practice is to pass y_true and y_pred. Here we assume errors are already y_true - y_pred.
    # So RMSE = sqrt(mean(errors^2)).
    comp_rmse = float(np.sqrt(np.mean(composition_only_errors ** 2)))
    aug_rmse = float(np.sqrt(np.mean(augmented_errors ** 2)))
    
    if comp_rmse == 0:
        error_reduction_pct = 0.0
    else:
        error_reduction_pct = ((comp_rmse - aug_rmse) / comp_rmse) * 100.0
    
    # Identify sensitive samples based on composition-only errors
    sensitive_samples = identify_sensitive_samples(composition_only_errors, sample_ids)
    
    # Check statistical power (n < 50 is inconclusive per T023)
    n = len(composition_only_errors)
    is_conclusive = n >= 50
    
    if not is_conclusive:
        logger.warning(f"Gap analysis is inconclusive: sample size {n} < 50")
    
    return {
        "composition_only_rmse": comp_rmse,
        "augmented_rmse": aug_rmse,
        "error_reduction_pct": error_reduction_pct,
        "sensitive_samples": sensitive_samples,
        "is_conclusive": is_conclusive,
        "sample_count": n
    }


def generate_predictions(
    model,
    X: np.ndarray,
    y_true: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Generate predictions and optionally calculate errors.
    
    Args:
        model: Trained sklearn model
        X: Feature matrix
        y_true: Optional true values for error calculation
        
    Returns:
        Dictionary containing predictions and optionally errors
    """
    predictions = model.predict(X)
    result = {
        "predictions": predictions
    }
    
    if y_true is not None:
        errors = y_true - predictions
        result["errors"] = errors
        result["rmse"] = calculate_rmse(y_true, predictions)
    
    return result


def main():
    """
    Main entry point for evaluator module.
    This function orchestrates the gap analysis evaluation workflow.
    """
    args = get_config_from_args()
    
    logger.info("Starting gap analysis evaluation")
    
    # Load processed data (assuming it exists from previous steps)
    # In a real pipeline, this would be passed via arguments or loaded from disk
    # For now, we demonstrate the logic structure
    
    # Example data loading (placeholder for real implementation)
    # data_path = os.path.join(args.data_dir, "processed", "alloy_data.csv")
    # if not os.path.exists(data_path):
    #     logger.error(f"Data file not found: {data_path}")
    #     sys.exit(1)
    
    # df = pd.read_csv(data_path)
    # X = df.drop(['observed_weight_gain', 'sample_id'], axis=1).values
    # y = df['observed_weight_gain'].values
    # ids = df['sample_id'].tolist()
    
    # Simulated for demonstration of logic
    logger.info("Evaluator module loaded. Ready to perform gap analysis.")
    
    # The actual evaluation would happen here when called from main.py
    # or via a specific CLI command
    
    logger.info("Gap analysis evaluation complete.")


if __name__ == "__main__":
    main()