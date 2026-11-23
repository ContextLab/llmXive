"""
Threshold optimization module for entropy-guided validity prediction.

This module implements logic to find the optimal entropy threshold that minimizes
the weighted sum of false positives and false negatives for token validity prediction.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_metrics_at_threshold(
    entropies: List[float],
    validity_labels: List[bool],
    threshold: float,
    fp_weight: float = 1.0,
    fn_weight: float = 1.0
) -> Dict[str, Any]:
    """
    Calculate classification metrics at a specific entropy threshold.

    Entropy values below the threshold are predicted as 'valid' (true),
    and values above are predicted as 'invalid' (false).

    Args:
        entropies: List of entropy values for each token.
        validity_labels: List of ground truth validity labels (True=valid, False=invalid).
        threshold: The entropy threshold to evaluate.
        fp_weight: Weight for false positive cost.
        fn_weight: Weight for false negative cost.

    Returns:
        Dictionary containing:
            - threshold: The evaluated threshold value.
            - tp: True positives count.
            - tn: True negatives count.
            - fp: False positives count.
            - fn: False negatives count.
            - precision: Precision score.
            - recall: Recall score.
            - f1: F1 score.
            - weighted_cost: Weighted sum of FP and FN.
    """
    if len(entropies) != len(validity_labels):
        raise ValueError("Entropies and validity_labels must have the same length")

    if len(entropies) == 0:
        return {
            'threshold': threshold,
            'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0,
            'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
            'weighted_cost': 0.0
        }

    entropies_arr = np.array(entropies)
    labels_arr = np.array(validity_labels, dtype=bool)

    # Prediction: entropy < threshold => valid (True), else invalid (False)
    predictions = entropies_arr < threshold

    tp = int(np.sum(predictions & labels_arr))
    tn = int(np.sum(~predictions & ~labels_arr))
    fp = int(np.sum(predictions & ~labels_arr))
    fn = int(np.sum(~predictions & labels_arr))

    # Calculate precision, recall, f1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    weighted_cost = (fp * fp_weight) + (fn * fn_weight)

    return {
        'threshold': float(threshold),
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn,
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'weighted_cost': float(weighted_cost)
    }


def find_optimal_threshold(
    entropies: List[float],
    validity_labels: List[bool],
    fp_weight: float = 1.0,
    fn_weight: float = 1.0,
    num_candidates: int = 100
) -> Dict[str, Any]:
    """
    Find the optimal entropy threshold that minimizes the weighted cost of errors.

    This function evaluates a range of candidate thresholds and selects the one
    that minimizes the weighted sum of false positives and false negatives.

    Args:
        entropies: List of entropy values.
        validity_labels: List of ground truth validity labels.
        fp_weight: Weight for false positive cost.
        fn_weight: Weight for false negative cost.
        num_candidates: Number of candidate thresholds to evaluate.

    Returns:
        Dictionary containing:
            - optimal_threshold: The threshold that minimizes weighted cost.
            - metrics: Full metrics dictionary at the optimal threshold.
            - all_metrics: List of metrics for all evaluated thresholds.
    """
    if len(entropies) == 0 or len(validity_labels) == 0:
        logger.warning("Empty input data for threshold optimization")
        return {
            'optimal_threshold': None,
            'metrics': None,
            'all_metrics': []
        }

    entropies_arr = np.array(entropies)
    min_entropy = float(np.min(entropies_arr))
    max_entropy = float(np.max(entropies_arr))

    # Generate candidate thresholds
    if min_entropy == max_entropy:
        candidate_thresholds = [min_entropy]
    else:
        candidate_thresholds = np.linspace(min_entropy, max_entropy, num_candidates)

    all_metrics = []
    best_threshold = None
    best_cost = float('inf')
    best_metrics = None

    for thresh in candidate_thresholds:
        metrics = calculate_metrics_at_threshold(
            entropies, validity_labels, thresh, fp_weight, fn_weight
        )
        all_metrics.append(metrics)

        if metrics['weighted_cost'] < best_cost:
            best_cost = metrics['weighted_cost']
            best_threshold = metrics['threshold']
            best_metrics = metrics

    return {
        'optimal_threshold': best_threshold,
        'metrics': best_metrics,
        'all_metrics': all_metrics
    }


def analyze_thresholds(
    entropies: List[float],
    validity_labels: List[bool],
    output_path: Optional[str] = None,
    fp_weight: float = 1.0,
    fn_weight: float = 1.0
) -> Dict[str, Any]:
    """
    Perform comprehensive threshold analysis and optionally write results to disk.

    Args:
        entropies: List of entropy values.
        validity_labels: List of ground truth validity labels.
        output_path: Optional path to write JSON results.
        fp_weight: Weight for false positive cost.
        fn_weight: Weight for false negative cost.

    Returns:
        Dictionary containing analysis results.
    """
    logger.info(f"Analyzing thresholds for {len(entropies)} data points")

    result = find_optimal_threshold(
        entropies, validity_labels, fp_weight, fn_weight
    )

    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Remove all_metrics from output file if too large, keep summary
        export_result = {
            'optimal_threshold': result['optimal_threshold'],
            'metrics': result['metrics'],
            'summary': {
                'num_data_points': len(entropies),
                'num_valid': sum(validity_labels),
                'num_invalid': len(validity_labels) - sum(validity_labels),
                'entropy_range': {
                    'min': float(np.min(entropies)),
                    'max': float(np.max(entropies))
                },
                'weights': {
                    'fp_weight': fp_weight,
                    'fn_weight': fn_weight
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_result, f, indent=2)

        logger.info(f"Threshold analysis results written to {output_path}")

    return result


def main() -> None:
    """
    Main entry point for threshold optimization script.
    Expects data in data/entropy_profiles_merged.jsonl format.
    """
    # Default paths relative to project root
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "entropy_profiles_merged.jsonl"
    output_path = base_path / "results" / "threshold_optimization.json"

    # Allow override via command line arguments
    if len(sys.argv) > 1:
        data_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    # Load data
    entropies = []
    validity_labels = []

    logger.info(f"Loading data from {data_path}")
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Extract entropy values (flatten layer-wise entropies)
                if 'entropy_values' in record and isinstance(record['entropy_values'], list):
                    entropies.extend(record['entropy_values'])
                    # Extend validity labels to match (assuming one validity per token)
                    validity = record.get('validity', False)
                    validity_labels.extend([validity] * len(record['entropy_values']))
                elif 'entropy' in record:
                    # Handle single entropy value per record
                    entropies.append(float(record['entropy']))
                    validity_labels.append(record.get('validity', False))
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

    if len(entropies) == 0:
        logger.error("No valid data points found in input file")
        sys.exit(1)

    logger.info(f"Loaded {len(entropies)} entropy values")

    # Run analysis
    result = analyze_thresholds(
        entropies,
        validity_labels,
        output_path=str(output_path),
        fp_weight=1.0,
        fn_weight=1.0
    )

    if result['optimal_threshold'] is not None:
        logger.info(f"Optimal threshold: {result['optimal_threshold']:.4f}")
        logger.info(f"Weighted cost at optimal: {result['metrics']['weighted_cost']:.2f}")
    else:
        logger.warning("Could not determine optimal threshold")


if __name__ == "__main__":
    main()
