import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed

logger = get_logger(__name__)

# Constants for file paths
FAILURE_CASES_PATH = Path("data/derived/failure_cases.json")
RULES_LIBRARY_PATH = Path("data/derived/rules_library.json")
METRICS_OUTPUT_PATH = Path("data/derived/metrics_summary.json")
COVERAGE_REPORT_PATH = Path("data/derived/coverage_report.json")

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def count_annotations_by_type(failure_cases: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count the number of annotations for each structural feature type.
    Returns a dictionary mapping feature type to count.
    """
    counts: Dict[str, int] = {}
    for case in failure_cases:
        feature = case.get("annotated_structural_feature")
        if feature:
            counts[feature] = counts.get(feature, 0) + 1
    return counts

def count_rules_by_category(rules: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count the number of rules by their inferred category or method.
    If 'method' or 'rule_category' is present, use that; otherwise default to 'Uncategorized'.
    """
    counts: Dict[str, int] = {}
    for rule in rules:
        # Try to find a category key; fallback to 'Uncategorized'
        category = rule.get("rule_category") or rule.get("method") or "Uncategorized"
        counts[category] = counts.get(category, 0) + 1
    return counts

def calculate_rule_coverage_stats(coverage_report_path: Path) -> Dict[str, Any]:
    """
    Load the coverage report and extract key statistics.
    Returns a dictionary with coverage percentage and total cases.
    """
    if not coverage_report_path.exists():
        logger.warning(f"Coverage report not found at {coverage_report_path}. Skipping stats.")
        return {"coverage_percentage": None, "total_cases": None, "covered_cases": None}

    with open(coverage_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    return {
        "coverage_percentage": report.get("coverage_percentage"),
        "total_cases": report.get("total_cases"),
        "covered_cases": report.get("covered_cases"),
        "fallback_triggered": report.get("fallback_triggered", False)
    }

def aggregate_metrics(
    annotation_counts: Dict[str, int],
    rule_counts: Dict[str, int],
    coverage_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all metrics into a single summary structure.
    """
    total_annotations = sum(annotation_counts.values())
    total_rules = sum(rule_counts.values())

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "annotation_summary": {
            "total_count": total_annotations,
            "by_feature": annotation_counts
        },
        "rule_generation_summary": {
            "total_count": total_rules,
            "by_category": rule_counts
        },
        "coverage_summary": coverage_stats
    }

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save the aggregated metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main() -> int:
    """
    Main entry point to log annotation counts and rule generation metrics.
    This function reads the failure cases and rules library, calculates metrics,
    and writes a summary to data/derived/metrics_summary.json.
    """
    log_stage_start(logger, "Metric Aggregation")

    try:
        # Load data
        logger.info(f"Loading failure cases from {FAILURE_CASES_PATH}")
        failure_cases = load_json_file(FAILURE_CASES_PATH)

        logger.info(f"Loading rules library from {RULES_LIBRARY_PATH}")
        rules = load_json_file(RULES_LIBRARY_PATH)

        # Calculate metrics
        annotation_counts = count_annotations_by_type(failure_cases)
        rule_counts = count_rules_by_category(rules)
        coverage_stats = calculate_rule_coverage_stats(COVERAGE_REPORT_PATH)

        # Aggregate
        metrics = aggregate_metrics(annotation_counts, rule_counts, coverage_stats)

        # Save
        save_metrics(metrics, METRICS_OUTPUT_PATH)

        # Log summary to stdout for immediate visibility
        logger.info(f"Total Annotations: {metrics['annotation_summary']['total_count']}")
        logger.info(f"Total Rules Generated: {metrics['rule_generation_summary']['total_count']}")
        if coverage_stats.get("coverage_percentage") is not None:
            logger.info(f"Rule Coverage: {coverage_stats['coverage_percentage']:.2f}%")

        log_stage_end(logger, "Metric Aggregation", success=True)
        return 0

    except Exception as e:
        logger.error(f"Failed to aggregate metrics: {e}")
        log_stage_end(logger, "Metric Aggregation", success=False)
        return 1

if __name__ == "__main__":
    set_seed()
    sys.exit(main())