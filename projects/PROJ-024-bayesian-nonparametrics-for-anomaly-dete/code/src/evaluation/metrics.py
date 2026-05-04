"""
Evaluation metrics module for anomaly detection models.

Provides functions for computing classification metrics (F1-score, precision, recall, AUC),
generating confusion matrices, and creating evaluation plots (ROC, PR curves).

All metrics support numpy type serialization for JSON output.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union, Sequence
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json
import csv

# Optional imports with graceful fallback
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    logging.warning("matplotlib/seaborn not available - plot generation disabled")

try:
    from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve, auc
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logging.warning("scikit-learn not available - using custom implementations")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class EvaluationMetrics:
    """Container for all evaluation metrics computed for a model."""
    f1_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    auc_roc: float = 0.0
    auc_pr: float = 0.0
    confusion_matrix: Optional[List[List[int]]] = None
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    model_name: str = "unknown"
    dataset_name: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    threshold: float = 0.5
    support: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'f1_score': float(self.f1_score),
            'precision': float(self.precision),
            'recall': float(self.recall),
            'auc_roc': float(self.auc_roc),
            'auc_pr': float(self.auc_pr),
            'confusion_matrix': self.confusion_matrix,
            'true_positives': int(self.true_positives),
            'false_positives': int(self.false_positives),
            'true_negatives': int(self.true_negatives),
            'false_negatives': int(self.false_negatives),
            'model_name': self.model_name,
            'dataset_name': self.dataset_name,
            'timestamp': self.timestamp,
            'threshold': float(self.threshold),
            'support': int(self.support)
        }
    
    def save_json(self, output_path: Union[str, Path]) -> None:
        """Save metrics to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved evaluation metrics to {output_path}")

# ============================================================================
# Utility Functions for Type Conversion
# ============================================================================

def _convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_numpy_types(item) for item in obj]
    return obj

# ============================================================================
# Core Metric Computation Functions
# ============================================================================

def compute_f1_score(y_true: Sequence[Union[int, float]], 
                     y_pred: Sequence[Union[int, float]], 
                     average: str = 'binary') -> float:
    """
    Compute F1-score (harmonic mean of precision and recall).
    
    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        average: 'binary' for binary classification, 'macro' or 'weighted' for multi-class
    
    Returns:
        F1-score as float between 0 and 1
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    if not HAS_SKLEARN:
        # Custom implementation
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return float(f1)
    else:
        from sklearn.metrics import f1_score as sklearn_f1_score
        return float(sklearn_f1_score(y_true, y_pred, average=average))

def compute_precision(y_true: Sequence[Union[int, float]], 
                     y_pred: Sequence[Union[int, float]]) -> float:
    """
    Compute precision (true positives / (true positives + false positives)).
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
    
    Returns:
        Precision as float between 0 and 1
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    return float(precision)

def compute_recall(y_true: Sequence[Union[int, float]], 
                  y_pred: Sequence[Union[int, float]]) -> float:
    """
    Compute recall (true positives / (true positives + false negatives)).
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
    
    Returns:
        Recall as float between 0 and 1
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return float(recall)

def compute_auc(y_true: Sequence[Union[int, float]], 
               y_score: Sequence[Union[int, float]], 
               curve_type: str = 'roc') -> float:
    """
    Compute Area Under Curve for ROC or PR curve.
    
    Args:
        y_true: Ground truth labels
        y_score: Prediction scores (probabilities or anomaly scores)
        curve_type: 'roc' for ROC-AUC, 'pr' for PR-AUC
    
    Returns:
        AUC value as float between 0 and 1
    """
    y_true = np.array(y_true)
    y_score = np.array(y_score)
    
    if not HAS_SKLEARN:
        # Custom trapezoidal integration
        if curve_type == 'roc':
            fpr, tpr, _ = compute_roc_curve_points(y_true, y_score)
        else:
            prec, rec, _ = compute_pr_curve_points(y_true, y_score)
            fpr, tpr = rec, prec  # Swap for PR curve
        return float(auc_custom(fpr, tpr))
    else:
        from sklearn.metrics import roc_auc_score, average_precision_score
        if curve_type == 'roc':
            return float(roc_auc_score(y_true, y_score))
        else:
            return float(average_precision_score(y_true, y_score))

def auc_custom(x: np.ndarray, y: np.ndarray) -> float:
    """Custom trapezoidal integration for AUC calculation."""
    x = np.array(x)
    y = np.array(y)
    return float(np.trapz(y, x))

# ============================================================================
# Confusion Matrix Functions (T042 Implementation)
# ============================================================================

def generate_confusion_matrix(y_true: Sequence[Union[int, float]], 
                              y_pred: Sequence[Union[int, float]]) -> Dict[str, Any]:
    """
    Generate confusion matrix from true and predicted labels.
    
    Args:
        y_true: Ground truth labels (0 or 1 for binary classification)
        y_pred: Predicted labels (0 or 1 for binary classification)
    
    Returns:
        Dictionary containing:
            - matrix: 2x2 confusion matrix as nested list
            - tp: true positives
            - fp: false positives
            - tn: true negatives
            - fn: false negatives
            - accuracy: overall accuracy
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Compute confusion matrix components
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    
    # Build 2x2 matrix: [[TN, FP], [FN, TP]]
    # Convention: rows = actual, cols = predicted
    matrix = [[tn, fp], 
              [fn, tp]]
    
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0
    
    return {
        'matrix': matrix,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn,
        'accuracy': float(accuracy),
        'total': total
    }

def save_confusion_matrix_plot(cm_data: Dict[str, Any], 
                               output_path: Union[str, Path],
                               title: str = "Confusion Matrix",
                               figsize: Tuple[int, int] = (8, 6)) -> None:
    """
    Save confusion matrix as a visualization (PNG).
    
    Args:
        cm_data: Dictionary from generate_confusion_matrix()
        output_path: Path to save the plot
        title: Plot title
        figsize: Figure size in inches
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not HAS_PLOT:
        logger.warning("matplotlib not available - cannot save confusion matrix plot")
        # Save as text file instead
        text_path = output_path.with_suffix('.txt')
        with open(text_path, 'w') as f:
            f.write(f"Confusion Matrix: {title}\n")
            f.write(f"Matrix: {cm_data['matrix']}\n")
            f.write(f"TP: {cm_data['tp']}, FP: {cm_data['fp']}, TN: {cm_data['tn']}, FN: {cm_data['fn']}\n")
            f.write(f"Accuracy: {cm_data['accuracy']:.4f}\n")
        logger.info(f"Saved confusion matrix text to {text_path}")
        return
    
    matrix = cm_data['matrix']
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use seaborn for heatmap visualization
    sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues',
               xticklabels=['Predicted Neg', 'Predicted Pos'],
               yticklabels=['Actual Neg', 'Actual Pos'],
               ax=ax)
    
    ax.set_title(title)
    ax.set_xlabel('Predicted Label')
    ax.set_ylabel('Actual Label')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved confusion matrix plot to {output_path}")

def save_confusion_matrix_data(cm_data: Dict[str, Any],
                               output_path: Union[str, Path]) -> None:
    """
    Save confusion matrix data to CSV and JSON formats.
    
    Args:
        cm_data: Dictionary from generate_confusion_matrix()
        output_path: Base path (without extension) for output files
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as CSV
    csv_path = output_path.with_suffix('.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Actual\\Predicted', 'Negative', 'Positive'])
        writer.writerow(['Negative', cm_data['matrix'][0][0], cm_data['matrix'][0][1]])
        writer.writerow(['Positive', cm_data['matrix'][1][0], cm_data['matrix'][1][1]])
    
    # Save as JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(_convert_numpy_types(cm_data), f, indent=2)
    
    logger.info(f"Saved confusion matrix data to {csv_path} and {json_path}")

def compute_all_metrics(y_true: Sequence[Union[int, float]], 
                        y_pred: Sequence[Union[int, float]],
                        y_score: Optional[Sequence[Union[int, float]]] = None,
                        model_name: str = "unknown",
                        dataset_name: str = "unknown",
                        threshold: float = 0.5) -> EvaluationMetrics:
    """
    Compute all evaluation metrics and return as EvaluationMetrics object.
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels (thresholded)
        y_score: Prediction scores (optional, for AUC computation)
        model_name: Name of the model being evaluated
        dataset_name: Name of the dataset used
        threshold: Threshold used for binary classification
    
    Returns:
        EvaluationMetrics object with all computed metrics
    """
    # Convert to numpy arrays
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Generate confusion matrix
    cm = generate_confusion_matrix(y_true, y_pred)
    
    # Compute metrics
    f1 = compute_f1_score(y_true, y_pred)
    prec = compute_precision(y_true, y_pred)
    rec = compute_recall(y_true, y_pred)
    
    auc_roc = 0.0
    auc_pr = 0.0
    if y_score is not None:
        y_score = np.array(y_score)
        auc_roc = compute_auc(y_true, y_score, 'roc')
        auc_pr = compute_auc(y_true, y_score, 'pr')
    
    return EvaluationMetrics(
        f1_score=f1,
        precision=prec,
        recall=rec,
        auc_roc=auc_roc,
        auc_pr=auc_pr,
        confusion_matrix=cm['matrix'],
        true_positives=cm['tp'],
        false_positives=cm['fp'],
        true_negatives=cm['tn'],
        false_negatives=cm['fn'],
        model_name=model_name,
        dataset_name=dataset_name,
        threshold=threshold,
        support=int(len(y_true))
    )

# ============================================================================
# ROC and PR Curve Functions
# ============================================================================

def compute_roc_curve_points(y_true: Sequence[Union[int, float]], 
                             y_score: Sequence[Union[int, float]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute ROC curve points (FPR, TPR, thresholds).
    
    Args:
        y_true: Ground truth labels
        y_score: Prediction scores
    
    Returns:
        Tuple of (FPR array, TPR array, thresholds array)
    """
    if not HAS_SKLEARN:
        # Custom implementation
        y_true = np.array(y_true)
        y_score = np.array(y_score)
        
        thresholds = np.sort(np.unique(y_score))[::-1]
        fpr_list = []
        tpr_list = []
        
        n_pos = np.sum(y_true == 1)
        n_neg = np.sum(y_true == 0)
        
        for thresh in thresholds:
            y_pred = (y_score >= thresh).astype(int)
            tp = np.sum((y_true == 1) & (y_pred == 1))
            fp = np.sum((y_true == 0) & (y_pred == 1))
            
            tpr = tp / n_pos if n_pos > 0 else 0.0
            fpr = fp / n_neg if n_neg > 0 else 0.0
            
            fpr_list.append(fpr)
            tpr_list.append(tpr)
        
        return np.array(fpr_list), np.array(tpr_list), thresholds
    else:
        from sklearn.metrics import roc_curve
        return roc_curve(y_true, y_score)

def compute_pr_curve_points(y_true: Sequence[Union[int, float]], 
                            y_score: Sequence[Union[int, float]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Precision-Recall curve points.
    
    Args:
        y_true: Ground truth labels
        y_score: Prediction scores
    
    Returns:
        Tuple of (precision array, recall array, thresholds array)
    """
    if not HAS_SKLEARN:
        # Custom implementation
        y_true = np.array(y_true)
        y_score = np.array(y_score)
        
        thresholds = np.sort(np.unique(y_score))[::-1]
        prec_list = []
        rec_list = []
        
        for thresh in thresholds:
            y_pred = (y_score >= thresh).astype(int)
            tp = np.sum((y_true == 1) & (y_pred == 1))
            fp = np.sum((y_true == 0) & (y_pred == 1))
            fn = np.sum((y_true == 1) & (y_pred == 0))
            
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            prec_list.append(prec)
            rec_list.append(rec)
        
        return np.array(prec_list), np.array(rec_list), thresholds
    else:
        from sklearn.metrics import precision_recall_curve
        return precision_recall_curve(y_true, y_score)

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    Test all metric computation functions with synthetic data.
    """
    # Generate synthetic test data
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = 50  # 5% anomaly rate
    
    # Create ground truth
    y_true = np.zeros(n_samples, dtype=int)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    y_true[anomaly_indices] = 1
    
    # Create predictions with some noise
    y_pred = y_true.copy()
    # Add some false positives and false negatives
    flip_indices = np.random.choice(n_samples, 20, replace=False)
    y_pred[flip_indices] = 1 - y_pred[flip_indices]
    
    # Create scores
    y_score = np.random.random(n_samples)
    # Boost scores for actual anomalies
    y_score[anomaly_indices] += 0.3
    y_score = np.clip(y_score, 0, 1)
    
    # Compute all metrics
    metrics = compute_all_metrics(
        y_true=y_true,
        y_pred=y_pred,
        y_score=y_score,
        model_name="DPGMM",
        dataset_name="synthetic_test"
    )
    
    # Print results
    print("=" * 60)
    print("Evaluation Metrics Test")
    print("=" * 60)
    print(f"Model: {metrics.model_name}")
    print(f"Dataset: {metrics.dataset_name}")
    print(f"Samples: {metrics.support}")
    print(f"F1-Score: {metrics.f1_score:.4f}")
    print(f"Precision: {metrics.precision:.4f}")
    print(f"Recall: {metrics.recall:.4f}")
    print(f"ROC-AUC: {metrics.auc_roc:.4f}")
    print(f"PR-AUC: {metrics.auc_pr:.4f}")
    print(f"Confusion Matrix:")
    print(f"  TN={metrics.true_negatives}, FP={metrics.false_positives}")
    print(f"  FN={metrics.false_negatives}, TP={metrics.true_positives}")
    print("=" * 60)
    
    # Generate and save confusion matrix
    cm_data = generate_confusion_matrix(y_true, y_pred)
    print(f"\nConfusion Matrix Data: {cm_data}")
    
    # Save outputs
    output_dir = Path("data/processed/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metrics JSON
    metrics.save_json(output_dir / "test_metrics.json")
    
    # Save confusion matrix data
    save_confusion_matrix_data(cm_data, output_dir / "confusion_matrix")
    
    # Save confusion matrix plot
    save_confusion_matrix_plot(cm_data, output_dir / "confusion_matrix.png")
    
    print(f"\nSaved outputs to {output_dir}")

if __name__ == "__main__":
    main()
