"""Evaluation metrics for material strength prediction.

Implements MSE, R², and single-sample t-test on squared errors comparing
CNN performance against a naive baseline (FR-005, SC-002).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
from scipy import stats

# Import project utilities from the API surface
from utils.config import get_results_dir, get_project_root, set_seed
from utils.logging_config import get_logger, log_operation, ReproducibilityLogger, LogEntry


def setup_logging() -> ReproducibilityLogger:
    """Setup logging for the metrics evaluation script."""
    logger = get_logger("metrics_eval")
    return logger


def load_predictions_from_csv(path: Path) -> Tuple[List[float], List[float]]:
    """Load predictions and true values from a CSV file.

    Expected CSV columns: 'image_id', 'prediction', 'true_value'

    Args:
        path: Path to the CSV file.

    Returns:
        Tuple of (predictions, true_values) lists.
    """
    predictions = []
    true_values = []

    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {path}")

    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            predictions.append(float(row['prediction']))
            true_values.append(float(row['true_value']))

    return predictions, true_values


def calculate_mse(y_true: List[float], y_pred: List[float]) -> float:
    """Calculate Mean Squared Error.

    Args:
        y_true: List of true values.
        y_pred: List of predicted values.

    Returns:
        MSE value.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    errors = np.array(y_true) - np.array(y_pred)
    mse = float(np.mean(errors ** 2))
    return mse


def calculate_r2(y_true: List[float], y_pred: List[float]) -> float:
    """Calculate R² (coefficient of determination).

    Args:
        y_true: List of true values.
        y_pred: List of predicted values.

    Returns:
        R² value.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    ss_res = np.sum((y_true_arr - y_pred_arr) ** 2)
    ss_tot = np.sum((y_true_arr - np.mean(y_true_arr)) ** 2)

    if ss_tot == 0:
        return 0.0 if ss_res == 0 else -1.0

    r2 = float(1 - (ss_res / ss_tot))
    return r2


def single_sample_ttest_squared_errors(
    cnn_sq_errors: List[float],
    baseline_sq_error_scalar: float,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Perform single-sample t-test on squared errors.

    Compares the distribution of CNN squared errors against a single scalar
    value (the squared error of the baseline mean predictor).

    Null Hypothesis: Mean(CNN_Error) == Baseline_Error

    Args:
        cnn_sq_errors: List of squared errors from the CNN model.
        baseline_sq_error_scalar: Single scalar value representing the
            squared error of the naive baseline (mean of training set).
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary with test results:
            - test_type: "single-sample"
            - t_statistic: float
            - p_value: float
            - outcome: "significant" if p < alpha, else "not_significant"
    """
    if len(cnn_sq_errors) == 0:
        raise ValueError("cnn_sq_errors cannot be empty")

    cnn_sq_errors_arr = np.array(cnn_sq_errors)

    # Perform single-sample t-test
    t_stat, p_value = stats.ttest_1samp(cnn_sq_errors_arr, baseline_sq_error_scalar)

    # Determine outcome
    outcome = "significant" if p_value < alpha else "not_significant"

    return {
        "test_type": "single-sample",
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "outcome": outcome,
        "alpha": alpha
    }


def evaluate_model_performance(
    predictions_path: Path,
    baseline_mse: float,
    output_path: Path,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """Evaluate model performance: MSE, R², and statistical significance test.

    Args:
        predictions_path: Path to CSV with 'prediction' and 'true_value' columns.
        baseline_mse: The MSE of the naive baseline (mean of training set).
        output_path: Path to write the statistical_test.json output.
        alpha: Significance level for the t-test.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing all evaluation metrics and test results.
    """
    set_seed(seed)
    logger = setup_logging()

    log_operation("evaluate_model_performance", 
                predictions=str(predictions_path), 
                baseline_mse=baseline_mse,
                alpha=alpha)

    # Load data
    predictions, true_values = load_predictions_from_csv(predictions_path)

    # Calculate metrics
    mse = calculate_mse(true_values, predictions)
    r2 = calculate_r2(true_values, predictions)

    # Calculate squared errors for CNN
    cnn_sq_errors = [(t - p) ** 2 for t, p in zip(true_values, predictions)]

    # Calculate squared error of baseline (scalar)
    # The baseline predictor always predicts the mean, so its error is constant
    # for all samples: (true_value - baseline_mean)^2. However, for the
    # single-sample test as specified in FR-005, we compare the distribution
    # of CNN errors against the SINGLE scalar value of the baseline MSE.
    # This is the conservative interpretation mandated by the spec.
    baseline_sq_error_scalar = baseline_mse

    # Perform single-sample t-test
    test_result = single_sample_ttest_squared_errors(
        cnn_sq_errors, 
        baseline_sq_error_scalar, 
        alpha
    )

    # Compile results
    results = {
        "mse": mse,
        "r2": r2,
        "n_samples": len(predictions),
        "test_result": test_result,
        "baseline_mse": baseline_mse
    }

    # Write output to JSON file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    log_operation("evaluation_complete", 
                mse=mse, 
                r2=r2, 
                p_value=test_result["p_value"],
                outcome=test_result["outcome"])

    return results


def main():
    """Main entry point for the metrics evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate model performance with statistical testing"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to CSV file with 'prediction' and 'true_value' columns"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON file (default: results/statistical_test.json)"
    )
    parser.add_argument(
        "--baseline-mse",
        type=float,
        default=None,
        help="MSE of the naive baseline (required if not in predictions file metadata)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for t-test (default: 0.05)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = get_project_root()
    predictions_path = Path(args.predictions)
    
    if not predictions_path.is_absolute():
        predictions_path = project_root / predictions_path

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = project_root / output_path
    else:
        output_path = get_results_dir() / "statistical_test.json"

    # Determine baseline MSE
    baseline_mse = args.baseline_mse
    if baseline_mse is None:
        # Try to load from baseline_stats.json if available
        baseline_stats_path = get_results_dir() / "baseline_stats.json"
        if baseline_stats_path.exists():
            with open(baseline_stats_path, 'r') as f:
                baseline_data = json.load(f)
                baseline_mse = baseline_data.get("mse")
            if baseline_mse is None:
                raise ValueError(
                    "Baseline MSE not provided via --baseline-mse and not found "
                    "in results/baseline_stats.json. Please provide it explicitly."
                )
        else:
            raise ValueError(
                "Baseline MSE not provided via --baseline-mse and "
                "results/baseline_stats.json does not exist. "
                "Please run the baseline predictor first or provide --baseline-mse."
            )

    # Run evaluation
    try:
        results = evaluate_model_performance(
            predictions_path=predictions_path,
            baseline_mse=baseline_mse,
            output_path=output_path,
            alpha=args.alpha,
            seed=args.seed
        )
        
        print(f"Evaluation complete.")
        print(f"MSE: {results['mse']:.4f}")
        print(f"R²: {results['r2']:.4f}")
        print(f"T-test outcome: {results['test_result']['outcome']} (p={results['test_result']['p_value']:.4f})")
        print(f"Results written to: {output_path}")
        
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    main()