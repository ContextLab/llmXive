"""
Sensitivity Analysis Script for Anomaly Detection Thresholds.

This script sweeps decision thresholds to evaluate the impact on
precision, recall, F1-score, and false-positive rates. It outputs
a JSON report containing the metrics for each threshold step.

Task: T026b [US3]
Output: data/results/sensitivity_analysis.json
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD_START = 0.0
THRESHOLD_END = 1.0
THRESHOLD_STEP = 0.05
OUTPUT_FILE = Path("data/results/sensitivity_analysis.json")


def load_predictions(file_path: Path) -> pd.DataFrame:
    """
    Load anomaly predictions from a CSV file.

    Args:
        file_path: Path to the predictions CSV.

    Returns:
        DataFrame with 'score' and 'anomaly' columns.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {file_path}")

    df = pd.read_csv(file_path)
    required_cols = ['score', 'anomaly']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")

    logger.info(f"Loaded predictions from {file_path}: {len(df)} rows")
    return df


def load_ground_truth(file_path: Path) -> pd.DataFrame:
    """
    Load ground truth labels from a CSV file.

    Args:
        file_path: Path to the ground truth CSV.

    Returns:
        DataFrame with 'anomaly' column (binary labels).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")

    df = pd.read_csv(file_path)
    if 'anomaly' not in df.columns:
        raise ValueError(f"Missing 'anomaly' column in ground truth: {file_path}")

    logger.info(f"Loaded ground truth from {file_path}: {len(df)} rows")
    return df


def calculate_metrics_at_threshold(
    scores: pd.Series,
    ground_truth: pd.Series,
    threshold: float
) -> Dict[str, float]:
    """
    Calculate precision, recall, F1, and FPR at a specific threshold.

    Args:
        scores: Predicted anomaly scores.
        ground_truth: Binary ground truth labels (0 or 1).
        threshold: Decision threshold.

    Returns:
        Dictionary containing precision, recall, f1_score, false_positive_rate.
    """
    # Apply threshold to get binary predictions
    predictions = (scores >= threshold).astype(int)

    # True Positives, False Positives, False Negatives, True Negatives
    tp = ((predictions == 1) & (ground_truth == 1)).sum()
    fp = ((predictions == 1) & (ground_truth == 0)).sum()
    fn = ((predictions == 0) & (ground_truth == 1)).sum()
    tn = ((predictions == 0) & (ground_truth == 0)).sum()

    # Precision
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    # Recall
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # F1 Score
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    # False Positive Rate
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "false_positive_rate": fpr
    }


def sweep_thresholds(
    scores: pd.Series,
    ground_truth: pd.Series,
    start: float = THRESHOLD_START,
    end: float = THRESHOLD_END,
    step: float = THRESHOLD_STEP
) -> List[Dict[str, Any]]:
    """
    Sweep through thresholds and calculate metrics for each.

    Args:
        scores: Predicted anomaly scores.
        ground_truth: Binary ground truth labels.
        start: Starting threshold value.
        end: Ending threshold value.
        step: Step size for threshold increment.

    Returns:
        List of dictionaries containing threshold and metrics.
    """
    results = []
    current = start
    while current <= end + 1e-9:  # Small epsilon for float comparison
        metrics = calculate_metrics_at_threshold(scores, ground_truth, current)
        result_entry = {
            "threshold": round(current, 2),
            **metrics
        }
        results.append(result_entry)
        current += step

    return results


def find_optimal_threshold(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find the threshold that maximizes F1-score.

    Args:
        results: List of threshold sweep results.

    Returns:
        Dictionary containing the optimal threshold and its metrics.
    """
    if not results:
        raise ValueError("No results provided to find optimal threshold")

    best = max(results, key=lambda x: x['f1_score'])
    logger.info(f"Optimal threshold: {best['threshold']} with F1: {best['f1_score']:.4f}")
    return best


def run_analysis(
    predictions_path: Path,
    ground_truth_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis pipeline.

    Args:
        predictions_path: Path to predictions CSV.
        ground_truth_path: Path to ground truth CSV.
        output_path: Path to save the output JSON.

    Returns:
        Dictionary containing the full analysis results.
    """
    # Load data
    predictions_df = load_predictions(predictions_path)
    ground_truth_df = load_ground_truth(ground_truth_path)

    # Ensure alignment (assume same index/order as per pipeline design)
    if len(predictions_df) != len(ground_truth_df):
        raise ValueError(
            f"Length mismatch: predictions ({len(predictions_df)}) "
            f"vs ground truth ({len(ground_truth_df)})"
        )

    scores = predictions_df['score']
    ground_truth = ground_truth_df['anomaly']

    # Sweep thresholds
    logger.info(f"Sweeping thresholds from {THRESHOLD_START} to {THRESHOLD_END} step {THRESHOLD_STEP}")
    sweep_results = sweep_thresholds(scores, ground_truth)

    # Find optimal
    optimal = find_optimal_threshold(sweep_results)

    # Compile final report
    report = {
        "analysis_config": {
            "threshold_start": THRESHOLD_START,
            "threshold_end": THRESHOLD_END,
            "threshold_step": THRESHOLD_STEP,
            "optimization_metric": "f1_score"
        },
        "optimal_threshold": optimal,
        "sweep_results": sweep_results
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    return report


def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for the sensitivity analysis script.

    Args:
        args: Command line arguments (optional).
    """
    parser = argparse.ArgumentParser(
        description="Sweep decision thresholds for anomaly detection evaluation."
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/results/bayesian_predictions.csv",
        help="Path to the predictions CSV file."
    )
    parser.add_argument(
        "--ground_truth",
        type=str,
        default="data/processed/ground_truth.csv",
        help="Path to the ground truth CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/sensitivity_analysis.json",
        help="Path to save the sensitivity analysis JSON report."
    )

    parsed_args = parser.parse_args() if args is None else args

    try:
        run_analysis(
            predictions_path=Path(parsed_args.predictions),
            ground_truth_path=Path(parsed_args.ground_truth),
            output_path=Path(parsed_args.output)
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()