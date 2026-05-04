"""
Evaluation Metrics for Anomaly Detection Models.

Implements F1-score, precision, recall, AUC, and confusion matrix generation.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union, Sequence
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for all evaluation metrics."""
    f1_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    auc_roc: float = 0.0
    auc_pr: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "f1_score": self.f1_score,
            "precision": self.precision,
            "recall": self.recall,
            "auc_roc": self.auc_roc,
            "auc_pr": self.auc_pr,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationMetrics":
        """Create EvaluationMetrics from dictionary."""
        return cls(
            f1_score=data.get("f1_score", 0.0),
            precision=data.get("precision", 0.0),
            recall=data.get("recall", 0.0),
            auc_roc=data.get("auc_roc", 0.0),
            auc_pr=data.get("auc_pr", 0.0),
            true_positives=data.get("true_positives", 0),
            false_positives=data.get("false_positives", 0),
            true_negatives=data.get("true_negatives", 0),
            false_negatives=data.get("false_negatives", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


def compute_f1_score(precision: float, recall: float,
                    epsilon: float = 1e-10) -> float:
    """
Compute F1-score from precision and recall.

Args:
    precision: Precision value (0-1)
    recall: Recall value (0-1)
    epsilon: Small value to avoid division by zero

Returns:
    F1-score (harmonic mean of precision and recall)
"""
    if precision + recall < epsilon:
        return 0.0
    return 2.0 * (precision * recall) / (precision + recall)


def compute_precision(tp: int, fp: int,
                    epsilon: float = 1e-10) -> float:
    """
Compute precision from confusion matrix values.

Args:
    tp: True positives count
    fp: False positives count
    epsilon: Small value to avoid division by zero

Returns:
    Precision value (0-1)
"""
    denominator = float(tp + fp)
    if denominator < epsilon:
        return 0.0
    return float(tp) / denominator


def compute_recall(tp: int, fn: int,
                  epsilon: float = 1e-10) -> float:
    """
Compute recall from confusion matrix values.

Args:
    tp: True positives count
    fn: False negatives count
    epsilon: Small value to avoid division by zero

Returns:
    Recall value (0-1)
"""
    denominator = float(tp + fn)
    if denominator < epsilon:
        return 0.0
    return float(tp) / denominator


def compute_auc(fpr: Sequence[float], tpr: Sequence[float]) -> float:
    """
Compute AUC using trapezoidal rule.

Args:
    fpr: False positive rates
    tpr: True positive rates

Returns:
    Area under the curve
"""
    fpr_arr = np.array(fpr)
    tpr_arr = np.array(tpr)

    # Sort by FPR
    sorted_indices = np.argsort(fpr_arr)
    fpr_sorted = fpr_arr[sorted_indices]
    tpr_sorted = tpr_arr[sorted_indices]

    # Trapezoidal integration
    auc_value = np.trapz(tpr_sorted, fpr_sorted)
    return float(auc_value)


def generate_confusion_matrix(y_true: Sequence[Union[int, bool]],
                             y_pred: Sequence[Union[int, bool]]) -> Dict[str, int]:
    """
Generate confusion matrix from true and predicted labels.

Args:
    y_true: True binary labels
    y_pred: Predicted binary labels

Returns:
    Dictionary with tp, fp, tn, fn counts
"""
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    tp = int(np.sum((y_true_arr == 1) & (y_pred_arr == 1)))
    fp = int(np.sum((y_true_arr == 0) & (y_pred_arr == 1)))
    tn = int(np.sum((y_true_arr == 0) & (y_pred_arr == 0)))
    fn = int(np.sum((y_true_arr == 1) & (y_pred_arr == 0)))

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn
    }


def save_confusion_matrix_plot(confusion: Dict[str, int],
                               output_path: str) -> Path:
    """
Save confusion matrix as a plot.

Args:
    confusion: Confusion matrix dictionary
    output_path: Path to save the plot

Returns:
    Path to saved plot file
"""
    import matplotlib.pyplot as plt

    tp = confusion.get("true_positives", 0)
    fp = confusion.get("false_positives", 0)
    tn = confusion.get("true_negatives", 0)
    fn = confusion.get("false_negatives", 0)

    matrix = np.array([[tn, fp], [fn, tp]])
    labels = [["TN", "FP"], ["FN", "TP"]]

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, cmap="Blues")

    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{labels[i][j]}\n{int(matrix[i, j])}",
                   ha="center", va="center", color="black")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Negative", "Positive"])
    ax.set_yticklabels(["Negative", "Positive"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix")

    plt.colorbar(im, ax=ax)
    plt.tight_layout()

    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_file, dpi=150)
    plt.close()

    logger.info(f"Confusion matrix saved to {output_file}")
    return output_file


def compute_all_metrics(y_true: Sequence[Union[int, bool]],
                       y_pred: Sequence[Union[int, bool]],
                       y_scores: Optional[Sequence[float]] = None) -> EvaluationMetrics:
    """
Compute all evaluation metrics from predictions.

Args:
    y_true: True binary labels
    y_pred: Predicted binary labels
    y_scores: Optional anomaly scores for AUC computation

Returns:
    EvaluationMetrics object with all computed metrics
"""
    confusion = generate_confusion_matrix(y_true, y_pred)

    precision = compute_precision(
        confusion["true_positives"],
        confusion["false_positives"]
    )

    recall = compute_recall(
        confusion["true_positives"],
        confusion["false_negatives"]
    )

    f1 = compute_f1_score(precision, recall)

    # Compute AUC if scores provided
    auc_roc = 0.0
    auc_pr = 0.0
    if y_scores is not None:
        # Generate ROC curve points
        fpr, tpr, _ = compute_roc_curve_points(y_true, y_scores)
        auc_roc = compute_auc(fpr, tpr)

        # Generate PR curve points
        precision_curve, recall_curve, _ = compute_pr_curve_points(y_true, y_scores)
        auc_pr = compute_auc(recall_curve, precision_curve)

    return EvaluationMetrics(
        f1_score=f1,
        precision=precision,
        recall=recall,
        auc_roc=auc_roc,
        auc_pr=auc_pr,
        true_positives=confusion["true_positives"],
        false_positives=confusion["false_positives"],
        true_negatives=confusion["true_negatives"],
        false_negatives=confusion["false_negatives"]
    )


def compute_roc_curve_points(y_true: Sequence[Union[int, bool]],
                            y_scores: Sequence[float],
                            n_thresholds: int = 100) -> Tuple[List[float], List[float], List[float]]:
    """
Compute ROC curve points.

Args:
    y_true: True binary labels
    y_scores: Anomaly scores
    n_thresholds: Number of thresholds to evaluate

Returns:
    Tuple of (FPR, TPR, thresholds)
"""
    y_true_arr = np.array(y_true)
    y_scores_arr = np.array(y_scores)

    thresholds = np.linspace(0, 1, n_thresholds)
    fpr_list = []
    tpr_list = []

    for thresh in thresholds:
        y_pred = (y_scores_arr >= thresh).astype(int)
        confusion = generate_confusion_matrix(y_true_arr, y_pred)

        fp = confusion["false_positives"]
        tn = confusion["true_negatives"]
        fn = confusion["false_negatives"]
        tp = confusion["true_positives"]

        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        fpr_list.append(float(fpr))
        tpr_list.append(float(tpr))

    return fpr_list, tpr_list, thresholds.tolist()


def compute_pr_curve_points(y_true: Sequence[Union[int, bool]],
                           y_scores: Sequence[float],
                           n_thresholds: int = 100) -> Tuple[List[float], List[float], List[float]]:
    """
Compute Precision-Recall curve points.

Args:
    y_true: True binary labels
    y_scores: Anomaly scores
    n_thresholds: Number of thresholds to evaluate

Returns:
    Tuple of (precision, recall, thresholds)
"""
    y_true_arr = np.array(y_true)
    y_scores_arr = np.array(y_scores)

    thresholds = np.linspace(0, 1, n_thresholds)
    precision_list = []
    recall_list = []

    for thresh in thresholds:
        y_pred = (y_scores_arr >= thresh).astype(int)
        confusion = generate_confusion_matrix(y_true_arr, y_pred)

        precision = compute_precision(
            confusion["true_positives"],
            confusion["false_positives"]
        )
        recall = compute_recall(
            confusion["true_positives"],
            confusion["false_negatives"]
        )

        precision_list.append(precision)
        recall_list.append(recall)

    return precision_list, recall_list, thresholds.tolist()


def main() -> None:
    """Main entry point for metrics testing."""
    logger.info("Evaluation Metrics Test")

    # Generate test data
    np.random.seed(42)
    y_true = np.random.randint(0, 2, 100)
    y_pred = np.random.randint(0, 2, 100)
    y_scores = np.random.rand(100)

    # Compute metrics
    metrics = compute_all_metrics(y_true, y_pred, y_scores)

    logger.info(f"F1-score: {metrics.f1_score:.4f}")
    logger.info(f"Precision: {metrics.precision:.4f}")
    logger.info(f"Recall: {metrics.recall:.4f}")
    logger.info(f"AUC-ROC: {metrics.auc_roc:.4f}")
    logger.info(f"AUC-PR: {metrics.auc_pr:.4f}")

    # Save confusion matrix plot
    plot_path = "paper/figures/confusion_matrix.png"
    save_confusion_matrix_plot(metrics.to_dict(), plot_path)

    logger.info("Test completed successfully")


if __name__ == "__main__":
    main()
