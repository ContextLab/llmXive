"""
Evaluation metrics for anomaly detection models.
Includes precision, recall, F1, AUC-ROC, and threshold enforcement.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Tuple

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, classification_report
import yaml

logger = logging.getLogger(__name__)


class MetricCalculator:
    """Calculator for standard classification metrics."""

    def __init__(self, threshold: float = 0.5):
        """
        Initialize metric calculator.

        Args:
            threshold: Classification threshold for binary predictions.
        """
        self.threshold = threshold

    def calculate_all(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_scores: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Calculate all standard metrics.

        Args:
            y_true: True labels.
            y_pred: Predicted labels.
            y_scores: Probability scores (optional, needed for AUC).

        Returns:
            Dictionary of metric names to values.
        """
        metrics = {
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
        }

        if y_scores is not None:
            try:
                metrics['auc_roc'] = roc_auc_score(y_true, y_scores)
            except ValueError as e:
                logger.warning(f"Could not compute AUC-ROC: {e}")
                metrics['auc_roc'] = None
        else:
            metrics['auc_roc'] = None

        return metrics

    def generate_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_scores: Optional[np.ndarray] = None
    ) -> str:
        """Generate a detailed classification report."""
        return classification_report(y_true, y_pred)


def load_config_threshold(config_path: str = 'code/config.yaml') -> float:
    """
    Load target AUC threshold from config file.

    Args:
        config_path: Path to the config YAML file.

    Returns:
        Target AUC threshold value.
    """
    default_threshold = 0.75

    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}. Using default threshold {default_threshold}")
        return default_threshold

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            threshold = config.get('target_auc', default_threshold)
            logger.info(f"Loaded target AUC threshold: {threshold}")
            return float(threshold)
    except Exception as e:
        logger.error(f"Error reading config: {e}. Using default threshold {default_threshold}")
        return default_threshold


def check_target_auc(
    auc_score: Optional[float],
    target_auc: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Check if the AUC score meets the target threshold.

    Args:
        auc_score: The computed AUC score.
        target_auc: The target threshold (loads from config if None).

    Returns:
        Tuple of (meets_threshold, message).
    """
    if auc_score is None:
        return False, "AUC score is None"

    if target_auc is None:
        target_auc = load_config_threshold()

    if auc_score >= target_auc:
        return True, f"AUC {auc_score:.4f} meets target {target_auc:.4f}"
    else:
        return False, f"AUC {auc_score:.4f} below target {target_auc:.4f}"


def save_metrics(
    metrics: Dict[str, Any],
    output_path: str
):
    """
    Save metrics to a JSON file.

    Args:
        metrics: Dictionary of metrics.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")


def main():
    """Example usage of metrics module."""
    logging.basicConfig(level=logging.INFO)

    # Example: Calculate metrics
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 0, 1, 1, 0, 0, 0, 1])
    y_scores = np.array([0.1, 0.2, 0.9, 0.8, 0.1, 0.6, 0.1, 0.7])

    calc = MetricCalculator()
    metrics = calc.calculate_all(y_true, y_pred, y_scores)
    logger.info(f"Calculated metrics: {metrics}")

    # Check against target
    meets, msg = check_target_auc(metrics['auc_roc'])
    logger.info(f"Threshold check: {msg}")


if __name__ == "__main__":
    main()
