import json
import time
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats

# Import existing utilities from the project
from src.utils.logging import get_logger
from src.utils.validation import validate_jsonl_file, ValidationError

# Configure logging
logger = get_logger(__name__)

@dataclass
class EvaluationMetrics:
    auc_roc: float
    cohen_kappa: float
    interruption_reduction_rate: float
    safety_recall: float
    mean_inference_latency_ms: float
    total_samples: int
    positive_predictions: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

def load_predictions(file_path: Path) -> List[Dict[str, Any]]:
    """Load predictions from a JSONL file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {file_path}")
    
    predictions = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                predictions.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num} in {file_path}: {e}")
    
    logger.info(f"Loaded {len(predictions)} predictions from {file_path}")
    return predictions

def load_ground_truth(file_path: Path) -> List[Dict[str, Any]]:
    """Load ground truth labels from a JSONL file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")
    
    ground_truth = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                ground_truth.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num} in {file_path}: {e}")
    
    logger.info(f"Loaded {len(ground_truth)} ground truth records from {file_path}")
    return ground_truth

def load_features_from_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load all feature records from JSONL files listed in the manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Feature manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    feature_files = manifest.get('feature_files', [])
    all_features = []
    
    for file_entry in feature_files:
        file_path = Path(file_entry['path'])
        if not file_path.exists():
            logger.warning(f"Feature file not found: {file_path}")
            continue
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    all_features.append(record)
                except json.JSONDecodeError:
                    continue
    
    logger.info(f"Loaded {len(all_features)} feature records from manifest")
    return all_features

def calculate_auc_roc(y_true: List[int], y_scores: List[float]) -> float:
    """Calculate AUC-ROC score."""
    if len(y_true) != len(y_scores):
        raise ValueError(f"Mismatch in lengths: y_true={len(y_true)}, y_scores={len(y_scores)}")
    
    if len(set(y_true)) < 2:
        logger.warning("Only one class present in y_true, returning 0.5 AUC")
        return 0.5
    
    # Sort by scores
    sorted_pairs = sorted(zip(y_scores, y_true), key=lambda x: x[0], reverse=True)
    
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    
    if n_pos == 0 or n_neg == 0:
        return 0.5
    
    # Calculate AUC using trapezoidal rule
    tpr_prev = 0.0
    fpr_prev = 0.0
    auc = 0.0
    tp = 0
    fp = 0
    
    prev_score = None
    for score, label in sorted_pairs:
        if prev_score is not None and score != prev_score:
            tpr = tp / n_pos
            fpr = fp / n_neg
            auc += (fpr - fpr_prev) * (tpr + tpr_prev) / 2
            tpr_prev = tpr
            fpr_prev = fpr
        
        if label == 1:
            tp += 1
        else:
            fp += 1
        prev_score = score
    
    # Final point
    tpr = tp / n_pos
    fpr = fp / n_neg
    auc += (fpr - fpr_prev) * (tpr + tpr_prev) / 2
    
    return auc

def calculate_cohen_kappa(y_true: List[int], y_pred: List[int]) -> float:
    """Calculate Cohen's Kappa coefficient."""
    if len(y_true) != len(y_pred):
        raise ValueError(f"Mismatch in lengths: y_true={len(y_true)}, y_pred={len(y_pred)}")
    
    n = len(y_true)
    if n == 0:
        return 0.0
    
    # Calculate observed agreement
    po = sum(1 for t, p in zip(y_true, y_pred) if t == p) / n
    
    # Calculate expected agreement
    classes = sorted(set(y_true) | set(y_pred))
    if len(classes) < 2:
        return 0.0
    
    # Binary case: classes are 0 and 1
    if len(classes) == 2 and 0 in classes and 1 in classes:
        p0 = sum(1 for t in y_true if t == 0) / n
        p1 = sum(1 for t in y_true if t == 1) / n
        q0 = sum(1 for p in y_pred if p == 0) / n
        q1 = sum(1 for p in y_pred if p == 1) / n
        
        pe = p0 * q0 + p1 * q1
    else:
        # General case
        pe = 0.0
        for c in classes:
            p_c = sum(1 for t in y_true if t == c) / n
            q_c = sum(1 for p in y_pred if p == c) / n
            pe += p_c * q_c
    
    if pe == 1.0:
        return 0.0
    
    kappa = (po - pe) / (1 - pe)
    return kappa

def calculate_interruption_reduction_rate(baseline_interruptions: int, 
                                           scheduler_interruptions: int, 
                                           total_frames: int) -> float:
    """
    Calculate Interruption Reduction Rate.
    IRR = 1 - (scheduler_interruptions / baseline_interruptions)
    If baseline_interruptions is 0, return 0.0 to avoid division by zero.
    """
    if baseline_interruptions == 0:
        return 0.0
    return 1.0 - (scheduler_interruptions / baseline_interruptions)

def calculate_safety_recall(y_true: List[int], y_pred: List[int]) -> float:
    """
    Calculate Safety Recall (Recall for positive class).
    Safety Recall = TP / (TP + FN)
    """
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)

def calculate_inference_latency(latencies: List[float]) -> float:
    """Calculate mean inference latency in milliseconds."""
    if not latencies:
        return 0.0
    return sum(latencies) / len(latencies)

def align_predictions_with_ground_truth(predictions: List[Dict[str, Any]], 
                                         ground_truth: List[Dict[str, Any]]) -> Tuple[List[int], List[int], List[int], List[float]]:
    """
    Align predictions with ground truth by frame_id or timestamp.
    Returns: (y_true, y_pred, baseline_pred, y_scores)
    """
    # Create lookup dictionaries
    gt_lookup = {gt.get('frame_id', gt.get('timestamp', i)): gt for i, gt in enumerate(ground_truth)}
    pred_lookup = {pred.get('frame_id', pred.get('timestamp', i)): pred for i, pred in enumerate(predictions)}
    
    # Get common keys
    common_keys = set(gt_lookup.keys()) & set(pred_lookup.keys())
    
    if not common_keys:
        raise ValueError("No common frame_ids/timestamps between predictions and ground truth")
    
    y_true = []
    y_pred = []
    baseline_pred = []
    y_scores = []
    
    for key in sorted(common_keys):
        gt_record = gt_lookup[key]
        pred_record = pred_lookup[key]
        
        # Extract ground truth label (1 for critical, 0 for silence)
        gt_label = gt_record.get('label', gt_record.get('is_critical', 0))
        if isinstance(gt_label, str):
            gt_label = 1 if gt_label.lower() in ['critical', 'fall', 'alert'] else 0
        
        # Extract scheduler prediction (binary)
        pred_label = pred_record.get('prediction', pred_record.get('is_intervention', 0))
        if isinstance(pred_label, str):
            pred_label = 1 if pred_label.lower() in ['true', '1', 'yes', 'critical'] else 0
        
        # Extract baseline prediction if available
        baseline_label = pred_record.get('baseline_prediction', pred_record.get('deterministic_label', 0))
        if isinstance(baseline_label, str):
            baseline_label = 1 if baseline_label.lower() in ['true', '1', 'yes', 'critical'] else 0
        
        # Extract probability score for AUC calculation
        score = pred_record.get('probability', pred_record.get('confidence', pred_record.get('score', 0.5)))
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                score = 0.5
        
        y_true.append(int(gt_label))
        y_pred.append(int(pred_label))
        baseline_pred.append(int(baseline_label))
        y_scores.append(float(score))
    
    logger.info(f"Aligned {len(y_true)} samples for evaluation")
    return y_true, y_pred, baseline_pred, y_scores

def evaluate_scheduler(predictions_path: Path, 
                       ground_truth_path: Path, 
                       baseline_predictions_path: Optional[Path] = None,
                       features_manifest_path: Optional[Path] = None) -> EvaluationMetrics:
    """
    Main evaluation function that calculates all required metrics.
    """
    logger.info(f"Evaluating scheduler with predictions: {predictions_path}")
    logger.info(f"Using ground truth: {ground_truth_path}")
    
    # Load data
    predictions = load_predictions(predictions_path)
    ground_truth = load_ground_truth(ground_truth_path)
    
    # Load baseline predictions if available
    baseline_predictions = []
    if baseline_predictions_path and baseline_predictions_path.exists():
        baseline_predictions = load_predictions(baseline_predictions_path)
        logger.info(f"Loaded {len(baseline_predictions)} baseline predictions")
    
    # Align data
    y_true, y_pred, baseline_pred, y_scores = align_predictions_with_ground_truth(
        predictions, ground_truth
    )
    
    # Calculate metrics
    auc_roc = calculate_auc_roc(y_true, y_scores)
    cohen_kappa = calculate_cohen_kappa(y_true, y_pred)
    
    # Interruption Reduction Rate
    baseline_interruptions = sum(baseline_pred) if baseline_pred else sum(y_pred)
    scheduler_interruptions = sum(y_pred)
    interruption_reduction_rate = calculate_interruption_reduction_rate(
        baseline_interruptions, scheduler_interruptions, len(y_true)
    )
    
    # Safety Recall
    safety_recall = calculate_safety_recall(y_true, y_pred)
    
    # Calculate inference latency from predictions if available
    latencies = []
    for pred in predictions:
        if 'inference_latency_ms' in pred:
            latencies.append(pred['inference_latency_ms'])
        elif 'latency_ms' in pred:
            latencies.append(pred['latency_ms'])
    
    mean_latency = calculate_inference_latency(latencies)
    
    # Calculate confusion matrix components
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    
    metrics = EvaluationMetrics(
        auc_roc=auc_roc,
        cohen_kappa=cohen_kappa,
        interruption_reduction_rate=interruption_reduction_rate,
        safety_recall=safety_recall,
        mean_inference_latency_ms=mean_latency,
        total_samples=len(y_true),
        positive_predictions=sum(y_pred),
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn
    )
    
    logger.info(f"Evaluation complete: AUC={auc_roc:.4f}, Kappa={cohen_kappa:.4f}, "
               f"IRR={interruption_reduction_rate:.4f}, Recall={safety_recall:.4f}, "
               f"Latency={mean_latency:.2f}ms")
    
    return metrics

def save_evaluation_results(metrics: EvaluationMetrics, output_path: Path) -> None:
    """Save evaluation results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = asdict(metrics)
    results['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved evaluation results to {output_path}")

def main():
    """Main entry point for evaluation script."""
    logger.info("Starting scheduler evaluation...")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    predictions_path = project_root / 'data' / 'scheduler' / 'predictions.jsonl'
    ground_truth_path = project_root / 'data' / 'raw' / 'manifest.jsonl'
    baseline_path = project_root / 'data' / 'baseline' / 'noisy_predictions.jsonl'
    features_manifest = project_root / 'data' / 'features' / 'manifest.json'
    output_path = project_root / 'data' / 'evaluation' / 'scheduler_metrics.json'
    
    # Allow override via environment variables
    if 'PREDICTIONS_PATH' in os.environ:
        predictions_path = Path(os.environ['PREDICTIONS_PATH'])
    if 'GROUND_TRUTH_PATH' in os.environ:
        ground_truth_path = Path(os.environ['GROUND_TRUTH_PATH'])
    if 'BASELINE_PATH' in os.environ:
        baseline_path = Path(os.environ['BASELINE_PATH'])
    if 'OUTPUT_PATH' in os.environ:
        output_path = Path(os.environ['OUTPUT_PATH'])
    
    try:
        # Run evaluation
        metrics = evaluate_scheduler(
            predictions_path=predictions_path,
            ground_truth_path=ground_truth_path,
            baseline_predictions_path=baseline_path,
            features_manifest_path=features_manifest
        )
        
        # Save results
        save_evaluation_results(metrics, output_path)
        
        # Print summary
        print("\n=== Scheduler Evaluation Results ===")
        print(f"Total Samples: {metrics.total_samples}")
        print(f"AUC-ROC: {metrics.auc_roc:.4f}")
        print(f"Cohen's Kappa: {metrics.cohen_kappa:.4f}")
        print(f"Interruption Reduction Rate: {metrics.interruption_reduction_rate:.4f}")
        print(f"Safety Recall: {metrics.safety_recall:.4f}")
        print(f"Mean Inference Latency: {metrics.mean_inference_latency_ms:.2f} ms")
        print(f"True Positives: {metrics.true_positives}")
        print(f"False Positives: {metrics.false_positives}")
        print(f"True Negatives: {metrics.true_negatives}")
        print(f"False Negatives: {metrics.false_negatives}")
        print(f"Results saved to: {output_path}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
