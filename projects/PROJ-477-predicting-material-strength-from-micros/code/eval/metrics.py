"""
Evaluation metrics and statistical testing for material strength prediction.

This module implements MSE, R², and a single-sample t-test on squared errors
to compare the CNN model against a naive baseline predictor.

Plan Override: This task explicitly implements the single-sample t-test as
mandated by Spec FR-005, overriding the paired t-test mentioned in plan.md.
See spec.md FR-005 for the requirement.
"""
import os
import sys
import json
import logging
import argparse
import csv
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Import from project utils
from utils.config import get_results_dir, get_project_root, set_seed, get_seed

# Setup logging
def setup_logging() -> logging.Logger:
    """Setup logger for metrics module."""
    logger = logging.getLogger("metrics")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def load_predictions_from_csv(predictions_path: Path) -> Tuple[List[float], List[float], List[str]]:
    """
    Load predictions and ground truth from a CSV file.

    Expected CSV columns: image_id, prediction, true_value

    Returns:
        Tuple of (predictions, true_values, image_ids) lists.
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    predictions = []
    true_values = []
    image_ids = []

    with open(predictions_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_ids.append(row["image_id"])
            predictions.append(float(row["prediction"]))
            true_values.append(float(row["true_value"]))

    return predictions, true_values, image_ids

def calculate_mse(predictions: List[float], true_values: List[float]) -> float:
    """Calculate Mean Squared Error."""
    if len(predictions) != len(true_values):
        raise ValueError("Predictions and true values must have the same length.")
    if len(predictions) == 0:
        raise ValueError("Cannot calculate MSE on empty lists.")

    squared_errors = [(p - t) ** 2 for p, t in zip(predictions, true_values)]
    return sum(squared_errors) / len(squared_errors)

def calculate_r2(predictions: List[float], true_values: List[float]) -> float:
    """Calculate R-squared (coefficient of determination)."""
    if len(predictions) != len(true_values):
        raise ValueError("Predictions and true values must have the same length.")
    if len(predictions) == 0:
        raise ValueError("Cannot calculate R2 on empty lists.")

    mean_true = sum(true_values) / len(true_values)
    ss_tot = sum((t - mean_true) ** 2 for t in true_values)
    ss_res = sum((t - p) ** 2 for t, p in zip(true_values, predictions))

    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0

    return 1.0 - (ss_res / ss_tot)

def single_sample_ttest_squared_errors(
    cnn_errors: List[float],
    baseline_errors: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a single-sample t-test on squared errors.

    Spec FR-005 Requirement: Compare CNN error to naive baseline error using
    a single-sample t-test. The null hypothesis is that the mean difference
    between CNN squared errors and baseline squared errors is zero.

    This overrides the paired t-test mentioned in plan.md as per spec.md FR-005.

    Args:
        cnn_errors: List of squared errors from the CNN model.
        baseline_errors: List of squared errors from the naive baseline.
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary with test_type, t_statistic, p_value, and outcome.
    """
    if len(cnn_errors) != len(baseline_errors):
        raise ValueError("Error lists must have the same length for comparison.")
    if len(cnn_errors) == 0:
        raise ValueError("Error lists cannot be empty.")

    # Calculate differences (CNN error - Baseline error)
    # We test if the mean difference is significantly different from 0
    differences = [c - b for c, b in zip(cnn_errors, baseline_errors)]
    n = len(differences)
    mean_diff = sum(differences) / n

    # Calculate sample standard deviation of differences
    if n < 2:
        # Cannot compute t-statistic with n=1
        return {
            "test_type": "single-sample",
            "t_statistic": 0.0,
            "p_value": 1.0,
            "outcome": "not_significant",
            "note": "Insufficient samples for t-test (n=1)"
        }

    variance = sum((d - mean_diff) ** 2 for d in differences) / (n - 1)
    std_diff = math.sqrt(variance)

    if std_diff == 0:
        # No variance in differences
        t_statistic = 0.0 if mean_diff == 0 else float('inf') if mean_diff > 0 else float('-inf')
        p_value = 1.0 if t_statistic == 0 else 0.0
    else:
        # Calculate t-statistic
        t_statistic = mean_diff / (std_diff / math.sqrt(n))

        # Approximate p-value using t-distribution
        # For large n, t-distribution approaches normal distribution
        # Using a simple approximation for two-tailed test
        # Note: In a real implementation, we would use scipy.stats.t.sf
        # Here we use a simple approximation for environments without scipy
        abs_t = abs(t_statistic)
        # Approximation for p-value (two-tailed) using standard normal for large n
        # This is a simplified version; for production, use scipy
        if abs_t > 6:
            p_value = 0.0
        else:
            # Simple approximation using error function logic
            # p-value ≈ 2 * (1 - CDF(|t|))
            # Using a polynomial approximation for the normal CDF
            z = abs_t
            t1 = 1.0 / (1.0 + 0.2316419 * z)
            d = 0.3989423 * math.exp(-z * z / 2.0)
            p = d * t1 * (0.3193815 + t1 * (-0.3565638 + t1 * (1.781478 + t1 * (-1.821256 + t1 * 1.330274))))
            p_value = 2.0 * p  # Two-tailed

    # Determine outcome based on alpha
    outcome = "significant" if p_value < alpha else "not_significant"

    return {
        "test_type": "single-sample",
        "t_statistic": t_statistic,
        "p_value": p_value,
        "outcome": outcome
    }

def evaluate_model_performance(
    cnn_predictions: List[float],
    baseline_predictions: List[float],
    true_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Evaluate model performance with MSE, R², and statistical testing.

    Args:
        cnn_predictions: Predictions from the CNN model.
        baseline_predictions: Predictions from the naive baseline.
        true_values: Ground truth values.
        alpha: Significance level for t-test.

    Returns:
        Dictionary containing all metrics and test results.
    """
    if len(cnn_predictions) != len(true_values) or len(baseline_predictions) != len(true_values):
        raise ValueError("All prediction lists must have the same length as true_values.")

    # Calculate squared errors for both models
    cnn_squared_errors = [(p - t) ** 2 for p, t in zip(cnn_predictions, true_values)]
    baseline_squared_errors = [(p - t) ** 2 for p, t in zip(baseline_predictions, true_values)]

    # Calculate metrics
    cnn_mse = sum(cnn_squared_errors) / len(cnn_squared_errors)
    baseline_mse = sum(baseline_squared_errors) / len(baseline_squared_errors)
    cnn_r2 = calculate_r2(cnn_predictions, true_values)
    baseline_r2 = calculate_r2(baseline_predictions, true_values)

    # Perform single-sample t-test on squared errors
    # Spec FR-005: Compare CNN error to baseline error
    t_test_result = single_sample_ttest_squared_errors(
        cnn_squared_errors,
        baseline_squared_errors,
        alpha=alpha
    )

    return {
        "cnn": {
            "mse": cnn_mse,
            "r2": cnn_r2
        },
        "baseline": {
            "mse": baseline_mse,
            "r2": baseline_r2
        },
        "comparison": {
            "mse_improvement": baseline_mse - cnn_mse,
            "r2_improvement": cnn_r2 - baseline_r2
        },
        "statistical_test": t_test_result
    }

def main():
    """
    Main entry point for metrics evaluation script.

    CLI Usage:
        python code/eval/metrics.py --predictions <path_to_predictions_csv>
                                    [--output <path_to_output_json>]
                                    [--alpha <significance_level>]
                                    [--seed <random_seed>]

    Outputs:
        results/statistical_test.json (or custom output path)
            Contains: {test_type, t_statistic, p_value, outcome}
    """
    parser = argparse.ArgumentParser(
        description="Evaluate model performance and perform statistical testing."
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to CSV file with predictions (columns: image_id, prediction, true_value, baseline_prediction)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON file (default: results/statistical_test.json)"
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
        default=None,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    if args.seed is not None:
        set_seed(args.seed)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        results_dir = get_results_dir()
        output_path = results_dir / "statistical_test.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Loading predictions from: {args.predictions}")
        predictions_path = Path(args.predictions)

        # Load data
        # Expected CSV format: image_id, prediction, true_value, baseline_prediction
        # If baseline_prediction is missing, we compute it as the mean of true_values
        image_ids, cnn_preds, true_vals, baseline_preds = [], [], [], []

        with open(predictions_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_ids.append(row["image_id"])
                cnn_preds.append(float(row["prediction"]))
                true_vals.append(float(row["true_value"]))
                if "baseline_prediction" in row:
                    baseline_preds.append(float(row["baseline_prediction"]))

        if not baseline_preds:
            logger.warning("No baseline predictions found. Computing mean baseline.")
            mean_baseline = sum(true_vals) / len(true_vals)
            baseline_preds = [mean_baseline] * len(true_vals)

        if len(cnn_preds) != len(true_vals) or len(baseline_preds) != len(true_vals):
            raise ValueError("Mismatch in number of predictions and true values.")

        logger.info(f"Loaded {len(cnn_preds)} samples.")

        # Evaluate performance
        results = evaluate_model_performance(
            cnn_predictions=cnn_preds,
            baseline_predictions=baseline_preds,
            true_values=true_vals,
            alpha=args.alpha
        )

        # Extract statistical test result for output
        statistical_result = {
            "test_type": results["statistical_test"]["test_type"],
            "t_statistic": results["statistical_test"]["t_statistic"],
            "p_value": results["statistical_test"]["p_value"],
            "outcome": results["statistical_test"]["outcome"]
        }

        # Write output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(statistical_result, f, indent=2)

        logger.info(f"Statistical test results written to: {output_path}")
        logger.info(f"Test Type: {statistical_result['test_type']}")
        logger.info(f"T-Statistic: {statistical_result['t_statistic']:.4f}")
        logger.info(f"P-Value: {statistical_result['p_value']:.4f}")
        logger.info(f"Outcome: {statistical_result['outcome']}")

        # Also log full metrics to results directory
        metrics_path = get_results_dir() / "evaluation_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Full evaluation metrics written to: {metrics_path}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()