"""
Aggregation module for User Story 3: Aggregate Results and Identify Resolution Thresholds.

This module loads metrics from multiple events and resolution configurations,
identifies resolution thresholds where bias exceeds uncertainty, and generates
summary reports.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from code.config import RESULTS_DIR

logger = logging.getLogger(__name__)


def load_all_metrics_from_dir(base_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all metric JSON files from a directory structure.

    Expects a structure like:
        base_dir/
            event_name/
                metrics_config_name.json

    Returns a dictionary mapping event names to lists of metric dictionaries.
    """
    all_metrics: Dict[str, List[Dict[str, Any]]] = {}

    if not base_dir.exists():
        logger.warning(f"Metrics directory not found: {base_dir}")
        return all_metrics

    for event_path in base_dir.iterdir():
        if not event_path.is_dir():
            continue

        event_name = event_path.name
        all_metrics[event_name] = []

        for metric_file in event_path.glob("*.json"):
            try:
                with open(metric_file, "r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
                    # Ensure the file path is attached for reference
                    metrics_data["_source_file"] = str(metric_file)
                    all_metrics[event_name].append(metrics_data)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load metrics from {metric_file}: {e}")

    return all_metrics


def classify_inconclusive_status(metrics: Dict[str, Any]) -> str:
    """
    Classify the status of a metrics entry based on convergence and data quality flags.

    Returns:
        'valid': Normal operation
        'inconclusive_data': Data quality issues (e.g., missing segments, low SNR) - exclude from denominator
        'inconclusive_convergence': Convergence failure (dlogz > 0.1) - count as 'bias exceeded'
    """
    # Check for explicit flags set during inference/metrics calculation
    if metrics.get("status") == "inconclusive_data":
        return "inconclusive_data"

    if metrics.get("status") == "inconclusive_convergence":
        return "inconclusive_convergence"

    # Fallback: check specific fields if status is not explicitly set
    # This handles cases where the flag might be missing but conditions are present
    if metrics.get("convergence_failed", False):
        return "inconclusive_convergence"

    if metrics.get("data_quality_issue", False):
        return "inconclusive_data"

    return "valid"


def calculate_threshold_for_event(
    event_metrics: List[Dict[str, Any]],
    sampling_rates: List[int] = [4096, 2048, 1024, 512, 256]
) -> Optional[int]:
    """
    Identify the lowest sampling rate where the majority rule is met for a single event.

    Logic:
    1. Sort metrics by sampling rate (descending).
    2. Identify the first (lowest) rate where bias > catalog_90_ci.
    3. If no rate exceeds the threshold, return None.

    Args:
        event_metrics: List of metric dictionaries for a single event.
        sampling_rates: List of expected sampling rates to check.

    Returns:
        The lowest sampling rate (int) where bias exceeds uncertainty, or None.
    """
    if not event_metrics:
        return None

    # Sort by sampling rate descending to process high-res first
    sorted_metrics = sorted(
        event_metrics,
        key=lambda x: x.get("sampling_rate", 0),
        reverse=True
    )

    # We need to find the *lowest* rate where bias exceeds.
    # Iterate from lowest to highest to find the first match?
    # No, the threshold is the lowest rate where the condition is met.
    # So we check 256, then 512, etc. The first one that triggers is the threshold.
    # Wait, the task says "lowest sampling rate where bias > catalog 90% CI".
    # If bias > CI at 256Hz, then 256Hz is the threshold.
    # If bias <= CI at 256Hz but > CI at 512Hz, then 512Hz is the threshold.
    # So we should iterate from lowest to highest.

    # Filter out inconclusive_data events for this specific event calculation?
    # Actually, the aggregation logic handles the denominator.
    # Here we just determine the threshold for *this* event instance.
    # If an event is inconclusive_data, it has no threshold.

    # Sort by sampling rate ascending (lowest first)
    sorted_metrics_asc = sorted(
        event_metrics,
        key=lambda x: x.get("sampling_rate", 0)
    )

    for metrics in sorted_metrics_asc:
        status = classify_inconclusive_status(metrics)
        if status == "inconclusive_data":
            # This specific data point is invalid, skip it
            continue

        bias = metrics.get("bias_magnitude", 0.0)
        uncertainty = metrics.get("catalog_90_ci", 0.0)

        # Check if uncertainty is valid
        if uncertainty <= 0:
            continue

        # Check if bias exceeds uncertainty
        if bias > uncertainty:
            return metrics.get("sampling_rate")

    return None


def aggregate_results(
    all_metrics: Dict[str, List[Dict[str, Any]]],
    sampling_rates: List[int] = [4096, 2048, 1028, 512, 256]
) -> Dict[str, Any]:
    """
    Aggregate results across all events to identify resolution thresholds.

    Implements Majority Rule Logic:
    1. Excluded: Events flagged as 'inconclusive_data' are excluded from the denominator.
    2. Counted as Bias Exceeded: Events flagged as 'inconclusive_convergence' are counted as 'bias exceeded'.
    3. Calculated: The threshold is the lowest rate where (Count of 'Bias Exceeded' / Total Valid Events) >= 50%.

    Returns a summary dictionary with counts and identified thresholds per rate.
    """
    if not all_metrics:
        logger.warning("No metrics found to aggregate.")
        return {"summary": [], "thresholds": {}}

    total_events = len(all_metrics)
    rate_stats: Dict[int, Dict[str, int]] = {rate: {"total": 0, "exceeded": 0} for rate in sampling_rates}

    # First pass: determine per-event threshold status
    event_thresholds: Dict[str, Optional[int]] = {}
    event_statuses: Dict[str, Dict[int, str]] = {} # event -> {rate -> status}

    for event_name, metrics_list in all_metrics.items():
        # Determine status for each rate for this event
        event_statuses[event_name] = {}
        for metrics in metrics_list:
            rate = metrics.get("sampling_rate")
            if rate:
                event_statuses[event_name][rate] = classify_inconclusive_status(metrics)

        # Calculate threshold for this event
        threshold = calculate_threshold_for_event(metrics_list, sampling_rates)
        event_thresholds[event_name] = threshold

    # Second pass: Aggregate per rate
    for event_name, threshold in event_thresholds.items():
        for rate in sampling_rates:
            status = event_statuses[event_name].get(rate, "valid")

            if status == "inconclusive_data":
                # Exclude from denominator
                continue

            # Count as valid event for this rate
            rate_stats[rate]["total"] += 1

            # Determine if this rate counts as "exceeded"
            # If the event's threshold is <= current rate, then at this rate bias > CI
            # If the event has no threshold (None), then bias never exceeded
            if threshold is not None and threshold <= rate:
                rate_stats[rate]["exceeded"] += 1

    # Calculate percentages and identify global threshold
    global_threshold = None
    summary = []

    # Sort rates descending to find the "lowest viable" rate (which is the highest rate in the list that meets criteria? No)
    # "Lowest sampling rate where majority rule is met" -> We want the smallest rate number.
    # But we check from lowest to highest?
    # Let's iterate from lowest to highest. The first one that meets >= 50% is the threshold.
    sorted_rates = sorted(sampling_rates)

    for rate in sorted_rates:
        stats = rate_stats[rate]
        total = stats["total"]
        exceeded = stats["exceeded"]

        if total == 0:
            percentage = 0.0
        else:
            percentage = (exceeded / total) * 100

        summary.append({
            "sampling_rate": rate,
            "total_valid_events": total,
            "events_exceeding_bias": exceeded,
            "percentage_exceeding": percentage
        })

        if percentage >= 50.0 and global_threshold is None:
            global_threshold = rate

    result = {
        "total_events_processed": total_events,
        "global_threshold_rate": global_threshold,
        "rate_breakdown": summary
    }

    return result


def save_aggregation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregation report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Aggregation report saved to {output_path}")


def main() -> None:
    """
    Main entry point for the aggregation script.
    Loads metrics from RESULTS_DIR, aggregates them, and saves the report.
    """
    metrics_dir = Path(RESULTS_DIR) / "metrics"
    output_file = Path(RESULTS_DIR) / "aggregation_report.json"

    logger.info(f"Loading metrics from {metrics_dir}")
    all_metrics = load_all_metrics_from_dir(metrics_dir)

    if not all_metrics:
        logger.warning("No metrics found. Skipping aggregation.")
        return

    logger.info(f"Processing {len(all_metrics)} events")
    report = aggregate_results(all_metrics)

    save_aggregation_report(report, output_file)
    logger.info("Aggregation complete.")


if __name__ == "__main__":
    from code.utils.logging_config import setup_logging
    setup_logging()
    main()
