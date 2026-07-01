"""
Metrics module for calculating and reporting AUC and TSS values for Species Distribution Models.

This module implements the evaluation metrics required by SC-001 (AUC) and SC-002 (TSS).
It provides functions to calculate these metrics from model predictions and ground truth labels,
and to generate structured reports.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Union
from sklearn.metrics import roc_auc_score, confusion_matrix, roc_curve
from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate the Area Under the Receiver Operating Characteristic Curve (AUC-ROC).

    Args:
        y_true: True binary labels (0 or 1).
        y_scores: Probability scores or decision function outputs.

    Returns:
        float: The AUC value between 0.0 and 1.0.

    Raises:
        ValueError: If inputs are invalid or AUC cannot be calculated.
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. AUC cannot be calculated.")
        return np.nan

    try:
        auc_value = roc_auc_score(y_true, y_scores)
        logger.info(f"AUC calculated: {auc_value:.4f}")
        return auc_value
    except ValueError as e:
        logger.error(f"Error calculating AUC: {e}")
        raise


def calculate_tss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the True Skill Statistic (TSS).

    TSS = Sensitivity + Specificity - 1
    where:
        Sensitivity = TP / (TP + FN)
        Specificity = TN / (TN + FP)

    Args:
        y_true: True binary labels (0 or 1).
        y_pred: Predicted binary labels (0 or 1).

    Returns:
        float: The TSS value between -1.0 and 1.0. Returns np.nan if division by zero occurs.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    tss_value = sensitivity + specificity - 1.0
    logger.info(f"TSS calculated: {tss_value:.4f} (Sensitivity: {sensitivity:.4f}, Specificity: {specificity:.4f})")
    return tss_value


def find_optimal_threshold(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Find the optimal threshold that maximizes the True Skill Statistic (TSS).

    Args:
        y_true: True binary labels (0 or 1).
        y_scores: Probability scores.

    Returns:
        float: The threshold that maximizes TSS.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    tss_values = tpr + (1 - fpr) - 1
    optimal_idx = np.argmax(tss_values)
    optimal_threshold = thresholds[optimal_idx]
    logger.info(f"Optimal threshold found: {optimal_threshold:.4f}")
    return optimal_threshold


def evaluate_model(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """
    Evaluate model performance by calculating AUC and TSS.

    If no threshold is provided, it is automatically determined to maximize TSS.

    Args:
        y_true: True binary labels (0 or 1).
        y_scores: Probability scores.
        threshold: Optional threshold for binarizing predictions. If None, optimal threshold is used.

    Returns:
        dict: Dictionary containing 'auc', 'tss', 'threshold', 'sensitivity', and 'specificity'.
    """
    auc = calculate_auc(y_true, y_scores)

    if threshold is None:
        threshold = find_optimal_threshold(y_true, y_scores)

    y_pred = (y_scores >= threshold).astype(int)
    tss = calculate_tss(y_true, y_pred)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        'auc': auc,
        'tss': tss,
        'threshold': threshold,
        'sensitivity': sensitivity,
        'specificity': specificity,
        'tp': int(tp),
        'tn': int(tn),
        'fp': int(fp),
        'fn': int(fn)
    }


def generate_metrics_report(
    results: Dict[str, Dict[str, float]],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate a structured report from model evaluation results.

    Args:
        results: Dictionary mapping species names to their evaluation metrics dictionaries.
        output_path: Optional path to save the report as CSV.

    Returns:
        pd.DataFrame: DataFrame containing the metrics report.
    """
    report_data = []
    for species, metrics in results.items():
        row = {'species': species}
        row.update(metrics)
        report_data.append(row)

    df = pd.DataFrame(report_data)
    logger.info(f"Generated metrics report with {len(df)} species.")

    if output_path:
        df.to_csv(output_path, index=False)
        logger.info(f"Metrics report saved to {output_path}")

    return df