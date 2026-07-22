"""
Metrics for evaluating meta-cognitive performance.

Implements calculations for:
- Self-consistency (majority vote)
- ROC-AUC
- Brier score
- Expected Calibration Error (ECE)

These metrics align with FR-003 and FR-004 in spec.md.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.preprocessing import label_binarize
from scipy.stats import entropy

from utils.logging import get_logger

logger = get_logger(__name__)


def calculate_self_consistency(
    predictions: List[str],
    num_samples: int
) -> float:
    """
    Calculate self-consistency score using majority vote.

    Args:
        predictions: List of predictions generated for a single question.
                    Each prediction is a string (e.g., "answer: 42").
        num_samples: Total number of samples generated per question.

    Returns:
        Self-consistency score (0.0 to 1.0).
        1.0 means all samples agree, 0.0 means maximum disagreement.
    """
    if not predictions or num_samples == 0:
        return 0.0

    # Count occurrences of each unique prediction
    from collections import Counter
    counts = Counter(predictions)

    # Get the count of the most frequent prediction
    max_count = max(counts.values())

    # Self-consistency is the proportion of samples that match the majority
    return max_count / num_samples


def calculate_roc_auc(
    y_true: List[int],
    y_scores: List[float]
) -> float:
    """
    Calculate ROC-AUC score.

    Args:
        y_true: True binary labels (0 or 1).
        y_scores: Predicted probabilities or confidence scores.

    Returns:
        ROC-AUC score (0.0 to 1.0).
    """
    if len(y_true) < 2 or len(y_scores) < 2:
        logger.warning("Insufficient data for ROC-AUC calculation. Returning 0.0.")
        return 0.0

    # Ensure labels are binary (0 or 1)
    y_true = np.array(y_true)
    y_scores = np.array(y_scores)

    # Check if we have both classes
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. Returning 0.5 for ROC-AUC.")
        return 0.5

    try:
        return roc_auc_score(y_true, y_scores)
    except ValueError as e:
        logger.error(f"Error calculating ROC-AUC: {e}")
        return 0.0


def calculate_brier_score(
    y_true: List[int],
    y_probs: List[float]
) -> float:
    """
    Calculate Brier score for probabilistic predictions.

    The Brier score is the mean squared difference between the predicted
    probability and the actual outcome. Lower is better.

    Args:
        y_true: True binary labels (0 or 1).
        y_probs: Predicted probabilities (0.0 to 1.0).

    Returns:
        Brier score (0.0 to 1.0).
    """
    if len(y_true) == 0 or len(y_probs) == 0:
        logger.warning("Empty input for Brier score calculation. Returning 0.5.")
        return 0.5

    y_true = np.array(y_true)
    y_probs = np.array(y_probs)

    # Ensure probabilities are in [0, 1]
    y_probs = np.clip(y_probs, 0.0, 1.0)

    try:
        return brier_score_loss(y_true, y_probs)
    except ValueError as e:
        logger.error(f"Error calculating Brier score: {e}")
        return 0.5


def calculate_ece(
    y_true: List[int],
    y_probs: List[float],
    num_bins: int = 10
) -> float:
    """
    Calculate Expected Calibration Error (ECE).

    ECE measures the difference between predicted confidence and actual accuracy,
    averaged across bins. Lower is better.

    Args:
        y_true: True binary labels (0 or 1).
        y_probs: Predicted probabilities (0.0 to 1.0).
        num_bins: Number of bins for calibration curve.

    Returns:
        Expected Calibration Error (0.0 to 1.0).
    """
    if len(y_true) == 0 or len(y_probs) == 0:
        logger.warning("Empty input for ECE calculation. Returning 0.0.")
        return 0.0

    y_true = np.array(y_true)
    y_probs = np.array(y_probs)

    # Ensure probabilities are in [0, 1]
    y_probs = np.clip(y_probs, 0.0, 1.0)

    # Create bins
    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0.0
    total_samples = len(y_true)

    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find samples in this bin
        in_bin = (y_probs > bin_lower) & (y_probs <= bin_upper)
        bin_size = np.sum(in_bin)

        if bin_size > 0:
            # Calculate accuracy and average confidence in this bin
            bin_accuracy = np.mean(y_true[in_bin])
            bin_confidence = np.mean(y_probs[in_bin])

            # Add weighted absolute difference to ECE
            ece += (bin_size / total_samples) * np.abs(bin_accuracy - bin_confidence)

    return ece


def calculate_calibration_curve(
    y_true: List[int],
    y_probs: List[float],
    num_bins: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate calibration curve data for plotting.

    Args:
        y_true: True binary labels (0 or 1).
        y_probs: Predicted probabilities (0.0 to 1.0).
        num_bins: Number of bins for calibration curve.

    Returns:
        Tuple of (bin_centers, bin_accuracies, bin_counts).
    """
    if len(y_true) == 0 or len(y_probs) == 0:
        logger.warning("Empty input for calibration curve. Returning empty arrays.")
        return np.array([]), np.array([]), np.array([])

    y_true = np.array(y_true)
    y_probs = np.array(y_probs)
    y_probs = np.clip(y_probs, 0.0, 1.0)

    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2
    bin_accuracies = np.zeros(num_bins)
    bin_counts = np.zeros(num_bins)

    for i, (bin_lower, bin_upper) in enumerate(zip(bin_boundaries[:-1], bin_boundaries[1:])):
        in_bin = (y_probs > bin_lower) & (y_probs <= bin_upper)
        bin_size = np.sum(in_bin)

        if bin_size > 0:
            bin_accuracies[i] = np.mean(y_true[in_bin])
            bin_counts[i] = bin_size

    return bin_centers, bin_accuracies, bin_counts


def calculate_entropy(
    y_probs: List[float]
) -> float:
    """
    Calculate entropy of predicted probabilities.

    Higher entropy indicates more uncertainty.

    Args:
        y_probs: Predicted probabilities (0.0 to 1.0).

    Returns:
        Entropy value (0.0 to log(2) for binary case).
    """
    if len(y_probs) == 0:
        return 0.0

    y_probs = np.array(y_probs)
    y_probs = np.clip(y_probs, 1e-10, 1.0 - 1e-10)  # Avoid log(0)

    # Binary entropy: -p*log(p) - (1-p)*log(1-p)
    # We calculate the mean entropy across samples
    entropies = -y_probs * np.log2(y_probs) - (1 - y_probs) * np.log2(1 - y_probs)
    return np.mean(entropies)


def aggregate_metrics(
    self_consistency_scores: List[float],
    roc_auc_scores: List[float],
    brier_scores: List[float],
    ece_scores: List[float]
) -> Dict[str, float]:
    """
    Aggregate metrics across multiple samples/questions.

    Args:
        self_consistency_scores: List of self-consistency scores.
        roc_auc_scores: List of ROC-AUC scores.
        brier_scores: List of Brier scores.
        ece_scores: List of ECE scores.

    Returns:
        Dictionary with mean, std, min, max for each metric.
    """
    def compute_stats(scores: List[float]) -> Dict[str, float]:
        if not scores:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        arr = np.array(scores)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr))
        }

    return {
        "self_consistency": compute_stats(self_consistency_scores),
        "roc_auc": compute_stats(roc_auc_scores),
        "brier_score": compute_stats(brier_scores),
        "ece": compute_stats(ece_scores)
    }