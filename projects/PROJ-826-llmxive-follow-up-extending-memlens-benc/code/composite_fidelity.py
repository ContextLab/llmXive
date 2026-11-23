"""
Task T035: Calculate composite metric for Fine vs Coarse accuracy and Object Detection Recall.

This module computes:
1. Relative improvement in accuracy: (Fine_Accuracy - Coarse_Accuracy) / Coarse_Accuracy
2. Object Detection Recall (from T011 results)

Logic:
- If Recall >= 0.6: Status = 'VALID', pipeline continues.
- If Recall < 0.6: Status = 'INVALID', pipeline HALTS (raises exception).

Output:
- data/processed/metrics/composite_fidelity.json
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Project root handling (assuming script runs from project root or code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_DIR = PROJECT_ROOT / "data" / "processed" / "metrics"
OUTPUT_FILE = METRICS_DIR / "composite_fidelity.json"
DETECTION_RECALL_FILE = METRICS_DIR / "detection_recall.json"

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_accuracy_metrics() -> Dict[str, float]:
    """
    Load accuracy metrics for Fine and Coarse strategies.
    Expects data from evaluation.py (T020) to be available.
    Since T026 generates the final report, we look for the standard metrics file.
    """
    # The evaluation pipeline typically saves aggregated metrics to a file like 'accuracy_metrics.json'
    # or includes them in the 'final_report.json'. 
    # Based on T020/T026, we assume a file named 'accuracy_metrics.json' exists in metrics_dir
    # or we derive it from the 'final_comparison_report.json' if T026 ran.
    
    # Let's check for the most likely artifact from T026: final_comparison_report.json
    # or a specific accuracy file.
    # If T026 ran, it generated 'data/processed/metrics/final_comparison_report.json'
    
    report_path = METRICS_DIR / "final_comparison_report.json"
    if report_path.exists():
        report = load_json_file(report_path)
        # Extract accuracies from the report structure
        # Assuming structure: {"coarse_accuracy": x, "fine_accuracy": y, ...}
        # If the report is a list of stats, we need to adapt.
        # Let's assume the standard output of T026 contains these keys.
        if "coarse_accuracy" in report and "fine_accuracy" in report:
            return {
                "coarse": report["coarse_accuracy"],
                "fine": report["fine_accuracy"]
            }
    
    # Fallback: try direct accuracy file if T020 saved it separately
    acc_path = METRICS_DIR / "accuracy_metrics.json"
    if acc_path.exists():
        data = load_json_file(acc_path)
        return {
            "coarse": data.get("coarse_accuracy"),
            "fine": data.get("fine_accuracy")
        }
    
    raise FileNotFoundError(
        "Could not find accuracy metrics. Ensure T020 and T026 have run successfully "
        "and generated 'final_comparison_report.json' or 'accuracy_metrics.json'."
    )


def calculate_relative_improvement(coarse_acc: float, fine_acc: float) -> float:
    """
    Calculate relative improvement: (Fine - Coarse) / Coarse.
    Handles division by zero.
    """
    if coarse_acc == 0:
        return float('inf') if fine_acc > 0 else 0.0
    return (fine_acc - coarse_acc) / coarse_acc


def calculate_composite_fidelity() -> Dict[str, Any]:
    """
    Main logic for T035.
    1. Load Object Detection Recall.
    2. Load Accuracy Metrics.
    3. Calculate Relative Improvement.
    4. Determine Status (VALID/INVALID).
    5. Write output.
    """
    # 1. Load Detection Recall (from T011)
    logger.info(f"Loading detection recall from: {DETECTION_RECALL_FILE}")
    detection_data = load_json_file(DETECTION_RECALL_FILE)
    
    # Extract recall value. Structure depends on T011 output.
    # T011 writes to detection_recall.json. Assuming it contains "recall" key.
    if isinstance(detection_data, dict):
        recall = detection_data.get("recall")
        if recall is None:
            # Maybe it's nested?
            recall = detection_data.get("object_detection_recall")
    elif isinstance(detection_data, list) and len(detection_data) > 0:
        # If it's a list of samples, we need the aggregate.
        # Assuming T011 wrote the aggregate in a 'summary' key or the first item is the summary.
        # Let's assume the file contains the aggregate result directly or under a 'summary' key.
        if "summary" in detection_data:
            recall = detection_data["summary"].get("recall")
        else:
            raise ValueError("Unexpected format in detection_recall.json. Expected dict with 'recall' or 'summary'.")
    else:
        raise ValueError("Could not parse detection recall from file.")

    if recall is None:
        raise ValueError("Object Detection Recall value not found in detection_recall.json")

    logger.info(f"Object Detection Recall: {recall:.4f}")

    # 2. Load Accuracy Metrics
    logger.info("Loading accuracy metrics...")
    acc_metrics = load_accuracy_metrics()
    coarse_acc = acc_metrics["coarse"]
    fine_acc = acc_metrics["fine"]
    
    logger.info(f"Coarse Accuracy: {coarse_acc:.4f}, Fine Accuracy: {fine_acc:.4f}")

    # 3. Calculate Relative Improvement
    rel_improvement = calculate_relative_improvement(coarse_acc, fine_acc)
    logger.info(f"Relative Improvement: {rel_improvement:.4f}")

    # 4. Determine Status
    status = "VALID" if recall >= 0.6 else "INVALID"
    
    result = {
        "object_detection_recall": recall,
        "coarse_accuracy": coarse_acc,
        "fine_accuracy": fine_acc,
        "relative_improvement": rel_improvement,
        "status": status,
        "threshold": 0.6,
        "message": "Pipeline HALTED: Recall < 0.6" if status == "INVALID" else "Pipeline OK: Recall >= 0.6"
    }

    # 5. Write Output
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Composite fidelity report written to: {OUTPUT_FILE}")

    # 6. HALT if INVALID
    if status == "INVALID":
        logger.error("CRITICAL: Object Detection Recall is below threshold (0.6). HALTING PIPELINE.")
        raise RuntimeError(f"Pipeline HALTED due to INVALID composite fidelity (Recall={recall:.4f} < 0.6)")

    return result


def main():
    """Entry point for T035."""
    try:
        calculate_composite_fidelity()
        logger.info("T035 completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Pipeline HALTED: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T035 execution: {e}")
        raise


if __name__ == "__main__":
    main()
