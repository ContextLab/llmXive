"""
API Log Aggregation Utility

Implements SC-004: Calculate and report the success/failure ratio of API calls.
This module aggregates metrics from the logging infrastructure and provides
reporting capabilities.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.logging_config import (
    get_api_logger,
    get_aggregated_metrics,
    calculate_success_ratio,
    log_api_call
)

logger = get_api_logger("api_metrics")

def aggregate_and_report(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregates current API metrics, calculates success/failure ratios,
    and optionally writes the report to a file.

    Args:
        output_path: Optional path to write the JSON report (e.g., data/processed/api_metrics.json)

    Returns:
        Dictionary containing the aggregated metrics and calculated ratios.
    """
    raw_metrics = get_aggregated_metrics()
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_calls": 0,
        "total_success": 0,
        "total_failure": 0,
        "endpoints": {}
    }

    overall_success = 0
    overall_failure = 0

    for key, stats in raw_metrics.items():
        success_count = stats["success"]
        failure_count = stats["failure"]
        total_count = success_count + failure_count

        overall_success += success_count
        overall_failure += failure_count
        report["total_calls"] += total_count

        ratio = calculate_success_ratio("", "") # Placeholder, will recalculate per key
        # Recalculate specific ratio
        if total_count > 0:
            ratio = success_count / total_count
        else:
            ratio = 0.0

        report["endpoints"][key] = {
            "success_count": success_count,
            "failure_count": failure_count,
            "total_count": total_count,
            "success_ratio": round(ratio, 4)
        }

    report["total_success"] = overall_success
    report["total_failure"] = overall_failure

    if report["total_calls"] > 0:
        report["overall_success_ratio"] = round(overall_success / report["total_calls"], 4)
    else:
        report["overall_success_ratio"] = 0.0

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"API metrics report written to {output_path}")

    return report

def check_thresholds(threshold: float = 0.95) -> bool:
    """
    Checks if the overall success ratio meets a specific threshold.
    SC-004 requirement: Monitor success/failure ratio.

    Args:
        threshold: Minimum acceptable success ratio (default 0.95).

    Returns:
        True if the ratio meets or exceeds the threshold, False otherwise.
    """
    report = aggregate_and_report()
    ratio = report.get("overall_success_ratio", 0.0)
    if ratio < threshold:
        logger.warning(f"API Success Ratio {ratio:.2f} is below threshold {threshold}")
        return False
    logger.info(f"API Success Ratio {ratio:.2f} meets threshold {threshold}")
    return True

def main():
    """
    Entry point for running the metrics aggregation as a standalone script.
    Useful for CI/CD checks or manual verification of SC-004.
    """
    logger.info("Running API Metrics Aggregation...")
    report = aggregate_and_report(output_path="data/processed/api_metrics.json")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    main()
