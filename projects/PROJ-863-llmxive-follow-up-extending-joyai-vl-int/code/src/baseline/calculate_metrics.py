import json
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.baseline.deterministic_detector import DeterministicPrediction, load_raw_frames
from src.data_synthesis.visual_labeler import FrameLabel
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_predictions(pred_path: Path) -> List[Dict[str, Any]]:
    """Load predictions from a JSONL file."""
    if not pred_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {pred_path}")
    
    predictions = []
    with open(pred_path, 'r') as f:
        for line in f:
            if line.strip():
                predictions.append(json.loads(line))
    return predictions

def load_ground_truth(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load ground truth labels from the manifest JSONL file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    ground_truth = []
    with open(manifest_path, 'r') as f:
        for line in f:
            if line.strip():
                ground_truth.append(json.loads(line))
    return ground_truth

def calculate_metrics(
    predictions: List[Dict[str, Any]], 
    ground_truth: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate F1, AUC, and Interruption Reduction metrics.
    
    Args:
        predictions: List of prediction records with 'is_critical' or 'label'
        ground_truth: List of ground truth records with 'is_critical' or 'label'
    
    Returns:
        Dictionary with F1, AUC, and Interruption Reduction Rate
    """
    if len(predictions) != len(ground_truth):
        raise ValueError(
            f"Prediction count ({len(predictions)}) does not match "
            f"ground truth count ({len(ground_truth)})"
        )
    
    if len(predictions) == 0:
        logger.warning("No predictions or ground truth to evaluate")
        return {
            'f1_score': 0.0,
            'auc_roc': 0.0,
            'interruption_reduction_rate': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'accuracy': 0.0
        }
    
    # Extract binary labels
    true_labels = []
    pred_labels = []
    
    for gt, pred in zip(ground_truth, predictions):
        # Handle different possible key names
        gt_label = gt.get('is_critical', gt.get('label', 0))
        pred_label = pred.get('is_critical', pred.get('label', 0))
        
        # Ensure boolean/int conversion
        true_labels.append(1 if gt_label else 0)
        pred_labels.append(1 if pred_label else 0)
    
    # Calculate confusion matrix components
    tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(true_labels, pred_labels) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 0)
    
    # Calculate precision, recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Calculate accuracy
    accuracy = (tp + tn) / len(true_labels) if len(true_labels) > 0 else 0.0
    
    # Calculate AUC-ROC (using trapezoidal rule)
    # Sort by prediction score (assuming higher is more critical)
    # For binary predictions, we use the prediction values directly
    auc_roc = calculate_auc_roc(true_labels, pred_labels)
    
    # Calculate Interruption Reduction Rate
    # This measures how many false alarms (interruptions) were avoided
    # compared to a baseline that always interrupts on critical events
    # Formula: (Baseline Interruptions - Actual Interruptions) / Baseline Interruptions
    # Baseline: Always interrupt on actual critical events (tp + fn)
    # Actual: Interrupts on predicted critical events (tp + fp)
    baseline_interruptions = tp + fn  # Total actual critical events
    actual_interruptions = tp + fp    # Total predicted critical events
    
    if baseline_interruptions > 0:
        interruption_reduction_rate = max(0.0, (baseline_interruptions - actual_interruptions) / baseline_interruptions)
    else:
        interruption_reduction_rate = 0.0
    
    return {
        'f1_score': round(f1_score, 4),
        'auc_roc': round(auc_roc, 4),
        'interruption_reduction_rate': round(interruption_reduction_rate, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'accuracy': round(accuracy, 4),
        'true_positives': tp,
        'true_negatives': tn,
        'false_positives': fp,
        'false_negatives': fn,
        'total_samples': len(true_labels)
    }

def calculate_auc_roc(y_true: List[int], y_pred: List[int]) -> float:
    """
    Calculate AUC-ROC using the trapezoidal rule.
    For binary predictions, this is equivalent to the probability that
    a randomly chosen positive example is ranked higher than a negative one.
    """
    if len(y_true) == 0:
        return 0.0
    
    # Sort by prediction score (descending)
    pairs = list(zip(y_pred, y_true))
    pairs.sort(key=lambda x: x[0], reverse=True)
    
    y_pred_sorted = [p[0] for p in pairs]
    y_true_sorted = [p[1] for p in pairs]
    
    n_pos = sum(y_true_sorted)
    n_neg = len(y_true_sorted) - n_pos
    
    if n_pos == 0 or n_neg == 0:
        return 0.5  # No meaningful AUC if all same class
    
    # Calculate AUC using trapezoidal rule
    tpr_prev = 0.0
    fpr_prev = 0.0
    auc = 0.0
    tp_count = 0
    fp_count = 0
    
    for i in range(len(y_pred_sorted)):
        if y_true_sorted[i] == 1:
            tp_count += 1
        else:
            fp_count += 1
        
        tpr = tp_count / n_pos
        fpr = fp_count / n_neg
        
        # Trapezoidal integration
        auc += (fpr - fpr_prev) * (tpr + tpr_prev) / 2
        
        tpr_prev = tpr
        fpr_prev = fpr
    
    return auc

def main():
    """Main function to calculate baseline metrics and save to JSON."""
    logger.info("Starting baseline metrics calculation")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    baseline_dir = data_dir / "baseline"
    
    # Ensure output directory exists
    baseline_dir.mkdir(parents=True, exist_ok=True)
    
    # Load deterministic predictions
    det_pred_path = baseline_dir / "deterministic_predictions.jsonl"
    manifest_path = data_dir / "manifest.jsonl"
    
    try:
        logger.info(f"Loading deterministic predictions from {det_pred_path}")
        det_predictions = load_predictions(det_pred_path)
        
        logger.info(f"Loading ground truth from {manifest_path}")
        ground_truth = load_ground_truth(manifest_path)
        
        logger.info(f"Calculating metrics for deterministic detector")
        det_metrics = calculate_metrics(det_predictions, ground_truth)
        
        # Load noisy predictions if available
        noisy_pred_path = baseline_dir / "noisy_predictions.jsonl"
        noisy_metrics = None
        
        if noisy_pred_path.exists():
            logger.info(f"Loading noisy predictions from {noisy_pred_path}")
            noisy_predictions = load_predictions(noisy_pred_path)
            logger.info(f"Calculating metrics for noisy detector")
            noisy_metrics = calculate_metrics(noisy_predictions, ground_truth)
        else:
            logger.warning(f"Noisy predictions file not found: {noisy_pred_path}")
        
        # Compile results
        results = {
            "deterministic": det_metrics,
            "noisy": noisy_metrics,
            "calculation_timestamp": "N/A",  # Could add datetime if needed
            "total_samples": det_metrics.get("total_samples", 0)
        }
        
        # Save metrics
        metrics_path = baseline_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Metrics saved to {metrics_path}")
        logger.info(f"Deterministic F1: {det_metrics['f1_score']}, AUC: {det_metrics['auc_roc']}, Interruption Reduction: {det_metrics['interruption_reduction_rate']}")
        
        if noisy_metrics:
            logger.info(f"Noisy F1: {noisy_metrics['f1_score']}, AUC: {noisy_metrics['auc_roc']}, Interruption Reduction: {noisy_metrics['interruption_reduction_rate']}")
        
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise

if __name__ == "__main__":
    main()
