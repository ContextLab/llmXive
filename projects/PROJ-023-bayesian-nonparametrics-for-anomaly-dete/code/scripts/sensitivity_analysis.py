"""
Sensitivity Analysis for Anomaly Detection Thresholds.

This script sweeps decision thresholds across a range to report false-positive/negative rates
and optimize for F1-score.

Author: llmXive Research Agent
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Importing from local lib modules
try:
    from lib.metrics import calculate_metrics
except ImportError:
    print("Error: Required modules in code/lib/ not found.")
    sys.exit(1)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def load_predictions(path: str) -> np.ndarray:
    """Load anomaly scores from CSV."""
    df = pd.read_csv(path)
    if 'anomaly_score' in df.columns:
        return df['anomaly_score'].values
    elif 'anomaly_flag' in df.columns:
        return df['anomaly_flag'].values
    else:
        raise ValueError(f"Invalid prediction file format: {path}")

def load_ground_truth(path: str) -> np.ndarray:
    """Load ground truth labels from CSV."""
    df = pd.read_csv(path)
    if 'label' in df.columns:
        return df['label'].values.astype(int)
    elif 'is_anomaly' in df.columns:
        return df['is_anomaly'].values.astype(int)
    else:
        raise ValueError(f"Invalid ground truth file format: {path}")

def calculate_metrics_at_threshold(
    scores: np.ndarray,
    ground_truth: np.ndarray,
    threshold: float
) -> Dict[str, float]:
    """
    Calculate precision, recall, F1 at a specific threshold.

    Args:
        scores (np.ndarray): Anomaly scores.
        ground_truth (np.ndarray): Ground truth labels.
        threshold (float): Threshold value.

    Returns:
        Dict[str, float]: Metrics dictionary.
    """
    predictions = (scores >= threshold).astype(int)
    tp = np.sum((predictions == 1) & (ground_truth == 1))
    fp = np.sum((predictions == 1) & (ground_truth == 0))
    fn = np.sum((predictions == 0) & (ground_truth == 1))
    tn = np.sum((predictions == 0) & (ground_truth == 0))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'false_positive_rate': fpr
    }

def sweep_thresholds(
    scores: np.ndarray,
    ground_truth: np.ndarray,
    start: float = 0.0,
    end: float = 1.0,
    step: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Sweep thresholds and collect metrics.

    Args:
        scores (np.ndarray): Anomaly scores.
        ground_truth (np.ndarray): Ground truth labels.
        start (float): Start threshold.
        end (float): End threshold.
        step (float): Step size.

    Returns:
        List[Dict[str, Any]]: List of metric dictionaries.
    """
    results = []
    # Handle floating point precision
    thresholds = np.arange(start, end + step, step)
    
    for t in thresholds:
        t_rounded = round(t, 2)
        metrics = calculate_metrics_at_threshold(scores, ground_truth, t_rounded)
        results.append({
            'threshold': t_rounded,
            **metrics
        })
    return results

def find_optimal_threshold(results: List[Dict[str, Any]]) -> float:
    """Find the threshold that maximizes F1-score."""
    best_f1 = -1.0
    best_threshold = 0.5
    for r in results:
        if r['f1_score'] > best_f1:
            best_f1 = r['f1_score']
            best_threshold = r['threshold']
    return best_threshold

def run_analysis(
    scores: np.ndarray,
    ground_truth: np.ndarray,
    output_path: str
) -> None:
    """
    Run full sensitivity analysis.

    Args:
        scores (np.ndarray): Anomaly scores.
        ground_truth (np.ndarray): Ground truth labels.
        output_path (str): Output JSON path.
    """
    logger.info("Running sensitivity analysis...")
    results = sweep_thresholds(scores, ground_truth)
    optimal_t = find_optimal_threshold(results)
    logger.info(f"Optimal threshold: {optimal_t}")

    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sensitivity Analysis")
    parser.add_argument('--scores', type=str, required=True, help='Path to anomaly scores CSV')
    parser.add_argument('--truth', type=str, required=True, help='Path to ground truth CSV')
    parser.add_argument('--output', type=str, default='data/results/sensitivity_analysis.json', help='Output JSON')
    args = parser.parse_args()

    scores = load_predictions(args.scores)
    ground_truth = load_ground_truth(args.truth)

    run_analysis(scores, ground_truth, args.output)
    logger.info("Sensitivity analysis completed.")

if __name__ == '__main__':
    main()
