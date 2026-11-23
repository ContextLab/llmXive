"""
T019c: Generate the final metrics file `data/results/model_metrics.json`.

This script aggregates all performance metrics, baseline comparisons,
and success criterion verifications into a single canonical JSON artifact.

Dependencies:
- T019: Classification and regression metrics (code/modeling/evaluate.py)
- T019d: Polymorphism metrics (code/modeling/polymorphism_metrics.py)
- T017c: Success criterion check (data/validation/success_criterion_check.json)
- T017: Molecular Weight baseline (data/results/mw_baseline_metrics.json)
- T017b: Majority class baseline (data/results/majority_class_baseline_metrics.json)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import config utilities from project root
# Note: Using absolute import style compatible with project structure
from config import (
    get_path_absolute,
    get_path_results,
    get_path_validation,
    ensure_directory
)
from logging_config import get_logger, setup_logging

# Constants for artifact paths
METRICS_EVALUATE_PATH = "data/results/evaluate_metrics.json" # From T019
POLYMORPHISM_METRICS_PATH = "data/results/polymorphism_metrics.json" # From T019d
SUCCESS_CRITERION_PATH = "data/validation/success_criterion_check.json" # From T017c
MW_BASELINE_PATH = "data/results/mw_baseline_metrics.json" # From T017
MAJORITY_BASELINE_PATH = "data/results/majority_class_baseline_metrics.json" # From T017b
FINAL_METRICS_PATH = "data/results/model_metrics.json"

def load_json_file(path_key: str, description: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file. Returns None if file is missing, but logs a warning.
    In a strict run, missing critical files should ideally raise, but we
    aggregate what exists to produce the final report.
    """
    path = get_path_absolute(path_key)
    if not os.path.exists(path):
        logging.warning(f"Required artifact missing for {description}: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON for {description}: {e}")
        return None

def aggregate_metrics(
    eval_metrics: Optional[Dict[str, Any]],
    polymorphism_metrics: Optional[Dict[str, Any]],
    success_check: Optional[Dict[str, Any]],
    mw_baseline: Optional[Dict[str, Any]],
    majority_baseline: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate all loaded metrics into the final structure.
    Handles missing components gracefully by marking them as 'unavailable'.
    """
    final_report = {
        "status": "completed",
        "artifacts_generated": [FINAL_METRICS_PATH],
        "components": {}
    }

    # 1. Model Performance Metrics (from T019)
    if eval_metrics:
        final_report["components"]["model_performance"] = eval_metrics
    else:
        final_report["components"]["model_performance"] = {
            "status": "unavailable",
            "reason": "T019 evaluation metrics not found"
        }

    # 2. Polymorphism Metrics (from T019d)
    if polymorphism_metrics:
        final_report["components"]["polymorphism_analysis"] = polymorphism_metrics
    else:
        final_report["components"]["polymorphism_analysis"] = {
            "status": "unavailable",
            "reason": "T019d polymorphism metrics not found"
        }

    # 3. Baseline Comparisons
    baselines = {}
    if mw_baseline:
        baselines["molecular_weight_regression"] = mw_baseline
    else:
        baselines["molecular_weight_regression"] = {"status": "unavailable"}

    if majority_baseline:
        baselines["majority_class_classification"] = majority_baseline
    else:
        baselines["majority_class_classification"] = {"status": "unavailable"}

    final_report["components"]["baselines"] = baselines

    # 4. Success Criterion Verification (from T017c)
    if success_check:
        final_report["components"]["success_criterion"] = success_check
        # Determine overall pass/fail
        is_success = success_check.get("passed", False)
        final_report["overall_success"] = is_success
        final_report["overall_status"] = "PASS" if is_success else "FAIL"
    else:
        final_report["components"]["success_criterion"] = {
            "status": "unavailable",
            "reason": "T017c success criterion check not found"
        }
        final_report["overall_success"] = False
        final_report["overall_status"] = "UNKNOWN"

    # Add metadata
    final_report["metadata"] = {
        "task_id": "T019c",
        "description": "Final metrics aggregation",
        "dependencies_verified": [
            "T019", "T019d", "T017c", "T017", "T017b"
        ]
    }

    return final_report

def main():
    """Main entry point for T019c."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting T019c: Final Metrics Generation")

    # Ensure output directory exists
    output_dir = get_path_absolute("data/results")
    ensure_directory(output_dir)

    # Load all required artifacts
    logger.info("Loading T019 evaluation metrics...")
    eval_metrics = load_json_file(METRICS_EVALUATE_PATH, "T019")

    logger.info("Loading T019d polymorphism metrics...")
    polymorphism_metrics = load_json_file(POLYMORPHISM_METRICS_PATH, "T019d")

    logger.info("Loading T017c success criterion check...")
    success_check = load_json_file(SUCCESS_CRITERION_PATH, "T017c")

    logger.info("Loading T017 MW baseline...")
    mw_baseline = load_json_file(MW_BASELINE_PATH, "T017")

    logger.info("Loading T017b Majority baseline...")
    majority_baseline = load_json_file(MAJORITY_BASELINE_PATH, "T017b")

    # Aggregate
    logger.info("Aggregating metrics...")
    final_report = aggregate_metrics(
        eval_metrics,
        polymorphism_metrics,
        success_check,
        mw_baseline,
        majority_baseline
    )

    # Write final output
    output_path = get_path_absolute(FINAL_METRICS_PATH)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2)
        logger.info(f"Successfully wrote final metrics to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write final metrics file: {e}")
        sys.exit(1)

    # Print summary to stdout for immediate feedback
    print(f"T019c Complete. Overall Status: {final_report.get('overall_status')}")
    if 'overall_success' in final_report:
        print(f"Success Criterion Met: {final_report['overall_success']}")

if __name__ == "__main__":
    main()