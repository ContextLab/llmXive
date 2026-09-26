"""
Metrics calculation module for Species Distribution Models.

Implements calculation of AUC (Area Under the ROC Curve) and TSS (True Skill Statistic),
along with optimal threshold finding and comprehensive model evaluation reporting.
"""

import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Union, List, Any
from pathlib import Path
from sklearn.metrics import roc_auc_score, confusion_matrix, roc_curve
from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate the Area Under the Receiver Operating Characteristic Curve (AUC).

    Args:
        y_true: Binary ground truth labels (0 or 1).
        y_scores: Predicted probabilities or scores for the positive class.

    Returns:
        float: AUC value between 0 and 1.

    Raises:
        ValueError: If inputs are invalid or contain only one class.
    """
    if len(y_true) == 0 or len(y_scores) == 0:
        raise ValueError("Input arrays cannot be empty.")

    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. AUC is undefined. Returning 0.5.")
        return 0.5

    try:
        auc_value = roc_auc_score(y_true, y_scores)
        logger.info(f"Calculated AUC: {auc_value:.4f}")
        return auc_value
    except ValueError as e:
        logger.error(f"Error calculating AUC: {e}")
        raise


def calculate_tss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the True Skill Statistic (TSS).

    TSS = Sensitivity + Specificity - 1
    TSS ranges from -1 to 1, where 1 indicates perfect agreement and
    values <= 0 indicate performance no better than random.

    Args:
        y_true: Binary ground truth labels (0 or 1).
        y_pred: Binary predicted labels (0 or 1).

    Returns:
        float: TSS value.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    # Avoid division by zero
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    tss_value = sensitivity + specificity - 1.0
    logger.info(f"Calculated TSS: {tss_value:.4f} (Sensitivity: {sensitivity:.4f}, Specificity: {specificity:.4f})")

    return tss_value


def find_optimal_threshold(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Find the optimal threshold that maximizes the True Skill Statistic (TSS).

    This is done by iterating over all unique thresholds from the ROC curve
    and selecting the one that yields the maximum TSS.

    Args:
        y_true: Binary ground truth labels (0 or 1).
        y_scores: Predicted probabilities or scores for the positive class.

    Returns:
        float: The threshold value that maximizes TSS.
    """
    if len(y_true) == 0 or len(y_scores) == 0:
        raise ValueError("Input arrays cannot be empty.")

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)

    # Calculate TSS for each threshold
    # TSS = Sensitivity (TPR) - (1 - Specificity) = TPR - FPR
    tss_values = tpr - fpr

    # Find the index of the maximum TSS
    max_idx = np.argmax(tss_values)
    optimal_threshold = thresholds[max_idx]

    logger.info(f"Found optimal threshold: {optimal_threshold:.4f} (Max TSS: {tss_values[max_idx]:.4f})")
    return optimal_threshold


def evaluate_model(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """
    Evaluate model performance using AUC and TSS.

    If a threshold is not provided, the optimal threshold maximizing TSS is calculated.
    Binary predictions are generated using the threshold to compute TSS.

    Args:
        y_true: Binary ground truth labels (0 or 1).
        y_scores: Predicted probabilities or scores for the positive class.
        threshold: Optional threshold for binary classification. If None, optimal is found.

    Returns:
        dict: Dictionary containing 'auc', 'tss', and 'threshold'.
    """
    # Calculate AUC
    auc = calculate_auc(y_true, y_scores)

    # Determine threshold
    if threshold is None:
        threshold = find_optimal_threshold(y_true, y_scores)

    # Generate binary predictions
    y_pred = (y_scores >= threshold).astype(int)

    # Calculate TSS
    tss = calculate_tss(y_true, y_pred)

    return {
        "auc": auc,
        "tss": tss,
        "threshold": threshold
    }


def generate_metrics_report(
    results: Dict[str, Any],
    output_path: Union[str, Path],
    species_name: str = "unknown"
) -> Path:
    """
    Generate a JSON report containing model metrics and evaluation details.

    Args:
        results: Dictionary containing model results (e.g., from train_rf).
        output_path: Path to save the JSON report.
        species_name: Name of the species for the report header.

    Returns:
        Path: The path to the generated report file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "species": species_name,
        "metrics": results.get("metrics", {}),
        "model_parameters": results.get("model_parameters", {}),
        "cross_validation_folds": results.get("cv_folds", 5),
        "timestamp": results.get("timestamp", "N/A"),
        "data_summary": {
            "total_records": results.get("total_records", 0),
            "presence_records": results.get("presence_records", 0),
            "absence_records": results.get("absence_records", 0),
            "feature_count": results.get("feature_count", 0)
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Metrics report saved to {output_path}")
    return output_path
