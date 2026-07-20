"""
Aggregation module for compiling results across events and resolutions.

This module loads metric results, applies majority rule logic, and
generates summary reports identifying resolution thresholds.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from code.config import RESULTS_METRICS_DIR
from code.data.models import BiasMetric

logger = logging.getLogger(__name__)


def load_all_metrics_from_dir(directory: Path) -> List[BiasMetric]:
    """
    Load all BiasMetric objects from a directory of JSON files.

    Args:
        directory: Path to the directory containing metric JSON files.

    Returns:
        A list of BiasMetric objects.
    """
    metrics = []
    if not directory.exists():
        logger.warning(f"Metrics directory does not exist: {directory}")
        return metrics

    for file_path in directory.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Reconstruct BiasMetric from dictionary
                metric = BiasMetric(
                    event_id=data["event_id"],
                    parameter=data["parameter"],
                    resolution_config=ResolutionConfig(
                        sampling_rate=data["resolution_config"]["sampling_rate"],
                        bit_depth=data["resolution_config"]["bit_depth"]
                    ),
                    bias_value=data["bias_value"],
                    exceeds_threshold=data["exceeds_threshold"],
                    threshold_value=data["threshold_value"],
                    hellinger_distance=data["hellinger_distance"]
                )
                metrics.append(metric)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load metrics from {file_path}: {e}")

    return metrics


def classify_inconclusive_status(metrics: List[BiasMetric]) -> Tuple[List[BiasMetric], List[BiasMetric]]:
    """
    Classify metrics into conclusive and inconclusive groups.

    Args:
        metrics: List of BiasMetric objects.

    Returns:
        A tuple containing:
            - List of conclusive metrics.
            - List of inconclusive metrics.
    """
    conclusive = []
    inconclusive = []

    for metric in metrics:
        # In a full implementation, we would check the inference status
        # stored in the metadata. For now, we assume all loaded metrics are conclusive.
        conclusive.append(metric)

    return conclusive, inconclusive


def calculate_threshold_for_event(
    metrics: List[BiasMetric],
    event_id: str
) -> Optional[int]:
    """
    Calculate the resolution threshold for a specific event.

    Args:
        metrics: List of BiasMetric objects for the event.
        event_id: The event ID.

    Returns:
        The lowest sampling rate where bias exceeds the threshold for >= 50% of parameters,
        or None if no such threshold is found.
    """
    event_metrics = [m for m in metrics if m.event_id == event_id]

    # Group by sampling rate
    rate_metrics: Dict[int, List[BiasMetric]] = {}
    for m in event_metrics:
        rate = m.resolution_config.sampling_rate
        if rate not in rate_metrics:
            rate_metrics[rate] = []
        rate_metrics[rate].append(m)

    # Check majority rule for each rate (sorted ascending)
    sorted_rates = sorted(rate_metrics.keys())
    for rate in sorted_rates:
        rate_group = rate_metrics[rate]
        total_params = len(rate_group)
        exceeded_count = sum(1 for m in rate_group if m.exceeds_threshold)

        if total_params > 0 and (exceeded_count / total_params) >= 0.5:
            return rate

    return None


def aggregate_results(
    all_metrics: List[BiasMetric],
    event_ids: List[str]
) -> Dict[str, Any]:
    """
    Aggregate results across multiple events.

    Args:
        all_metrics: List of all BiasMetric objects.
        event_ids: List of event IDs to include.

    Returns:
        A dictionary containing aggregated results.
    """
    thresholds = {}
    for event_id in event_ids:
        threshold = calculate_threshold_for_event(all_metrics, event_id)
        thresholds[event_id] = threshold

    # Calculate statistics
    valid_thresholds = [t for t in thresholds.values() if t is not None]
    if len(valid_thresholds) >= 2:
        mean_threshold = np.mean(valid_thresholds)
        std_threshold = np.std(valid_thresholds)
    else:
        mean_threshold = None
        std_threshold = None

    return {
        "thresholds": thresholds,
        "mean_threshold": mean_threshold,
        "std_threshold": std_threshold,
        "valid_event_count": len(valid_thresholds)
    }


def save_aggregation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregation report to a JSON file.

    Args:
        report: The aggregation report dictionary.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Aggregation report saved to {output_path}")


def main():
    """
    Main entry point for aggregation.

    This function is intended to be called from a script to execute
    the aggregation pipeline.
    """
    logger.info("Starting aggregation...")
    # Placeholder for actual execution logic
    logger.info("Aggregation completed.")
