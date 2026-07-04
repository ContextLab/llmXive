"""
Evaluation module for inconsistency-detection component on synthetic validation dataset.

Implements FR-031: Evaluate the inconsistency detection component on the synthetic
validation dataset, computing precision, recall, and F1 score, and asserting that
precision >= 90% and recall >= 80%.
"""
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Paths relative to project root
SYNTHETIC_SUMMARIES_PATH = Path("data/synthetic/synthetic_validation.csv")
GROUND_TRUTH_PATH = Path("data/synthetic/synthetic_ground_truth.json")
AUDIT_REPORT_PATH = Path("output/audit_report.json")
EVALUATION_OUTPUT_PATH = Path("output/evaluation_results.json")

PRECISION_THRESHOLD = 0.90
RECALL_THRESHOLD = 0.80

logger = get_default_logger(__name__)


def load_synthetic_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load synthetic summaries from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Synthetic summaries file not found: {path}")
    
    summaries = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            summaries.append(row)
    return summaries


def load_ground_truth(path: Path) -> Dict[str, Any]:
    """Load ground truth labels from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_audit_records(path: Path) -> List[Dict[str, Any]]:
    """Load audit records from the audit report JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Audit report file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Handle both list and dict with 'records' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "records" in data:
            return data["records"]
        else:
            return []


def evaluate_detection(
    ground_truth: Dict[str, Any],
    audit_records: List[Dict[str, Any]]
) -> Tuple[int, int, int, int]:
    """
    Evaluate inconsistency detection by comparing predictions against ground truth.
    
    Returns: (true_positives, false_positives, false_negatives, true_negatives)
    """
    # Build ground truth lookup by URL or ID
    # Ground truth structure: { "summaries": [ { "url": ..., "is_inconsistent": ... }, ... ] }
    gt_lookup = {}
    for entry in ground_truth.get("summaries", []):
        key = entry.get("url") or entry.get("id")
        if key:
            gt_lookup[key] = entry.get("is_inconsistent", False)
    
    # Build predictions lookup
    pred_lookup = {}
    for record in audit_records:
        key = record.get("url") or record.get("id")
        if key:
            # Determine if flagged as inconsistent
            is_flagged = record.get("is_inconsistent", False) or record.get("flagged", False)
            pred_lookup[key] = is_flagged
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0
    
    # Evaluate on common keys
    for key in gt_lookup:
        actual = gt_lookup[key]
        predicted = pred_lookup.get(key, False)
        
        if actual and predicted:
            true_positives += 1
        elif not actual and predicted:
            false_positives += 1
        elif actual and not predicted:
            false_negatives += 1
        else:
            true_negatives += 1
    
    return true_positives, false_positives, false_negatives, true_negatives


def validate_summary(
    tp: int,
    fp: int,
    fn: int,
    tn: int
) -> Tuple[float, float, float, bool]:
    """
    Calculate precision, recall, F1, and check if thresholds are met.
    
    Returns: (precision, recall, f1, thresholds_met)
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    thresholds_met = (precision >= PRECISION_THRESHOLD) and (recall >= RECALL_THRESHOLD)
    
    return precision, recall, f1, thresholds_met


def write_evaluation_results(
    path: Path,
    metrics: Dict[str, Any],
    thresholds_met: bool
) -> None:
    """Write evaluation results to JSON file."""
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "thresholds_met": thresholds_met,
        "precision_threshold": PRECISION_THRESHOLD,
        "recall_threshold": RECALL_THRESHOLD
    }
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Evaluation results written to {path}")


def main() -> int:
    """
    Main entry point for T029: Evaluate inconsistency-detection component.
    
    Returns: 0 on success, 1 if thresholds not met (ERR-800)
    """
    logger.info("Starting T029: Evaluate inconsistency-detection component on synthetic dataset")
    
    try:
        # Load data
        logger.info(f"Loading synthetic summaries from {SYNTHETIC_SUMMARIES_PATH}")
        summaries = load_synthetic_summaries(SYNTHETIC_SUMMARIES_PATH)
        logger.info(f"Loaded {len(summaries)} synthetic summaries")
        
        logger.info(f"Loading ground truth from {GROUND_TRUTH_PATH}")
        ground_truth = load_ground_truth(GROUND_TRUTH_PATH)
        logger.info(f"Loaded ground truth with {len(ground_truth.get('summaries', []))} entries")
        
        logger.info(f"Loading audit report from {AUDIT_REPORT_PATH}")
        audit_records = load_audit_records(AUDIT_REPORT_PATH)
        logger.info(f"Loaded {len(audit_records)} audit records")
        
        # Evaluate detection
        tp, fp, fn, tn = evaluate_detection(ground_truth, audit_records)
        logger.info(f"TP={tp}, FP={fp}, FN={fn}, TN={tn}")
        
        # Calculate metrics
        precision, recall, f1, thresholds_met = validate_summary(tp, fp, fn, tn)
        logger.info(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
        
        # Write results
        write_evaluation_results(
            EVALUATION_OUTPUT_PATH,
            {
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            },
            thresholds_met
        )
        
        if thresholds_met:
            logger.info(f"SUCCESS: Precision ({precision:.2%}) >= {PRECISION_THRESHOLD:.0%} and Recall ({recall:.2%}) >= {RECALL_THRESHOLD:.0%}")
            return 0
        else:
            error_msg = get_error_message("ERR-800")
            logger.error(f"ERR-800: Thresholds not met. Precision={precision:.2%} (need >= {PRECISION_THRESHOLD:.0%}), Recall={recall:.2%} (need >= {RECALL_THRESHOLD:.0%})")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"ERR-800: Required data file not found - {e}")
        return 1
    except Exception as e:
        logger.error(f"ERR-800: Evaluation failed with exception - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
