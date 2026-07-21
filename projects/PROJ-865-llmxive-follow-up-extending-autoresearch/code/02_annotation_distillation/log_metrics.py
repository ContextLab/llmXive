"""
Metrics Logging Module for AutoResearchClaw Pipeline.

This module implements T016: Add logging to track annotation counts and rule generation metrics.
It aggregates statistics from failure case annotations and distilled rules, calculating coverage
and saving a comprehensive metrics report.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collections import defaultdict

# Import from project utils
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import set_seed

# Constants
ANNOTATED_FAILURES_PATH = Path("data/derived/failure_cases.json")
RULES_LIBRARY_PATH = Path("data/derived/rules_library.json")
COVERAGE_REPORT_PATH = Path("data/derived/coverage_report.json")
METRICS_OUTPUT_PATH = Path("data/derived/annotation_distillation_metrics.json")
VALIDATION_SPLIT_SIZE = 0.2  # 20% for validation if splitting needed, though we use full set for stats

logger = get_logger(__name__)


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Required file missing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.warning(f"Expected list in {file_path}, got {type(data)}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        raise


def count_annotations_by_type(annotations: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count the number of failure cases for each annotated structural feature type.

    Args:
        annotations: List of failure case dictionaries.

    Returns:
        Dictionary mapping feature type to count.
    """
    counts = defaultdict(int)
    total = len(annotations)

    for item in annotations:
        feature = item.get("annotated_structural_feature", "Unknown")
        counts[feature] += 1

    # Ensure all expected categories are present even if zero
    expected_categories = [
        "Syntactic Error",
        "Logical Loop",
        "Semantic Ambiguity",
        "Missing Context",
        "Unstructured"
    ]
    for cat in expected_categories:
        if cat not in counts:
            counts[cat] = 0

    logger.info(f"Annotation counts calculated: {dict(counts)} (Total: {total})")
    return dict(counts)


def count_rules_by_category(rules: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count rules by their category or type if available.
    If no explicit category exists, groups by rule complexity or source.

    Args:
        rules: List of rule dictionaries.

    Returns:
        Dictionary mapping category to count.
    """
    counts = defaultdict(int)
    total = len(rules)

    for rule in rules:
        # Try to find a category field, fallback to 'type' or 'source'
        category = rule.get("category") or rule.get("type") or rule.get("source") or "Uncategorized"
        counts[category] += 1

    logger.info(f"Rule counts by category: {dict(counts)} (Total: {total})")
    return dict(counts)


def calculate_rule_coverage_stats(coverage_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from coverage report data.

    Args:
        coverage_data: Dictionary from coverage_report.json.

    Returns:
        Dictionary with coverage statistics.
    """
    if not coverage_data:
        logger.warning("No coverage data provided for statistics calculation.")
        return {
            "total_coverage_pct": 0.0,
            "covered_count": 0,
            "uncovered_count": 0,
            "total_cases": 0
        }

    total = coverage_data.get("total_cases", 0)
    covered = coverage_data.get("covered_count", 0)
    pct = coverage_data.get("coverage_percentage", 0.0)

    logger.info(f"Coverage stats: {pct}% ({covered}/{total})")
    return {
        "total_coverage_pct": pct,
        "covered_count": covered,
        "uncovered_count": total - covered,
        "total_cases": total
    }


def aggregate_metrics(
    annotations: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    coverage_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate all metrics into a single report structure.

    Args:
        annotations: List of annotated failure cases.
        rules: List of distilled rules.
        coverage_data: Optional coverage report data.

    Returns:
        Comprehensive metrics dictionary.
    """
    annotation_counts = count_annotations_by_type(annotations)
    rule_counts = count_rules_by_category(rules)
    coverage_stats = calculate_rule_coverage_stats(coverage_data)

    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_stage": "annotation_distillation",
        "annotation_metrics": {
            "total_annotations": len(annotations),
            "distribution": annotation_counts
        },
        "rule_metrics": {
            "total_rules": len(rules),
            "distribution": rule_counts
        },
        "coverage_metrics": coverage_stats,
        "summary": {
            "annotation_coverage": len(annotations) > 0,
            "rule_generation_complete": len(rules) > 0,
            "overall_status": "success" if (len(annotations) > 0 and len(rules) > 0) else "partial"
        }
    }

    logger.info("Metrics aggregation complete.")
    return metrics


def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregated metrics to a JSON file.

    Args:
        metrics: The metrics dictionary to save.
        output_path: Path to the output file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, default=str)
        logger.info(f"Metrics saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write metrics file: {e}")
        raise


def main() -> int:
    """
    Main entry point for T016: Log metrics for annotation and rule generation.

    This function:
    1. Loads annotated failure cases from data/derived/failure_cases.json
    2. Loads distilled rules from data/derived/rules_library.json
    3. Loads coverage report from data/derived/coverage_report.json (if exists)
    4. Aggregates counts and statistics
    5. Saves the final metrics report to data/derived/annotation_distillation_metrics.json

    Returns:
        0 on success, 1 on failure.
    """
    log_stage_start(logger, "T016: Log Annotation and Rule Metrics")

    try:
        # Set seed for reproducibility
        set_seed(42)

        # Load data
        logger.info(f"Loading annotated failures from {ANNOTATED_FAILURES_PATH}")
        annotations = load_json_file(ANNOTATED_FAILURES_PATH)

        logger.info(f"Loading rules library from {RULES_LIBRARY_PATH}")
        rules = load_json_file(RULES_LIBRARY_PATH)

        # Load coverage report if it exists
        coverage_data = None
        if COVERAGE_REPORT_PATH.exists():
            logger.info(f"Loading coverage report from {COVERAGE_REPORT_PATH}")
            coverage_data = load_json_file(COVERAGE_REPORT_PATH)
            # Ensure it's a dict, not a list (coverage report might be a single object)
            if isinstance(coverage_data, list) and len(coverage_data) == 1:
                coverage_data = coverage_data[0]
        else:
            logger.warning(f"Coverage report not found at {COVERAGE_REPORT_PATH}. Skipping coverage stats.")

        # Aggregate metrics
        metrics = aggregate_metrics(annotations, rules, coverage_data)

        # Save metrics
        save_metrics(metrics, METRICS_OUTPUT_PATH)

        log_stage_end(logger, "T016: Log Annotation and Rule Metrics", status="success")
        return 0

    except Exception as e:
        logger.error(f"Task T016 failed: {e}", exc_info=True)
        log_stage_end(logger, "T016: Log Annotation and Rule Metrics", status="failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())