"""
T016: Add logging to track annotation counts and rule generation metrics.

This module provides functions to aggregate and log metrics from the annotation
and distillation pipeline stages. It reads the output artifacts from T011
(annotated failures) and T013 (distilled rules) and logs structured summaries
using the project's logging utility.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Import from project API surface
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage

# Output paths for metrics
METRICS_OUTPUT_PATH = Path("data/derived/annotation_rule_metrics.json")


def load_json_file(file_path: Path) -> Optional[Any]:
    """Safely load a JSON file, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger = get_logger(__name__)
        logger.warning(f"Failed to load {file_path}: {e}")
        return None


def count_annotations_by_type(annotated_failures: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count the number of annotated failures for each failure type.

    Args:
        annotated_failures: List of failure dictionaries from annotate_failures.py

    Returns:
        Dictionary mapping failure_type to count
    """
    counts = {
        "Syntactic": 0,
        "Logical": 0,
        "Semantic": 0,
        "Missing Context": 0,
        "Unstructured": 0,
        "Unknown": 0
    }
    for entry in annotated_failures:
      failure_type = entry.get("failure_type", "Unknown")
      if failure_type in counts:
          counts[failure_type] += 1
      else:
          counts["Unknown"] += 1
    return counts


def count_rules_by_category(rules_library: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count the number of distilled rules for each rule category/type.

    Args:
        rules_library: List of rule dictionaries from distill_rules.py

    Returns:
        Dictionary mapping rule category to count
    """
    counts = {}
    for rule in rules_library:
        category = rule.get("category", "Uncategorized")
        counts[category] = counts.get(category, 0) + 1
    return counts


def calculate_rule_coverage_stats(rules_library: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate basic statistics about rule coverage.

    Args:
        rules_library: List of rule dictionaries

    Returns:
        Dictionary with coverage statistics
    """
    total_rules = len(rules_library)
    if total_rules == 0:
        return {
            "total_rules": 0,
            "avg_conditions_per_rule": 0.0,
            "avg_actions_per_rule": 0.0
        }

    total_conditions = sum(len(rule.get("conditions", [])) for rule in rules_library)
    total_actions = sum(len(rule.get("actions", [])) for rule in rules_library)

    return {
        "total_rules": total_rules,
        "avg_conditions_per_rule": round(total_conditions / total_rules, 2),
        "avg_actions_per_rule": round(total_actions / total_rules, 2),
        "max_conditions": max((len(rule.get("conditions", [])) for rule in rules_library), default=0),
        "max_actions": max((len(rule.get("actions", [])) for rule in rules_library), default=0)
    }


def aggregate_metrics(
    annotated_failures_path: Path,
    rules_library_path: Path,
    coverage_report_path: Path
) -> Dict[str, Any]:
    """
    Aggregate all metrics from the annotation and distillation pipeline.

    Args:
        annotated_failures_path: Path to annotated_failures.json
        rules_library_path: Path to rules_library.json
        coverage_report_path: Path to coverage_report.json

    Returns:
        Dictionary containing all aggregated metrics
    """
    logger = get_logger(__name__)

    # Load data
    annotated_failures = load_json_file(annotated_failures_path)
    rules_library = load_json_file(rules_library_path)
    coverage_report = load_json_file(coverage_report_path)

    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "annotation_metrics": {},
        "rule_metrics": {},
        "coverage_metrics": {},
        "summary": {}
    }

    # Annotation metrics
    if annotated_failures:
        annotation_counts = count_annotations_by_type(annotated_failures)
        metrics["annotation_metrics"] = {
            "total_annotations": len(annotated_failures),
            "by_failure_type": annotation_counts
        }
        logger.info(f"Annotation counts: {annotation_counts}")
    else:
        logger.warning("No annotated failures found at " + str(annotated_failures_path))

    # Rule metrics
    if rules_library:
        rule_counts = count_rules_by_category(rules_library)
        coverage_stats = calculate_rule_coverage_stats(rules_library)
        metrics["rule_metrics"] = {
            "total_rules": len(rules_library),
            "by_category": rule_counts,
            "coverage_statistics": coverage_stats
        }
        logger.info(f"Rule counts: {rule_counts}")
        logger.info(f"Rule coverage stats: {coverage_stats}")
    else:
        logger.warning("No rules library found at " + str(rules_library_path))

    # Coverage metrics
    if coverage_report:
        metrics["coverage_metrics"] = {
            "validation_coverage": coverage_report.get("coverage", 0.0),
            "validation_size": coverage_report.get("validation_size", 0),
            "matched_cases": coverage_report.get("matched_cases", 0),
            "unmatched_cases": coverage_report.get("unmatched_cases", 0)
        }
        logger.info(f"Coverage: {metrics['coverage_metrics']['validation_coverage']}")
    else:
        logger.warning("No coverage report found at " + str(coverage_report_path))

    # Summary
    metrics["summary"] = {
        "total_failures_processed": metrics["annotation_metrics"].get("total_annotations", 0),
        "total_rules_generated": metrics["rule_metrics"].get("total_rules", 0),
        "coverage_achieved": metrics["coverage_metrics"].get("validation_coverage", 0.0),
        "pipeline_status": "success" if (
            metrics["annotation_metrics"].get("total_annotations", 0) > 0 and
            metrics["rule_metrics"].get("total_rules", 0) > 0
        ) else "incomplete"
    }

    return metrics


def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def main() -> int:
    """
    Main entry point for T016.
    Reads pipeline outputs and logs metrics.
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "T016 - Log Annotation and Rule Metrics")

    # Define input paths (relative to project root)
    project_root = Path.cwd()
    annotated_failures_path = project_root / "data" / "derived" / "annotated_failures.json"
    rules_library_path = project_root / "data" / "derived" / "rules_library.json"
    coverage_report_path = project_root / "data" / "derived" / "coverage_report.json"

    # Aggregate metrics
    metrics = aggregate_metrics(
        annotated_failures_path,
        rules_library_path,
        coverage_report_path
    )

    # Save metrics to file
    save_metrics(metrics, METRICS_OUTPUT_PATH)
    logger.info(f"Metrics saved to {METRICS_OUTPUT_PATH}")

    # Log summary to console via logger
    logger.info(f"Pipeline Summary: {metrics['summary']}")

    log_stage_end(logger, "T016 - Log Annotation and Rule Metrics", status="completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())