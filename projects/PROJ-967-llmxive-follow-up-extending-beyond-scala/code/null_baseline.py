import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
from scipy import stats

def setup_logging() -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def calculate_mean_baseline_metrics(y_true: np.ndarray, y_pred_mean: np.ndarray) -> Dict[str, float]:
    """
    Calculate R² and MAE for a mean predictor baseline.
    
    Args:
        y_true: Ground truth values.
        y_pred_mean: Predictions where every value is the mean of y_true.
        
    Returns:
        Dictionary with 'r2' and 'mae' metrics.
    """
    # R² calculation: 1 - SS_res / SS_tot
    # For a mean predictor, SS_res is exactly SS_tot, so R² should be 0.0.
    # However, we calculate it explicitly to handle floating point nuances.
    ss_res = np.sum((y_true - y_pred_mean) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        r2 = 0.0
    else:
        r2 = 1 - (ss_res / ss_tot)
        
    mae = np.mean(np.abs(y_true - y_pred_mean))
    
    return {'r2': float(r2), 'mae': float(mae)}

def load_rf_results(results_path: str) -> Dict[str, Any]:
    """
    Load Random Forest results from a JSON file.
    
    Args:
        results_path: Path to the results JSON file.
        
    Returns:
        Dictionary containing RF metrics.
    """
    with open(results_path, 'r') as f:
        return json.load(f)

def compare_and_save_results(
    rf_results: Dict[str, Any],
    baseline_results: Dict[str, float],
    y_true: np.ndarray,
    y_pred_rf: np.ndarray,
    output_path: str
) -> None:
    """
    Perform paired t-test between RF residuals and Mean Predictor residuals,
    then save all comparison results.
    
    Args:
        rf_results: RF metrics (R², MAE, etc.).
        baseline_results: Mean predictor metrics.
        y_true: Ground truth values.
        y_pred_rf: RF predictions.
        output_path: Path to save the comparison results.
    """
    # Calculate residuals
    residuals_rf = y_true - y_pred_rf
    mean_val = np.mean(y_true)
    residuals_mean = y_true - mean_val
    
    # Paired t-test on residuals
    # We are testing if the residuals of the RF are significantly different (smaller) than the mean predictor.
    # H0: The mean difference between residuals is 0.
    # H1: The mean difference is not 0 (or specifically, RF residuals are smaller).
    t_stat, p_value = stats.ttest_rel(residuals_mean, residuals_rf)
    
    # Prepare output
    comparison = {
        "rf_metrics": rf_results,
        "baseline_metrics": baseline_results,
        "statistical_test": {
            "test_type": "paired_t_test_residuals",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant_at_0_05": p_value < 0.05,
            "interpretation": "RF significantly better" if p_value < 0.05 else "RF not significantly better"
        },
        "validation_criteria": {
            "r2_positive": rf_results.get('r2', 0) > 0.0,
            "t_test_significant": p_value < 0.05,
            "overall_pass": (rf_results.get('r2', 0) > 0.0) and (p_value < 0.05)
        }
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    logging.info(f"Comparison results saved to {output_path}")
    logging.info(f"RF R²: {rf_results.get('r2'):.4f}, Baseline R²: {baseline_results['r2']:.4f}")
    logging.info(f"T-statistic: {t_stat:.4f}, P-value: {p_value:.4f}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Random Forest model against a mean predictor baseline.")
    parser.add_argument("--rf-results", type=str, required=True, help="Path to RF results JSON (e.g., results/results.json)")
    parser.add_argument("--features", type=str, required=True, help="Path to features JSON (data/processed/features.json)")
    parser.add_argument("--output", type=str, default="results/null_baseline.json", help="Path to save comparison results")
    return parser.parse_args()

def main() -> None:
    logger = setup_logging()
    args = parse_args()
    
    logger.info(f"Loading RF results from {args.rf_results}")
    rf_results = load_rf_results(args.rf_results)
    
    logger.info(f"Loading features from {args.features}")
    with open(args.features, 'r') as f:
        features_data = json.load(f)
    
    # Extract y_true and y_pred from features data
    # Assuming features_data is a list of records with 'fidelity_loss' (y_true) and 'prediction' (y_pred)
    # If the structure is different, adjust accordingly. 
    # Based on typical pipeline: 'fidelity_loss' is the target, 'prediction' is the model output.
    # If 'prediction' is not present in features, we might need to load it from elsewhere, 
    # but for this task, we assume it's available or we reconstruct from RF results if possible.
    # However, the RF results usually contain aggregated metrics, not per-sample predictions.
    # We need per-sample predictions for the t-test. 
    # Let's assume the features.json was updated to include predictions, or we load them from a separate file.
    # Since the task description says "on the *same test set*", we need the test set predictions.
    # If the pipeline doesn't save per-sample predictions, we might need to re-run prediction or store them.
    # For this implementation, we assume the features file contains a 'prediction' key for each sample 
    # that was part of the test set, or we load a separate 'test_predictions.json'.
    # Given the constraints, let's assume the features file has 'fidelity_loss' and 'prediction' for all samples,
    # and the RF results were derived from a subset. We'll filter or use all if not specified.
    # Actually, a more robust approach: The RF results file might not have per-sample data.
    # We need to load the test set predictions. Let's assume there's a file 'results/test_predictions.json'
    # or we extract from the main results if structured that way.
    # To be safe, let's assume the 'features.json' contains the full dataset with 'fidelity_loss' and 'prediction'
    # where 'prediction' is the RF output for the test samples and NaN or None for training samples.
    # But the task says "on the same test set".
    
    # Alternative: If we don't have per-sample predictions, we can't do a paired t-test on residuals.
    # We must have them. Let's assume the pipeline saves them in 'results/test_predictions.json'.
    # If not, we might need to modify train.py to save them. 
    # For this task, I will assume the features file has a 'prediction' field for the relevant samples.
    # If 'prediction' is missing, we raise an error.
    
    y_true_list = []
    y_pred_list = []
    
    for item in features_data:
        if 'fidelity_loss' in item and 'prediction' in item:
            # Only include if prediction is not null/None
            if item['prediction'] is not None:
                y_true_list.append(item['fidelity_loss'])
                y_pred_list.append(item['prediction'])
    
    if not y_true_list:
        raise ValueError("No valid test samples found with 'fidelity_loss' and 'prediction' in features.")
        
    y_true = np.array(y_true_list)
    y_pred_rf = np.array(y_pred_list)
    
    # Calculate mean predictor predictions
    y_pred_mean = np.full_like(y_true, np.mean(y_true))
    
    # Calculate baseline metrics
    baseline_metrics = calculate_mean_baseline_metrics(y_true, y_pred_mean)
    
    # Compare and save
    compare_and_save_results(rf_results, baseline_metrics, y_true, y_pred_rf, args.output)
    
    logger.info("Null baseline comparison completed successfully.")

if __name__ == "__main__":
    main()