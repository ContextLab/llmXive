import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.models.data_models import AuditRecord

logger = get_default_logger("evaluation")

def load_synthetic_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load synthetic summaries from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Synthetic summaries file not found: {path}")
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ['n_control', 'n_treatment', 'success_control', 'success_treatment']:
                if key in row and row[key]:
                    row[key] = int(row[key])
            for key in ['p_value_reported', 'effect_size_reported']:
                if key in row and row[key]:
                    row[key] = float(row[key])
            records.append(row)
    return records

def load_ground_truth(path: Path) -> List[Dict[str, Any]]:
    """Load ground truth from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])

def evaluate_detection(audit_records: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate inconsistency detection component.
    
    Compares audit results against ground truth to compute precision, recall, and F1.
    
    Args:
        audit_records: List of audit records with 'is_inconsistent' flag
        ground_truth: List of ground truth records with 'is_inconsistent' flag
    
    Returns:
        Dictionary with precision, recall, F1, and counts
    """
    # Create lookup by ID
    gt_lookup = {rec.get('id'): rec for rec in ground_truth}
    
    tp = 0  # True Positives: detected inconsistent and actually inconsistent
    fp = 0  # False Positives: detected inconsistent but actually consistent
    fn = 0  # False Negatives: detected consistent but actually inconsistent
    tn = 0  # True Negatives: detected consistent and actually consistent
    
    for audit_rec in audit_records:
        record_id = audit_rec.get('id')
        if record_id not in gt_lookup:
            logger.warning(f"Audit record {record_id} not found in ground truth, skipping")
            continue
        
        gt_rec = gt_lookup[record_id]
        detected_inconsistent = audit_rec.get('is_inconsistent', False)
        actual_inconsistent = gt_rec.get('is_inconsistent', False)
        
        if detected_inconsistent and actual_inconsistent:
            tp += 1
        elif detected_inconsistent and not actual_inconsistent:
            fp += 1
        elif not detected_inconsistent and actual_inconsistent:
            fn += 1
        else:
            tn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': tp,
        'false_positives': fp,
        'true_negatives': tn,
        'false_negatives': fn,
        'total_evaluated': tp + fp + tn + fn
    }

def validate_summary(metrics: Dict[str, float], thresholds: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Validate that metrics meet required thresholds.
    
    Args:
        metrics: Dictionary with precision, recall, f1
        thresholds: Dictionary with minimum required values
    
    Returns:
        Tuple of (passed, list of failure messages)
    """
    failures = []
    
    if metrics['precision'] < thresholds['precision']:
        failures.append(f"Precision {metrics['precision']:.4f} < required {thresholds['precision']}")
    
    if metrics['recall'] < thresholds['recall']:
        failures.append(f"Recall {metrics['recall']:.4f} < required {thresholds['recall']}")
    
    if metrics['f1'] < thresholds['f1']:
        failures.append(f"F1 {metrics['f1']:.4f} < required {thresholds['f1']}")
    
    return len(failures) == 0, failures

def write_evaluation_results(results: Dict[str, Any], output_path: Path):
    """Write evaluation results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Evaluation results written to {output_path}")

def main():
    """Main entry point for evaluation."""
    logger.info("Starting inconsistency detection evaluation")
    
    # Define paths
    synthetic_csv = Path("data/synthetic/synthetic_validation.csv")
    ground_truth_json = Path("data/synthetic/synthetic_ground_truth.json")
    audit_report_json = Path("output/audit_report.json")
    evaluation_output = Path("output/evaluation_results.json")
    
    # Thresholds per FR-031
    thresholds = {
        'precision': 0.90,
        'recall': 0.80,
        'f1': 0.85
    }
    
    try:
        # Load data
        logger.info(f"Loading synthetic summaries from {synthetic_csv}")
        synthetic_summaries = load_synthetic_summaries(synthetic_csv)
        logger.info(f"Loaded {len(synthetic_summaries)} synthetic summaries")
        
        logger.info(f"Loading ground truth from {ground_truth_json}")
        ground_truth = load_ground_truth(ground_truth_json)
        logger.info(f"Loaded {len(ground_truth)} ground truth records")
        
        # Load audit results
        logger.info(f"Loading audit report from {audit_report_json}")
        if not audit_report_json.exists():
            error_msg = get_error_message("ERR-800")
            raise RuntimeError(f"Audit report not found: {audit_report_json}. {error_msg}")
        
        with open(audit_report_json, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        
        audit_records = audit_data.get('records', [])
        logger.info(f"Loaded {len(audit_records)} audit records")
        
        # Evaluate
        logger.info("Computing detection metrics")
        metrics = evaluate_detection(audit_records, ground_truth)
        logger.info(f"Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}, F1: {metrics['f1']:.4f}")
        
        # Validate against thresholds
        passed, failures = validate_summary(metrics, thresholds)
        
        # Add metadata
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'thresholds': thresholds,
            'passed': passed,
            'failures': failures
        }
        
        # Write results
        write_evaluation_results(results, evaluation_output)
        
        if not passed:
            error_msg = get_error_message("ERR-800")
            logger.error(f"Evaluation failed: {failures}. {error_msg}")
            raise RuntimeError(f"Evaluation failed: {failures}. {error_msg}")
        
        logger.info("Evaluation passed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main() or 0)
