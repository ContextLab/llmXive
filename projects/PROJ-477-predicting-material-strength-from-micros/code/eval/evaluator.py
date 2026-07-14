"""
Evaluator module implementing the Null Hypothesis Protocol.

This module orchestrates the evaluation of model performance against baselines
and enforces the null hypothesis rejection criteria.

Task T025: If R² < 0.2, write results/null_hypothesis_report.json and raise SystemExit(1).
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import from existing project modules
from utils.config import get_project_root, get_results_dir, set_seed, get_seed
from eval.metrics import (
    calculate_mse, 
    calculate_r2, 
    single_sample_ttest_squared_errors,
    load_predictions_from_csv,
    evaluate_model_performance
)

# Setup logging
logger = logging.getLogger(__name__)

NULL_HYPOTHESIS_THRESHOLD = 0.2


def write_null_hypothesis_report(
    r2_value: float, 
    threshold: float, 
    status: str,
    results_dir: Path
) -> Path:
    """
    Write the null hypothesis report to JSON.
    
    Args:
        r2_value: The calculated R² value
        threshold: The threshold used for comparison
        status: The status string ('rejected' or 'not_rejected')
        results_dir: Directory to write the report to
        
    Returns:
        Path to the written report file
    """
    report = {
        "status": status,
        "r2_value": float(r2_value),
        "threshold": float(threshold)
    }
    
    report_path = results_dir / "null_hypothesis_report.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Null hypothesis report written to {report_path}")
    return report_path


def evaluate_and_check_null_hypothesis(
    predictions_path: Path,
    ground_truth_path: Path,
    baseline_predictions_path: Optional[Path] = None,
    results_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Evaluate model performance and enforce null hypothesis protocol.
    
    If R² < 0.2:
        1. Write results/null_hypothesis_report.json with status='not_rejected'
        2. Raise SystemExit(1)
        
    If R² >= 0.2:
        1. Write results/null_hypothesis_report.json with status='rejected'
        2. Continue evaluation normally
        
    Args:
        predictions_path: Path to model predictions CSV
        ground_truth_path: Path to ground truth labels CSV
        baseline_predictions_path: Optional path to baseline predictions for comparison
        results_dir: Directory for output reports
        
    Returns:
        Dictionary containing evaluation metrics
        
    Raises:
        SystemExit: If R² < threshold (null hypothesis not rejected)
    """
    if results_dir is None:
        results_dir = get_results_dir()
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load predictions and ground truth
    predictions, ground_truth = load_predictions_from_csv(
        predictions_path, 
        ground_truth_path
    )
    
    logger.info(f"Loaded {len(predictions)} predictions for evaluation")
    
    # Calculate metrics
    mse = calculate_mse(ground_truth, predictions)
    r2 = calculate_r2(ground_truth, predictions)
    
    logger.info(f"Evaluation Results: MSE={mse:.4f}, R²={r2:.4f}")
    
    # Null Hypothesis Protocol (T025)
    if r2 < NULL_HYPOTHESIS_THRESHOLD:
        logger.warning(
            f"R² ({r2:.4f}) is below threshold ({NULL_HYPOTHESIS_THRESHOLD}). "
            "Null hypothesis NOT rejected."
        )
        
        # Write report with status 'not_rejected'
        report_path = write_null_hypothesis_report(
            r2_value=r2,
            threshold=NULL_HYPOTHESIS_THRESHOLD,
            status="not_rejected",
            results_dir=results_dir
        )
        
        # Raise SystemExit(1) as per requirements
        raise SystemExit(1)
    
    # R² >= threshold - null hypothesis rejected
    logger.info(
        f"R² ({r2:.4f}) meets/exceeds threshold ({NULL_HYPOTHESIS_THRESHOLD}). "
        "Null hypothesis REJECTED."
    )
    
    # Write report with status 'rejected'
    report_path = write_null_hypothesis_report(
        r2_value=r2,
        threshold=NULL_HYPOTHESIS_THRESHOLD,
        status="rejected",
        results_dir=results_dir
    )
    
    # Prepare results dictionary
    results = {
        "mse": float(mse),
        "r2": float(r2),
        "null_hypothesis_rejected": True,
        "threshold": NULL_HYPOTHESIS_THRESHOLD,
        "predictions_file": str(predictions_path),
        "ground_truth_file": str(ground_truth_path)
    }
    
    # Add baseline comparison if available
    if baseline_predictions_path and baseline_predictions_path.exists():
        baseline_predictions, _ = load_predictions_from_csv(
            baseline_predictions_path,
            ground_truth_path
        )
        baseline_mse = calculate_mse(ground_truth, baseline_predictions)
        baseline_r2 = calculate_r2(ground_truth, baseline_predictions)
        
        results["baseline_mse"] = float(baseline_mse)
        results["baseline_r2"] = float(baseline_r2)
        
        # Perform t-test on squared errors
        t_stat, p_value = single_sample_ttest_squared_errors(
            ground_truth, predictions, baseline_predictions
        )
        results["t_statistic"] = float(t_stat)
        results["p_value"] = float(p_value)
        results["t_test_significant"] = p_value < 0.05
    
    return results


def main():
    """
    Main entry point for the evaluator script.
    
    Usage:
        python code/eval/evaluator.py --predictions <path> --ground_truth <path> [--baseline <path>]
    """
    parser = argparse.ArgumentParser(
        description="Evaluate model performance and enforce null hypothesis protocol"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to model predictions CSV file"
    )
    parser.add_argument(
        "--ground_truth",
        type=str,
        required=True,
        help="Path to ground truth labels CSV file"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        required=False,
        help="Optional path to baseline predictions CSV file"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory to write results (default: project results dir)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set seed
    set_seed(args.seed)
    
    # Resolve paths
    predictions_path = Path(args.predictions)
    ground_truth_path = Path(args.ground_truth)
    baseline_path = Path(args.baseline) if args.baseline else None
    
    if args.results_dir:
        results_dir = Path(args.results_dir)
    else:
        results_dir = get_results_dir()
    
    # Validate input files exist
    if not predictions_path.exists():
        logger.error(f"Predictions file not found: {predictions_path}")
        sys.exit(1)
    
    if not ground_truth_path.exists():
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        sys.exit(1)
    
    if baseline_path and not baseline_path.exists():
        logger.warning(f"Baseline file not found: {baseline_path}")
        baseline_path = None
    
    try:
        # Run evaluation with null hypothesis check
        results = evaluate_and_check_null_hypothesis(
            predictions_path=predictions_path,
            ground_truth_path=ground_truth_path,
            baseline_predictions_path=baseline_path,
            results_dir=results_dir
        )
        
        # Write final results to JSON
        final_report_path = results_dir / "evaluation_report.json"
        with open(final_report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Evaluation complete. Results written to {final_report_path}")
        print(json.dumps(results, indent=2))
        
    except SystemExit as e:
        # Re-raise SystemExit from null hypothesis protocol
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()