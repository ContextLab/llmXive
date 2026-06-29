"""
Evaluation module for inconsistency-detection component on synthetic validation dataset.

Implements FR-031: Evaluate inconsistency-detection component on synthetic validation dataset.
Computes precision, recall, F1 and asserts precision ≥ 90%, recall ≥ 80%, F1 ≥ 0.85.
Raises ERR-800 if thresholds are not met.
"""
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from code.src.audit.validator import validate_all_summaries, write_audit_report
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants for evaluation thresholds (FR-031)
PRECISION_THRESHOLD = 0.90
RECALL_THRESHOLD = 0.80
F1_THRESHOLD = 0.85

# Error code for evaluation failure
ERR_EVALUATION_FAILED = "ERR-800"

def load_synthetic_summaries(csv_path: Path) -> List[Dict[str, Any]]:
    """Load synthetic A/B test summaries from CSV file."""
    summaries = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            summary = {
                'url': row.get('url', ''),
                'domain': row.get('domain', ''),
                'outcome_type': row.get('outcome_type', 'binary'),
                'sample_size_control': int(row.get('sample_size_control', 0)),
                'sample_size_treatment': int(row.get('sample_size_treatment', 0)),
                'successes_control': int(row.get('successes_control', 0)),
                'successes_treatment': int(row.get('successes_treatment', 0)),
                'reported_p_value': float(row.get('reported_p_value', 0.0)),
                'reported_effect_size': float(row.get('reported_effect_size', 0.0)),
                'baseline_conversion_rate': float(row.get('baseline_conversion_rate', 0.0)),
                'is_inconsistent': row.get('is_inconsistent', 'false').lower() == 'true',
                'inconsistency_reason': row.get('inconsistency_reason', ''),
            }
            summaries.append(summary)
    return summaries

def load_ground_truth(json_path: Path) -> Dict[str, Any]:
    """Load ground truth labels from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_detection(
    summaries: List[Dict[str, Any]],
    ground_truth: Dict[str, Any],
    logger: AuditLogger
) -> Tuple[int, int, int, int, float, float, float]:
    """
    Evaluate inconsistency detection against ground truth.
    
    Returns:
        Tuple of (true_positives, true_negatives, false_positives, false_negatives,
                 precision, recall, f1)
    """
    # Get ground truth labels
    gt_labels = ground_truth.get('labels', {})
    
    tp = 0  # True Positive: flagged as inconsistent (correctly)
    tn = 0  # True Negative: not flagged as inconsistent (correctly)
    fp = 0  # False Positive: flagged as inconsistent (incorrectly)
    fn = 0  # False Negative: not flagged as inconsistent (incorrectly)
    
    for summary in summaries:
        url = summary.get('url', '')
        is_actually_inconsistent = summary.get('is_inconsistent', False)
        
        # Run validation on this summary
        ab_summary = ABTestSummary(
            url=url,
            domain=summary.get('domain', ''),
            outcome_type=summary.get('outcome_type', 'binary'),
            sample_size_control=summary.get('sample_size_control', 0),
            sample_size_treatment=summary.get('sample_size_treatment', 0),
            successes_control=summary.get('successes_control', 0),
            successes_treatment=summary.get('successes_treatment', 0),
            reported_p_value=summary.get('reported_p_value', 0.0),
            reported_effect_size=summary.get('reported_effect_size', 0.0),
            baseline_conversion_rate=summary.get('baseline_conversion_rate', 0.0),
            extraction_timestamp=datetime.now().isoformat()
        )
        
        audit_record = validate_summary(ab_summary, logger)
        is_flagged_inconsistent = audit_record.is_inconsistent
        
        # Compare with ground truth
        if is_actually_inconsistent and is_flagged_inconsistent:
            tp += 1
        elif not is_actually_inconsistent and not is_flagged_inconsistent:
            tn += 1
        elif not is_actually_inconsistent and is_flagged_inconsistent:
            fp += 1
        elif is_actually_inconsistent and not is_flagged_inconsistent:
            fn += 1
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return tp, tn, fp, fn, precision, recall, f1

def validate_summary(summary_dict: Dict[str, Any], logger: AuditLogger) -> AuditRecord:
    """Validate a single summary and return AuditRecord."""
    from code.src.audit.validator import check_p_value_consistency, check_effect_size_consistency, detect_sample_size_mismatch
    
    ab_summary = ABTestSummary(
        url=summary_dict.get('url', ''),
        domain=summary_dict.get('domain', ''),
        outcome_type=summary_dict.get('outcome_type', 'binary'),
        sample_size_control=summary_dict.get('sample_size_control', 0),
        sample_size_treatment=summary_dict.get('sample_size_treatment', 0),
        successes_control=summary_dict.get('successes_control', 0),
        successes_treatment=summary_dict.get('successes_treatment', 0),
        reported_p_value=summary_dict.get('reported_p_value', 0.0),
        reported_effect_size=summary_dict.get('reported_effect_size', 0.0),
        baseline_conversion_rate=summary_dict.get('baseline_conversion_rate', 0.0),
        extraction_timestamp=datetime.now().isoformat()
    )
    
    # Check for inconsistencies
    is_inconsistent = False
    inconsistency_reasons = []
    
    # Sample size mismatch check
    sample_mismatch = detect_sample_size_mismatch(ab_summary)
    if sample_mismatch:
        is_inconsistent = True
        inconsistency_reasons.append("sample_size_mismatch")
    
    # P-value consistency check
    p_consistency = check_p_value_consistency(ab_summary)
    if p_consistency and p_consistency.get('is_inconsistent', False):
        is_inconsistent = True
        inconsistency_reasons.append("p_value_inconsistency")
    
    # Effect size consistency check
    effect_consistency = check_effect_size_consistency(ab_summary)
    if effect_consistency and effect_consistency.get('is_inconsistent', False):
        is_inconsistent = True
        inconsistency_reasons.append("effect_size_inconsistency")
    
    audit_record = AuditRecord(
        url=ab_summary.url,
        domain=ab_summary.domain,
        is_inconsistent=is_inconsistent,
        inconsistency_reasons=inconsistency_reasons,
        validation_timestamp=datetime.now().isoformat(),
        data_quality_warning=None
    )
    
    return audit_record

def write_evaluation_results(
    tp: int, tn: int, fp: int, fn: int,
    precision: float, recall: float, f1: float,
    output_path: Path,
    logger: AuditLogger
):
    """Write evaluation results to JSON file."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'confusion_matrix': {
            'true_positives': tp,
            'true_negatives': tn,
            'false_positives': fp,
            'false_negatives': fn
        },
        'metrics': {
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        },
        'thresholds': {
            'precision_threshold': PRECISION_THRESHOLD,
            'recall_threshold': RECALL_THRESHOLD,
            'f1_threshold': F1_THRESHOLD
        },
        'passed': {
            'precision': precision >= PRECISION_THRESHOLD,
            'recall': recall >= RECALL_THRESHOLD,
            'f1': f1 >= F1_THRESHOLD
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results written to {output_path}")

def main():
    """Main entry point for evaluation script."""
    # Setup logging
    logger = get_default_logger()
    logger.info("Starting synthetic validation evaluation (T029)")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    synthetic_csv = project_root / "data" / "synthetic" / "synthetic_validation.csv"
    ground_truth_json = project_root / "data" / "synthetic" / "synthetic_ground_truth.json"
    output_json = project_root / "output" / "synthetic_evaluation_results.json"
    
    # Ensure output directory exists
    output_json.parent.mkdir(parents=True, exist_ok=True)
    
    # Check input files exist
    if not synthetic_csv.exists():
        logger.error(f"Synthetic CSV not found: {synthetic_csv}")
        logger.error(get_error_message("ERR-800"))
        sys.exit(1)
    
    if not ground_truth_json.exists():
        logger.error(f"Ground truth JSON not found: {ground_truth_json}")
        logger.error(get_error_message("ERR-800"))
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading synthetic summaries from {synthetic_csv}")
    summaries = load_synthetic_summaries(synthetic_csv)
    logger.info(f"Loaded {len(summaries)} synthetic summaries")
    
    logger.info(f"Loading ground truth from {ground_truth_json}")
    ground_truth = load_ground_truth(ground_truth_json)
    
    # Evaluate
    logger.info("Running inconsistency detection evaluation")
    tp, tn, fp, fn, precision, recall, f1 = evaluate_detection(summaries, ground_truth, logger)
    
    logger.info(f"Confusion Matrix: TP={tp}, TN={tn}, FP={fp}, FN={fn}")
    logger.info(f"Metrics: Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
    
    # Write results
    write_evaluation_results(tp, tn, fp, fn, precision, recall, f1, output_json, logger)
    
    # Check thresholds
    precision_ok = precision >= PRECISION_THRESHOLD
    recall_ok = recall >= RECALL_THRESHOLD
    f1_ok = f1 >= F1_THRESHOLD
    
    if precision_ok and recall_ok and f1_ok:
        logger.info("✓ All evaluation thresholds passed")
        logger.info(f"  Precision: {precision:.4f} >= {PRECISION_THRESHOLD}")
        logger.info(f"  Recall: {recall:.4f} >= {RECALL_THRESHOLD}")
        logger.info(f"  F1: {f1:.4f} >= {F1_THRESHOLD}")
        sys.exit(0)
    else:
        logger.error("✗ Evaluation thresholds NOT met")
        if not precision_ok:
            logger.error(f"  Precision: {precision:.4f} < {PRECISION_THRESHOLD}")
        if not recall_ok:
            logger.error(f"  Recall: {recall:.4f} < {RECALL_THRESHOLD}")
        if not f1_ok:
            logger.error(f"  F1: {f1:.4f} < {F1_THRESHOLD}")
        logger.error(get_error_message(ERR_EVALUATION_FAILED))
        sys.exit(1)

if __name__ == "__main__":
    main()