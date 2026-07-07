import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)

def load_synthetic_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load synthetic A/B test summaries from a CSV file."""
    summaries = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            summaries.append(row)
    return summaries

def load_ground_truth(path: Path) -> Dict[str, bool]:
    """
    Load ground truth labels from a CSV file.
    Expected columns: 'id', 'is_inconsistent' (boolean or 'true'/'false'/'1'/'0')
    Returns a dict mapping id -> True (inconsistent) or False (consistent).
    """
    truth_map = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record_id = row.get('id')
            if not record_id:
                logger.warning("Skipping ground truth row without 'id'")
                continue
            
            val = row.get('is_inconsistent', '').strip().lower()
            if val in ('true', '1', 'yes'):
                truth_map[record_id] = True
            elif val in ('false', '0', 'no', ''):
                truth_map[record_id] = False
            else:
                logger.warning(f"Unknown ground truth value '{val}' for id {record_id}")
                truth_map[record_id] = False
    return truth_map

def load_audit_records(path: Path) -> List[Dict[str, Any]]:
    """Load audit records from the JSON report produced by the validator."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        raise ValueError(f"Unexpected audit report format at {path}")

def validate_summary(summary: Dict[str, Any], ground_truth: Dict[str, bool]) -> Tuple[str, bool, bool]:
    """
    Validate a single summary against ground truth.
    Returns (record_id, is_inconsistent_detected, is_actually_inconsistent).
    """
    record_id = summary.get('id') or summary.get('summary_id')
    if not record_id:
        raise ValueError("Summary missing 'id' or 'summary_id'")

    is_actually_inconsistent = ground_truth.get(record_id, False)
    
    # Determine if the audit flagged this as inconsistent
    # The validator produces 'inconsistent' flag or 'data_quality_warning'
    is_inconsistent_detected = summary.get('inconsistent', False)
    if not isinstance(is_inconsistent_detected, bool):
        # Handle string representations
        is_inconsistent_detected = str(is_inconsistent_detected).lower() in ('true', '1', 'yes')

    return record_id, is_inconsistent_detected, is_actually_inconsistent

def evaluate_detection(
    audit_records: List[Dict[str, Any]],
    ground_truth: Dict[str, bool]
) -> Dict[str, float]:
    """
    Compute precision, recall, and F1 score for inconsistency detection.
    
    Precision = TP / (TP + FP)
    Recall = TP / (TP + FN)
    F1 = 2 * (Precision * Recall) / (Precision + Recall)
    
    Where:
    - TP: Detected as inconsistent AND actually inconsistent
    - FP: Detected as inconsistent BUT actually consistent
    - FN: Detected as consistent BUT actually inconsistent
    """
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    for record in audit_records:
        record_id, detected, actual = validate_summary(record, ground_truth)
        
        if detected and actual:
            tp += 1
        elif detected and not actual:
            fp += 1
        elif not detected and actual:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "total_records": tp + fp + fn + tn
    }

def write_evaluation_results(results: Dict[str, Any], output_path: Path) -> None:
    """Write evaluation metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Evaluation results written to {output_path}")

def main() -> int:
    """
    Main entry point for T029: Evaluate inconsistency-detection component.
    
    Expects:
    - Synthetic summaries with ground truth at data/synthetic_validation/summaries_with_ground_truth.csv
    - Audit report at output/audit_report.json
    
    Outputs:
    - output/evaluation_results.json
    
    Returns:
    - 0 if precision >= 0.90 and recall >= 0.80
    - 1 otherwise (triggers ERR-800)
    """
    base_dir = Path(__file__).resolve().parents[3]
    
    # Paths
    synthetic_path = base_dir / "data" / "synthetic_validation" / "summaries_with_ground_truth.csv"
    audit_report_path = base_dir / "output" / "audit_report.json"
    output_path = base_dir / "output" / "evaluation_results.json"

    if not synthetic_path.exists():
        logger.error(f"Synthetic ground truth file not found: {synthetic_path}")
        print(f"ERR-800: Missing synthetic ground truth file at {synthetic_path}")
        return 1

    if not audit_report_path.exists():
        logger.error(f"Audit report not found: {audit_report_path}")
        print(f"ERR-800: Missing audit report at {audit_report_path}")
        return 1

    try:
        logger.info("Loading synthetic summaries and ground truth...")
        summaries = load_synthetic_summaries(synthetic_path)
        ground_truth = load_ground_truth(synthetic_path)
        
        # Note: In our synthetic generation, the CSV contains the ground truth column
        # We use the same file for both summaries and truth mapping
        
        logger.info("Loading audit records...")
        audit_records = load_audit_records(audit_report_path)
        
        logger.info(f"Comparing {len(audit_records)} audit records against ground truth...")
        metrics = evaluate_detection(audit_records, ground_truth)
        
        logger.info(f"Results: Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}, F1={metrics['f1']:.4f}")
        
        write_evaluation_results(metrics, output_path)
        
        # Thresholds per FR-031 / SC-030
        precision_threshold = 0.90
        recall_threshold = 0.80
        
        if metrics['precision'] >= precision_threshold and metrics['recall'] >= recall_threshold:
            logger.info(f"SUCCESS: Precision ({metrics['precision']:.4f}) >= {precision_threshold} AND Recall ({metrics['recall']:.4f}) >= {recall_threshold}")
            return 0
        else:
            msg = f"FAILURE: Precision ({metrics['precision']:.4f}) < {precision_threshold} OR Recall ({metrics['recall']:.4f}) < {recall_threshold}"
            logger.error(msg)
            print(f"ERR-800: {msg}")
            return 1
            
    except Exception as e:
        logger.exception("Evaluation failed with exception")
        print(f"ERR-800: Evaluation failed - {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
