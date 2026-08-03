"""
Evaluation metrics and statistical tests for material strength prediction.

Implements MSE, R², and a single-sample t-test comparing CNN squared errors
against the baseline mean squared error (scalar).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from scipy import stats

# Project imports
from utils.config import get_results_dir, get_project_root, set_seed
from utils.logging_config import get_logger, log_operation


def setup_logging() -> logging.Logger:
    """Initialize logger for metrics module."""
    logger = get_logger("metrics")
    # Ensure logger has basic handlers if none exist (for direct script execution)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def load_predictions_from_csv(predictions_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load predictions and true values from a CSV file.
    
    Expected columns: 'image_id', 'predicted_strength', 'true_strength'
    
    Args:
        predictions_path: Path to the predictions CSV file.
        
    Returns:
        Tuple of (y_pred, y_true) as numpy arrays.
    """
    y_pred = []
    y_true = []
    
    with open(predictions_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            y_pred.append(float(row['predicted_strength']))
            y_true.append(float(row['true_strength']))
    
    return np.array(y_pred), np.array(y_true)


def calculate_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Squared Error."""
    return float(np.mean((y_true - y_pred) ** 2))


def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² (coefficient of determination)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - (ss_res / ss_tot))


def single_sample_ttest_squared_errors(
    cnn_sq_errors: np.ndarray,
    baseline_sq_error_scalar: float,
    alpha: float = 0.05
) -> Dict[str, any]:
    """
    Perform a single-sample t-test on squared errors.
    
    Null Hypothesis: Mean(CNN_Squared_Errors) == Baseline_Squared_Error_Scalar
    Alternative: Mean(CNN_Squared_Errors) != Baseline_Squared_Error_Scalar
    
    This compares the distribution of CNN errors against the single scalar
    value of the baseline's squared error (the squared error of the training mean).
    
    Args:
        cnn_sq_errors: Array of squared errors for the CNN model.
        baseline_sq_error_scalar: The squared error of the baseline (training mean).
        alpha: Significance level for the test.
        
    Returns:
        Dictionary with test_type, t_statistic, p_value, and outcome.
    """
    if len(cnn_sq_errors) == 0:
        raise ValueError("cnn_sq_errors array is empty; cannot perform t-test.")
    
    # scipy.stats.ttest_1samp tests if the mean of a distribution differs from a population mean
    # Here, the "population mean" is our baseline scalar error
    t_stat, p_value = stats.ttest_1samp(cnn_sq_errors, baseline_sq_error_scalar)
    
    outcome = "significant" if p_value < alpha else "not_significant"
    
    return {
        "test_type": "single-sample",
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "outcome": outcome
    }


def evaluate_model_performance(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    baseline_mean: float,
    output_path: str,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, any]:
    """
    Evaluate model performance: MSE, R², and single-sample t-test.
    
    Args:
        y_true: True values array.
        y_pred: Predicted values array.
        baseline_mean: The mean of the training set (naive baseline predictor).
        output_path: Path to write the statistical test results JSON.
        alpha: Significance level.
        seed: Random seed for reproducibility (if needed).
        
    Returns:
        Dictionary containing all metrics and test results.
    """
    if seed is not None:
        set_seed(seed)
    
    logger = setup_logging()
    logger.info("Starting model performance evaluation.")
    
    # Calculate errors
    errors = y_pred - y_true
    sq_errors = errors ** 2
    
    # Calculate MSE and R²
    mse = calculate_mse(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)
    
    logger.info(f"MSE: {mse:.6f}")
    logger.info(f"R²: {r2:.6f}")
    
    # Calculate baseline squared error (scalar)
    # Baseline predictor is the mean of training set, so its error on test set is (y_true - baseline_mean)
    # The squared error for the baseline is (y_true - baseline_mean)^2
    # However, FR-005 specifies comparing CNN squared errors against the "squared error of the training set mean"
    # This implies a single scalar: (baseline_mean - baseline_mean)^2? No, that's 0.
    # Re-reading FR-005: "baseline_sq_error_scalar is the squared error of the training set mean"
    # Context implies the baseline predictor is the training mean.
    # The "squared error of the baseline" usually refers to the MSE of the baseline on the test set.
    # But the t-test is single-sample: comparing a distribution (CNN errors) to a scalar.
    # The scalar must be the MSE of the baseline on the test set?
    # Let's interpret "squared error of the training set mean" as the MSE of the baseline predictor on the current test set.
    # Baseline predictions = [baseline_mean] * len(y_true)
    baseline_predictions = np.full_like(y_true, baseline_mean, dtype=float)
    baseline_sq_errors = (y_true - baseline_predictions) ** 2
    baseline_sq_error_scalar = float(np.mean(baseline_sq_errors))
    
    logger.info(f"Baseline MSE (scalar for t-test): {baseline_sq_error_scalar:.6f}")
    
    # Perform single-sample t-test
    ttest_result = single_sample_ttest_squared_errors(sq_errors, baseline_sq_error_scalar, alpha)
    
    logger.info(f"T-test outcome: {ttest_result['outcome']} (p={ttest_result['p_value']:.6f})")
    
    # Prepare output
    results = {
        "mse": mse,
        "r2": r2,
        "baseline_mse": baseline_sq_error_scalar,
        "t_test": ttest_result
    }
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    
    return results


def main():
    """Main entry point for the metrics evaluation script."""
    parser = argparse.ArgumentParser(description="Evaluate model performance with statistical tests.")
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to the CSV file containing predictions (columns: image_id, predicted_strength, true_strength)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write the statistical test results JSON. Defaults to results/statistical_test.json."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for the t-test (default: 0.05)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--baseline-mean",
        type=float,
        required=True,
        help="The mean of the training set yield strengths (naive baseline value)."
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output is None:
        results_dir = get_results_dir()
        output_path = str(Path(results_dir) / "statistical_test.json")
    else:
        output_path = args.output
    
    # Load data
    logger = setup_logging()
    logger.info(f"Loading predictions from {args.predictions}")
    
    try:
        y_pred, y_true = load_predictions_from_csv(args.predictions)
    except FileNotFoundError:
        logger.error(f"Predictions file not found: {args.predictions}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading predictions: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(y_true)} samples.")
    
    # Evaluate
    try:
        results = evaluate_model_performance(
            y_true=y_true,
            y_pred=y_pred,
            baseline_mean=args.baseline_mean,
            output_path=output_path,
            alpha=args.alpha,
            seed=args.seed
        )
        logger.info("Evaluation completed successfully.")
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()