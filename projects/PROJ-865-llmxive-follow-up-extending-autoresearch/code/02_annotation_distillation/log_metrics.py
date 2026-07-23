import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import set_seed

# Ensure logger is configured
logger = get_logger("log_metrics")

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {file_path}, got {type(data)}")
    return data

def count_annotations_by_type(annotations: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count annotations by their 'annotated_structural_feature' field.
    """
    counts: Dict[str, int] = {}
    for entry in annotations:
        feature = entry.get("annotated_structural_feature", "Unknown")
        counts[feature] = counts.get(feature, 0) + 1
    return counts

def count_rules_by_category(rules: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count rules by a categorical field if present, or total count.
    For this task, we assume rules have a 'rule_id' and potentially a 'category' or similar.
    If no specific category exists, we just count total rules.
    """
    total_rules = len(rules)
    # Attempt to group by a 'category' field if it exists in the rule structure
    category_counts: Dict[str, int] = {}
    for rule in rules:
        # Check for a 'category' or 'type' field; if not present, use 'Unspecified'
        cat = rule.get("category", rule.get("type", "Unspecified"))
        category_counts[cat] = category_counts.get(cat, 0) + 1
    return {
        "total_rules": total_rules,
        "by_category": category_counts
    }

def calculate_rule_coverage_stats(coverage_report: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract key coverage statistics from a coverage report.
    Expected keys in coverage_report: 'coverage_percentage', 'total_cases', 'covered_cases'.
    """
    return {
        "coverage_percentage": coverage_report.get("coverage_percentage", 0.0),
        "total_cases": coverage_report.get("total_cases", 0),
        "covered_cases": coverage_report.get("covered_cases", 0),
        "uncovered_cases": coverage_report.get("uncovered_cases", 0)
    }

def aggregate_metrics(
    failure_cases_path: Path,
    rules_library_path: Path,
    coverage_report_path: Path,
    output_metrics_path: Path
) -> Dict[str, Any]:
    """
    Aggregate all metrics: annotation counts, rule counts, coverage stats.
    Logs the aggregated metrics and saves them to a JSON file.
    """
    # Load data
    logger.info(f"Loading failure cases from {failure_cases_path}")
    failure_cases = load_json_file(failure_cases_path)

    logger.info(f"Loading rules library from {rules_library_path}")
    rules = load_json_file(rules_library_path)

    logger.info(f"Loading coverage report from {coverage_report_path}")
    with open(coverage_report_path, 'r', encoding='utf-8') as f:
        coverage_report = json.load(f)

    # Compute metrics
    annotation_counts = count_annotations_by_type(failure_cases)
    rule_counts = count_rules_by_category(rules)
    coverage_stats = calculate_rule_coverage_stats(coverage_report)

    # Aggregate into a single metrics dictionary
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "annotation_counts": annotation_counts,
        "rule_counts": rule_counts,
        "coverage_stats": coverage_stats,
        "total_annotations": len(failure_cases),
        "total_rules": len(rules)
    }

    # Log the metrics
    log_stage_start(logger, "Aggregated Metrics")
    logger.info(f"Total Annotations: {metrics['total_annotations']}")
    logger.info(f"Annotation Breakdown: {json.dumps(annotation_counts)}")
    logger.info(f"Total Rules: {metrics['total_rules']}")
    logger.info(f"Rule Counts by Category: {json.dumps(rule_counts.get('by_category', {}))}")
    logger.info(f"Coverage Stats: {json.dumps(coverage_stats)}")
    log_stage_end(logger, "Aggregated Metrics")

    # Save metrics to file
    output_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {output_metrics_path}")
    return metrics

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save metrics dictionary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main entry point for logging annotation counts and rule generation metrics.
    Reads from standard paths and writes metrics to data/derived/metrics.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_derived_dir = project_root / "data" / "derived"

    failure_cases_path = data_derived_dir / "failure_cases.json"
    rules_library_path = data_derived_dir / "rules_library.json"
    coverage_report_path = data_derived_dir / "coverage_report.json"
    output_metrics_path = data_derived_dir / "metrics.json"

    # Validate input files exist
    for path in [failure_cases_path, rules_library_path, coverage_report_path]:
        if not path.exists():
            logger.error(f"Required input file missing: {path}")
            sys.exit(1)

    # Run aggregation
    try:
        metrics = aggregate_metrics(
            failure_cases_path,
            rules_library_path,
            coverage_report_path,
            output_metrics_path
        )
        logger.info("Metric aggregation completed successfully.")
    except Exception as e:
        logger.error(f"Error during metric aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()