"""
Statistical aggregation utilities for the feature importance drift analysis pipeline.
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any

from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)


def calculate_stability_metrics(
    r_squared_values: List[float],
    successful_windows: int,
    total_windows: int
) -> Dict[str, Any]:
    """
    Calculate stability metrics from model performance.

    Args:
        r_squared_values: List of R² values from successful windows
        successful_windows: Count of windows with R² >= threshold
        total_windows: Total number of windows processed

    Returns:
        Dictionary with stability metrics
    """
    if not r_squared_values:
        return {
            "mean_r_squared": 0.0,
            "std_r_squared": 0.0,
            "min_r_squared": 0.0,
            "max_r_squared": 0.0,
            "successful_window_count": 0,
            "total_window_count": total_windows,
            "success_rate": 0.0
        }

    mean_r2 = sum(r_squared_values) / len(r_squared_values)
    variance = sum((x - mean_r2) ** 2 for x in r_squared_values) / len(r_squared_values)
    std_r2 = variance ** 0.5

    return {
        "mean_r_squared": mean_r2,
        "std_r_squared": std_r2,
        "min_r_squared": min(r_squared_values),
        "max_r_squared": max(r_squared_values),
        "successful_window_count": successful_windows,
        "total_window_count": total_windows,
        "success_rate": successful_windows / total_windows if total_windows > 0 else 0.0
    }


def aggregate_from_profiles(
    profiles_path: Path
) -> Dict[str, Any]:
    """
    Aggregate stability metrics from importance profile CSV.

    Args:
        profiles_path: Path to importance_profiles.csv

    Returns:
        Aggregated stability metrics dictionary
    """
    config = get_config()
    r_squared_values = []
    successful_windows = 0
    total_windows = 0

    if not profiles_path.exists():
        logger.warning(f"Profiles file not found: {profiles_path}")
        return calculate_stability_metrics([], 0, 0)

    with open(profiles_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_windows += 1
            try:
                r2 = float(row.get('r_squared', 0.0))
                if r2 >= config.min_r_squared:
                    successful_windows += 1
                    r_squared_values.append(r2)
            except (ValueError, TypeError):
                logger.warning(f"Invalid R² value in row: {row}")

    return calculate_stability_metrics(r_squared_values, successful_windows, total_windows)


def save_stability_report(
    metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save stability metrics report to JSON file.

    Args:
        metrics: Stability metrics dictionary
        output_path: Path to save the JSON report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Stability report saved to {output_path}")


def main() -> None:
    """Main entry point for stats_aggregator module (testing)."""
    config = get_config()
    profiles_path = config.output_dir / "importance_profiles.csv"
    metrics = aggregate_from_profiles(profiles_path)
    report_path = config.output_dir / "stability_report.json"
    save_stability_report(metrics, report_path)
    print(f"Stability Report: {json.dumps(metrics, indent=2)}")
