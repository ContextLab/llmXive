"""
Sensitivity Analysis Script for Anomaly Detection Thresholds.

This script performs a sweep over decision thresholds to analyze the
trade-off between false positive and false negative rates. It identifies
optimal thresholds based on different criteria (e.g., F1-score, specificity).

Author: Research Team
Date: 2026-04-29
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_predictions(path: Path) -> pd.DataFrame:
    """
    Load predictions from a CSV file.

    Args:
        path (Path): Path to the predictions CSV file.

    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {path}")

    df = pd.read_csv(path)
    required_cols = ['is_anomaly']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Predictions file must contain columns: {required_cols}")

    logger.info(f"Loaded predictions from {path}: {len(df)} rows")
    return df


def load_ground_truth(path: Path) -> pd.DataFrame:
    """
    Load ground truth labels from a CSV file.

    Args:
        path (Path): Path to the ground truth CSV file.

    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")

    df = pd.read_csv(path)
    required_cols = ['is_anomaly']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Ground truth file must contain columns: {required_cols}")

    logger.info(f"Loaded ground truth from {path}: {len(df)} rows")
    return df


def sweep_thresholds(
    scores: np.ndarray,
    ground_truth: np.ndarray,
    thresholds: List[float]
) -> List[Dict[str, Any]]:
    """
    Sweep over thresholds and calculate metrics for each.

    Args:
        scores (np.ndarray): Anomaly scores or reconstruction errors.
        ground_truth (np.ndarray): True binary labels.
        thresholds (List[float]): List of thresholds to evaluate.

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing metrics for each threshold.
    """
    results = []

    for thresh in thresholds:
        predictions = (scores >= thresh).astype(int)

        tp = np.sum((ground_truth == 1) & (predictions == 1))
        fp = np.sum((ground_truth == 0) & (predictions == 1))
        tn = np.sum((ground_truth == 0) & (predictions == 0))
        fn = np.sum((ground_truth == 1) & (predictions == 0))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        results.append({
            'threshold': thresh,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'specificity': specificity,
            'fpr': fpr,
            'fnr': fnr,
            'tp': int(tp),
            'fp': int(fp),
            'tn': int(tn),
            'fn': int(fn)
        })

    logger.info(f"Swept {len(thresholds)} thresholds")
    return results


def find_optimal_threshold(
    results: List[Dict[str, Any]],
    criterion: str = 'f1_score'
) -> Dict[str, Any]:
    """
    Find the optimal threshold based on a given criterion.

    Args:
        results (List[Dict[str, Any]]): List of threshold results.
        criterion (str): Criterion to optimize ('f1_score', 'specificity', etc.).

    Returns:
        Dict[str, Any]: The result dictionary with the optimal threshold.
    """
    if criterion not in results[0]:
        raise ValueError(f"Criterion '{criterion}' not found in results")

    optimal = max(results, key=lambda x: x[criterion])
    logger.info(f"Optimal threshold for {criterion}: {optimal['threshold']:.4f} "
                f"({criterion}={optimal[criterion]:.4f})")
    return optimal


def run_analysis(
    scores: np.ndarray,
    ground_truth: np.ndarray,
    n_thresholds: int = 50,
    criterion: str = 'f1_score'
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis.

    Args:
        scores (np.ndarray): Anomaly scores.
        ground_truth (np.ndarray): True binary labels.
        n_thresholds (int): Number of thresholds to sweep.
        criterion (str): Criterion for optimal threshold selection.

    Returns:
        Dict[str, Any]: Dictionary containing analysis results.
    """
    # Generate thresholds
    min_score = np.min(scores)
    max_score = np.max(scores)
    thresholds = np.linspace(min_score, max_score, n_thresholds).tolist()

    # Sweep thresholds
    results = sweep_thresholds(scores, ground_truth, thresholds)

    # Find optimal threshold
    optimal = find_optimal_threshold(results, criterion)

    # Prepare output
    analysis = {
        'n_thresholds': n_thresholds,
        'criterion': criterion,
        'optimal_threshold': optimal,
        'all_results': results
    }

    logger.info("Sensitivity analysis completed")
    return analysis


def main() -> None:
    """
    Main entry point for the sensitivity analysis script.
    """
    parser = argparse.ArgumentParser(description="Sensitivity Analysis for Anomaly Detection")
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/results/bayesian_predictions.csv",
        help="Path to predictions CSV file"
    )
    parser.add_argument(
        "--ground_truth",
        type=str,
        default="data/processed/ground_truth.csv",
        help="Path to ground truth CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/sensitivity_analysis.json",
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--score_column",
        type=str,
        default="anomaly_score",
        help="Column name for anomaly scores in predictions file"
    )
    parser.add_argument(
        "--n_thresholds",
        type=int,
        default=50,
        help="Number of thresholds to sweep"
    )
    parser.add_argument(
        "--criterion",
        type=str,
        default="f1_score",
        help="Criterion for optimal threshold selection"
    )
    args = parser.parse_args()

    predictions_path = Path(args.predictions)
    ground_truth_path = Path(args.ground_truth)
    output_path = Path(args.output)

    try:
        # Load data
        df_pred = load_predictions(predictions_path)
        df_gt = load_ground_truth(ground_truth_path)

        # Align data (assuming same length and order)
        if len(df_pred) != len(df_gt):
            logger.warning("Predictions and ground truth have different lengths. "
                           "Truncating to the shorter length.")
            min_len = min(len(df_pred), len(df_gt))
            df_pred = df_pred.iloc[:min_len]
            df_gt = df_gt.iloc[:min_len]

        scores = df_pred[args.score_column].values
        ground_truth = df_gt['is_anomaly'].values

        # Run analysis
        analysis = run_analysis(
            scores, ground_truth,
            n_thresholds=args.n_thresholds,
            criterion=args.criterion
        )

        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)

        logger.info(f"Saved analysis results to {output_path}")

    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
