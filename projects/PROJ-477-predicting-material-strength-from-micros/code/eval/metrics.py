"""
Evaluation metrics module for Material Strength Prediction.

Implements MSE, R², and statistical significance testing (single-sample t-test)
comparing CNN squared errors against baseline squared errors.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from utils.config import get_results_dir, get_project_root, set_seed
from utils.logging_config import get_logger, log_metric

# Configure logger
logger = get_logger(__name__)


def calculate_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Mean Squared Error.

    Args:
        y_true: Ground truth values (numpy array)
        y_pred: Predicted values (numpy array)

    Returns:
        MSE value (float)
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    squared_errors = (y_true - y_pred) ** 2
    return float(np.mean(squared_errors))


def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (coefficient of determination).

    Args:
        y_true: Ground truth values (numpy array)
        y_pred: Predicted values (numpy array)

    Returns:
        R² value (float)
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        # All true values are the same; perfect prediction or no variance
        if ss_res == 0:
            return 1.0
        return 0.0

    return float(1.0 - (ss_res / ss_tot))


def single_sample_ttest_squared_errors(
    y_true: np.ndarray,
    y_pred_cnn: np.ndarray,
    y_pred_baseline: np.ndarray,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a single-sample t-test on squared errors.

    The test compares the squared errors of the CNN model against the squared
    errors of the baseline model. The null hypothesis is that the mean difference
    (baseline_sq_error - cnn_sq_error) is zero.

    Alternative hypothesis (one-tailed): CNN has significantly lower error
    (i.e., mean difference > 0).

    Args:
        y_true: Ground truth values
        y_pred_cnn: CNN model predictions
        y_pred_baseline: Baseline model predictions
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary containing:
            - t_statistic: t-value
            - p_value: p-value for the one-tailed test
            - mean_difference: mean(baseline_sq_error - cnn_sq_error)
            - is_significant: True if p_value < alpha
            - confidence_interval: 95% CI for the mean difference
    """
    if len(y_true) != len(y_pred_cnn) or len(y_true) != len(y_pred_baseline):
        raise ValueError("All input arrays must have the same length")
    
    if len(y_true) < 2:
        raise ValueError("Need at least 2 samples for t-test")

    # Calculate squared errors
    cnn_sq_errors = (y_true - y_pred_cnn) ** 2
    baseline_sq_errors = (y_true - y_pred_baseline) ** 2

    # Difference: baseline - cnn (positive means CNN is better)
    differences = baseline_sq_errors - cnn_sq_errors

    # Single-sample t-test against zero
    # We test if the mean difference is significantly greater than 0
    t_stat, p_value_two_tailed = stats.ttest_1samp(differences, 0.0)

    # Convert to one-tailed p-value (we expect CNN to be better, so difference > 0)
    # If t_stat > 0, the one-tailed p-value is half the two-tailed
    # If t_stat < 0, the one-tailed p-value is 1 - (two_tailed / 2)
    if t_stat > 0:
        p_value_one_tailed = p_value_two_tailed / 2.0
    else:
        p_value_one_tailed = 1.0 - (p_value_two_tailed / 2.0)

    # Calculate 95% confidence interval for the mean difference
    n = len(differences)
    mean_diff = np.mean(differences)
    std_err = np.std(differences, ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, df=n-1)  # Two-tailed 95% CI
    ci_lower = mean_diff - (t_crit * std_err)
    ci_upper = mean_diff + (t_crit * std_err)

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value_one_tailed),
        "mean_difference": float(mean_diff),
        "is_significant": bool(p_value_one_tailed < alpha),
        "alpha": alpha,
        "confidence_interval": {
            "lower": float(ci_lower),
            "upper": float(ci_upper)
        },
        "n_samples": n,
        "test_type": "single_sample_ttest",
        "hypothesis": "CNN error < Baseline error (one-tailed)"
    }


def load_predictions_from_csv(
    predictions_path: Path
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load predictions from a CSV file containing columns:
    image_id, true_strength, cnn_prediction, baseline_prediction

    Args:
        predictions_path: Path to the predictions CSV file

    Returns:
        Tuple of (y_true, y_pred_cnn, y_pred_baseline) as numpy arrays
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    y_true_list = []
    y_pred_cnn_list = []
    y_pred_baseline_list = []

    with open(predictions_path, 'r') as f:
        # Skip header
        header = f.readline().strip().split(',')
        
        # Validate columns
        required_cols = {'image_id', 'true_strength', 'cnn_prediction', 'baseline_prediction'}
        if not required_cols.issubset(set(header)):
            missing = required_cols - set(header)
            raise ValueError(f"Missing required columns: {missing}")
        
        true_idx = header.index('true_strength')
        cnn_idx = header.index('cnn_prediction')
        baseline_idx = header.index('baseline_prediction')

        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < max(true_idx, cnn_idx, baseline_idx) + 1:
                continue
            
            try:
                y_true_list.append(float(parts[true_idx]))
                y_pred_cnn_list.append(float(parts[cnn_idx]))
                y_pred_baseline_list.append(float(parts[baseline_idx]))
            except ValueError:
                logger.warning(f"Skipping invalid row: {line}")
                continue

    if len(y_true_list) == 0:
        raise ValueError("No valid data rows found in predictions file")

    return (
        np.array(y_true_list, dtype=np.float64),
        np.array(y_pred_cnn_list, dtype=np.float64),
        np.array(y_pred_baseline_list, dtype=np.float64)
    )


def evaluate_model_performance(
    predictions_path: Path,
    output_path: Optional[Path] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Main evaluation function that computes all metrics and statistical tests.

    Args:
        predictions_path: Path to predictions CSV
        output_path: Path to write evaluation report (JSON). If None, uses default.
        alpha: Significance level for t-test

    Returns:
        Dictionary containing all evaluation metrics and test results
    """
    logger.info(f"Loading predictions from: {predictions_path}")
    y_true, y_pred_cnn, y_pred_baseline = load_predictions_from_csv(predictions_path)
    logger.info(f"Loaded {len(y_true)} samples for evaluation")

    # Calculate metrics
    mse_cnn = calculate_mse(y_true, y_pred_cnn)
    mse_baseline = calculate_mse(y_true, y_pred_baseline)
    r2_cnn = calculate_r2(y_true, y_pred_cnn)
    r2_baseline = calculate_r2(y_true, y_pred_baseline)

    logger.info(f"CNN - MSE: {mse_cnn:.4f}, R²: {r2_cnn:.4f}")
    logger.info(f"Baseline - MSE: {mse_baseline:.4f}, R²: {r2_baseline:.4f}")

    # Perform statistical test
    ttest_results = single_sample_ttest_squared_errors(
        y_true, y_pred_cnn, y_pred_baseline, alpha=alpha
    )

    # Compile results
    results = {
        "metrics": {
            "cnn": {
                "mse": mse_cnn,
                "r2": r2_cnn
            },
            "baseline": {
                "mse": mse_baseline,
                "r2": r2_baseline
            }
        },
        "statistical_test": ttest_results,
        "summary": {
            "mse_improvement": float(mse_baseline - mse_cnn),
            "mse_improvement_pct": float((mse_baseline - mse_cnn) / mse_baseline * 100) if mse_baseline > 0 else 0.0,
            "r2_improvement": float(r2_cnn - r2_baseline),
            "statistically_significant": ttest_results["is_significant"]
        },
        "sample_size": len(y_true),
        "alpha": alpha
    }

    # Write output if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Evaluation report written to: {output_path}")

    return results


def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Evaluate model performance with statistical testing"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to predictions CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON report (default: results/evaluation_report.json)"
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
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()
    set_seed(args.seed)

    # Setup logging
    log_metric("evaluation_start", 1)

    predictions_path = Path(args.predictions)
    
    if args.output:
        output_path = Path(args.output)
    else:
        results_dir = get_results_dir()
        output_path = results_dir / "evaluation_report.json"

    try:
        results = evaluate_model_performance(
            predictions_path, 
            output_path, 
            alpha=args.alpha
        )
        
        # Log key metrics
        log_metric("cnn_mse", results["metrics"]["cnn"]["mse"])
        log_metric("cnn_r2", results["metrics"]["cnn"]["r2"])
        log_metric("baseline_mse", results["metrics"]["baseline"]["mse"])
        log_metric("baseline_r2", results["metrics"]["baseline"]["r2"])
        log_metric("statistical_significance", 1 if results["summary"]["statistically_significant"] else 0)

        print(f"Evaluation complete. Report saved to: {output_path}")
        print(f"CNN MSE: {results['metrics']['cnn']['mse']:.4f}, R²: {results['metrics']['cnn']['r2']:.4f}")
        print(f"Baseline MSE: {results['metrics']['baseline']['mse']:.4f}, R²: {results['metrics']['baseline']['r2']:.4f}")
        print(f"Statistically significant (α={args.alpha}): {results['summary']['statistically_significant']}")
        
        return 0

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        log_metric("evaluation_error", 1)
        return 1


if __name__ == "__main__":
    sys.exit(main())