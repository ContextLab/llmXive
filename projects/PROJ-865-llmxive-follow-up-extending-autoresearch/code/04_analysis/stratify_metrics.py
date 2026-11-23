"""
Stratified Metrics Analysis for US2.

This module implements the logic to ensure metrics are recorded separately
for each failure type (Syntactic Error, Logical Loop, Semantic Ambiguity,
Missing Context, Unstructured). It loads the merged results from
data/derived/results.csv and aggregates success rates and time-to-pivot
statistics by failure_type.
"""
import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Import from project utilities
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

RESULTS_CSV_PATH = Path("data/derived/results.csv")
STRATIFIED_REPORT_JSON_PATH = Path("data/derived/stratified_metrics_report.json")

# Expected failure types based on schema T004a
FAILURE_TYPES = [
    "Syntactic Error",
    "Logical Loop",
    "Semantic Ambiguity",
    "Missing Context",
    "Unstructured"
]


def load_results_csv(path: Path) -> List[Dict[str, Any]]:
    """
    Load the merged results CSV.
    Expects columns: task_id, method, time_to_pivot, success, failure_type
    """
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    results = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse numeric fields
            row["time_to_pivot"] = float(row["time_to_pivot"])
            row["success"] = row["success"].lower() == "true"
            results.append(row)
    return results


def calculate_stratified_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate metrics stratified by failure_type.

    Returns a dictionary where keys are failure types and values are dicts
    containing:
      - count: total number of records
      - success_rate: float (0.0 to 1.0)
      - avg_time_to_pivot: float
      - min_time_to_pivot: float
      - max_time_to_pivot: float
    """
    # Initialize buckets for all expected types, even if empty
    buckets: Dict[str, List[Dict[str, Any]]] = {ft: [] for ft in FAILURE_TYPES}

    # Group results by failure_type
    for row in results:
        ft = row.get("failure_type", "Unstructured")
        if ft in buckets:
            buckets[ft].append(row)
        else:
            # Handle unexpected types by grouping into a catch-all or ignoring
            # For strict compliance, we log and ignore or treat as Unstructured
            logger.warning(f"Unexpected failure_type found: {ft}. Treating as Unstructured.")
            buckets["Unstructured"].append(row)

    stratified_data = {}

    for ft, rows in buckets.items():
        if not rows:
            stratified_data[ft] = {
                "count": 0,
                "success_rate": 0.0,
                "avg_time_to_pivot": 0.0,
                "min_time_to_pivot": 0.0,
                "max_time_to_pivot": 0.0,
                "method_breakdown": {}
            }
            continue

        count = len(rows)
        successes = sum(1 for r in rows if r["success"])
        success_rate = successes / count if count > 0 else 0.0

        times = [r["time_to_pivot"] for r in rows]
        avg_time = sum(times) / count
        min_time = min(times)
        max_time = max(times)

        # Breakdown by method (Rule Engine vs Baseline)
        method_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "successes": 0, "total_time": 0.0})
        for r in rows:
            method = r.get("method", "unknown")
            method_stats[method]["count"] += 1
            if r["success"]:
                method_stats[method]["successes"] += 1
            method_stats[method]["total_time"] += r["time_to_pivot"]

        method_breakdown = {}
        for method, stats in method_stats.items():
            method_breakdown[method] = {
                "count": stats["count"],
                "success_rate": stats["successes"] / stats["count"] if stats["count"] > 0 else 0.0,
                "avg_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0.0
            }

        stratified_data[ft] = {
            "count": count,
            "success_rate": round(success_rate, 4),
            "avg_time_to_pivot": round(avg_time, 4),
            "min_time_to_pivot": round(min_time, 4),
            "max_time_to_pivot": round(max_time, 4),
            "method_breakdown": dict(method_breakdown)
        }

    return stratified_data


def save_stratified_report(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save the stratified metrics report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Stratified metrics report saved to {output_path}")


def main() -> int:
    """
    Main entry point for the stratified metrics analysis.
    """
    log_stage_start(logger, "Stratified Metrics Analysis")

    try:
        # Load results
        logger.info(f"Loading results from {RESULTS_CSV_PATH}")
        results = load_results_csv(RESULTS_CSV_PATH)
        logger.info(f"Loaded {len(results)} records")

        # Calculate metrics
        logger.info("Calculating stratified metrics...")
        metrics = calculate_stratified_metrics(results)

        # Save report
        logger.info(f"Saving report to {STRATIFIED_REPORT_JSON_PATH}")
        save_stratified_report(metrics, STRATIFIED_REPORT_JSON_PATH)

        log_stage_end(logger, "Stratified Metrics Analysis", status="success")
        return 0

    except Exception as e:
        logger.error(f"Error during stratified metrics analysis: {e}", exc_info=True)
        log_stage_end(logger, "Stratified Metrics Analysis", status="failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())