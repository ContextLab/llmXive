"""
Evaluation metrics for anomaly detection models.

Implements F1, Precision, Recall, AUC, and confusion matrix calculations
for comparing DPGMM and baseline models on time series anomaly detection.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union, Sequence
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _np_to_py(o: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return o


@dataclass
class EvaluationMetrics:
    """Container for all evaluation metrics from a model run."""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0
    auc_pr: float = 0.0
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_samples: int = 0
    anomaly_threshold: float = 0.0
    model_name: str = ""
    dataset_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with numpy-safe serialization."""
        return {
            "precision": _np_to_py(self.precision),
            "recall": _np_to_py(self.recall),
            "f1_score": _np_to_py(self.f1_score),
            "auc_roc": _np_to_py(self.auc_roc),
            "auc_pr": _np_to_py(self.auc_pr),
            "true_positives": int(self.true_positives),
            "true_negatives": int(self.true_negatives),
            "false_positives": int(self.false_positives),
            "false_negatives": int(self.false_negatives),
            "total_samples": int(self.total_samples),
            "anomaly_threshold": _np_to_py(self.anomaly_threshold),
            "model_name": self.model_name,
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp
        }


def compute_precision(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute precision score.

    Precision = TP / (TP + FP)
    """
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)

    tp = np.sum(y_true & y_pred)
    fp = np.sum(~y_true & y_pred)

    if (tp + fp) == 0:
        return 0.0

    return float(tp / (tp + fp))


def compute_recall(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute recall score.

    Recall = TP / (TP + FN)
    """
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)

    tp = np.sum(y_true & y_pred)
    fn = np.sum(y_true & ~y_pred)

    if (tp + fn) == 0:
        return 0.0

    return float(tp / (tp + fn))


def compute_f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute F1 score (harmonic mean of precision and recall).

    F1 = 2 * (precision * recall) / (precision + recall)
    """
    precision = compute_precision(y_true, y_pred)
    recall = compute_recall(y_true, y_pred)

    if (precision + recall) == 0:
        return 0.0

    return float(2 * (precision * recall) / (precision + recall))


def compute_auc(y_true: np.ndarray, scores: np.ndarray, curve: str = "roc") -> float:
    """
    Compute Area Under Curve for ROC or PR curve.

    Args:
        y_true: Ground truth binary labels
        scores: Anomaly scores (higher = more anomalous)
        curve: "roc" for ROC-AUC or "pr" for PR-AUC

    Returns:
        AUC value between 0 and 1
    """
    y_true = np.asarray(y_true, dtype=bool)
    scores = np.asarray(scores, dtype=float)

    if curve == "roc":
        fpr, tpr, _ = compute_roc_curve_points(y_true, scores)
        # Trapezoidal integration
        auc = np.trapz(tpr, fpr)
    elif curve == "pr":
        precision, recall, _ = compute_pr_curve_points(y_true, scores)
        # Trapezoidal integration for PR curve
        auc = np.trapz(precision, recall)
    else:
        raise ValueError(f"Unknown curve type: {curve}. Use 'roc' or 'pr'.")

    return float(auc)


def compute_roc_curve_points(y_true: np.ndarray, scores: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute ROC curve points (FPR, TPR, thresholds).

    Returns:
        Tuple of (FPR array, TPR array, thresholds array)
    """
    y_true = np.asarray(y_true, dtype=bool)
    scores = np.asarray(scores, dtype=float)

    # Get unique thresholds
    thresholds = np.unique(scores)
    thresholds = np.sort(thresholds)[::-1]  # Higher scores = more anomalous

    fpr_list = []
    tpr_list = []

    n_pos = np.sum(y_true)
    n_neg = len(y_true) - n_pos

    if n_pos == 0 or n_neg == 0:
        # Degenerate case
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([0.0, 1.0])

    for threshold in thresholds:
        y_pred = scores >= threshold
        tp = np.sum(y_true & y_pred)
        fp = np.sum(~y_true & y_pred)

        tpr = tp / n_pos if n_pos > 0 else 0.0
        fpr = fp / n_neg if n_neg > 0 else 0.0

        fpr_list.append(fpr)
        tpr_list.append(tpr)

    # Add origin and endpoint
    fpr_list.insert(0, 0.0)
    tpr_list.insert(0, 0.0)
    fpr_list.append(1.0)
    tpr_list.append(1.0)

    return (
        np.array(fpr_list),
        np.array(tpr_list),
        np.concatenate([[np.inf], thresholds, [0.0]])
    )


def compute_pr_curve_points(y_true: np.ndarray, scores: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Precision-Recall curve points.

    Returns:
        Tuple of (Precision array, Recall array, thresholds array)
    """
    y_true = np.asarray(y_true, dtype=bool)
    scores = np.asarray(scores, dtype=float)

    # Get unique thresholds
    thresholds = np.unique(scores)
    thresholds = np.sort(thresholds)[::-1]

    precision_list = []
    recall_list = []

    n_pos = np.sum(y_true)

    if n_pos == 0:
        return np.array([1.0]), np.array([0.0]), np.array([0.0])

    for threshold in thresholds:
        y_pred = scores >= threshold
        tp = np.sum(y_true & y_pred)
        fp = np.sum(~y_true & y_pred)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / n_pos if n_pos > 0 else 0.0

        precision_list.append(precision)
        recall_list.append(recall)

    # Add starting point (precision=1.0, recall=0.0)
    precision_list.insert(0, 1.0)
    recall_list.insert(0, 0.0)

    return (
        np.array(precision_list),
        np.array(recall_list),
        np.concatenate([[np.inf], thresholds, [0.0]])
    )


def generate_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, int]:
    """
    Generate confusion matrix components.

    Returns:
        Dict with tp, tn, fp, fn counts
    """
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)

    tp = int(np.sum(y_true & y_pred))
    tn = int(np.sum(~y_true & ~y_pred))
    fp = int(np.sum(~y_true & y_pred))
    fn = int(np.sum(y_true & ~y_pred))

    return {
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn
    }


def save_confusion_matrix_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: Union[str, Path],
    title: str = "Confusion Matrix"
) -> Path:
    """
    Save confusion matrix as a plot.

    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        output_path: Path to save the plot
        title: Plot title

    Returns:
        Path to saved plot
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm = generate_confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        [[cm["true_negatives"], cm["false_positives"]],
         [cm["false_negatives"], cm["true_positives"]]],
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Predicted Normal", "Predicted Anomaly"],
        yticklabels=["Actual Normal", "Actual Anomaly"],
        ax=ax
    )
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title(title)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Saved confusion matrix plot to {output_path}")
    return output_path


def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: Optional[np.ndarray] = None,
    model_name: str = "unknown",
    dataset_name: str = "unknown"
) -> EvaluationMetrics:
    """
    Compute all evaluation metrics at once.

    Args:
        y_true: Ground truth binary labels
        y_pred: Predicted binary labels
        scores: Optional anomaly scores for AUC calculation
        model_name: Name of the model being evaluated
        dataset_name: Name of the dataset

    Returns:
        EvaluationMetrics object with all computed metrics
    """
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)

    cm = generate_confusion_matrix(y_true, y_pred)

    metrics = EvaluationMetrics(
        precision=compute_precision(y_true, y_pred),
        recall=compute_recall(y_true, y_pred),
        f1_score=compute_f1_score(y_true, y_pred),
        true_positives=cm["true_positives"],
        true_negatives=cm["true_negatives"],
        false_positives=cm["false_positives"],
        false_negatives=cm["false_negatives"],
        total_samples=len(y_true),
        model_name=model_name,
        dataset_name=dataset_name
    )

    if scores is not None:
        scores = np.asarray(scores, dtype=float)
        metrics.auc_roc = compute_auc(y_true, scores, curve="roc")
        metrics.auc_pr = compute_auc(y_true, scores, curve="pr")

    return metrics


def main() -> None:
    """
    Main entry point for testing metrics calculations.

    Runs a simple demo with synthetic data.
    """
    # Generate synthetic test data
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = 100

    y_true = np.zeros(n_samples, dtype=bool)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    y_true[anomaly_indices] = True

    # Simulate predictions with some noise
    y_pred = y_true.copy()
    noise_mask = np.random.random(n_samples) < 0.1
    y_pred = y_pred ^ noise_mask

    # Generate scores (higher for anomalies)
    scores = np.random.random(n_samples)
    scores[anomaly_indices] += 0.3
    scores = np.clip(scores, 0, 1)

    # Compute all metrics
    metrics = compute_all_metrics(y_true, y_pred, scores, "DPGMM", "synthetic_test")

    print("=" * 50)
    print("Evaluation Metrics Report")
    print("=" * 50)
    print(f"Model: {metrics.model_name}")
    print(f"Dataset: {metrics.dataset_name}")
    print(f"Total Samples: {metrics.total_samples}")
    print(f"Anomalies: {np.sum(y_true)}")
    print("-" * 50)
    print(f"Precision: {metrics.precision:.4f}")
    print(f"Recall:    {metrics.recall:.4f}")
    print(f"F1 Score:  {metrics.f1_score:.4f}")
    print(f"AUC-ROC:   {metrics.auc_roc:.4f}")
    print(f"AUC-PR:    {metrics.auc_pr:.4f}")
    print("-" * 50)
    print(f"TP: {metrics.true_positives}, TN: {metrics.true_negatives}")
    print(f"FP: {metrics.false_positives}, FN: {metrics.false_negatives}")
    print("=" * 50)


if __name__ == "__main__":
    main()
