"""
Module to save network metrics including FD as a covariate.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.config import Config

logger = logging.getLogger(__name__)


def save_metrics_to_csv(
    metrics: List[Dict[str, Any]],
    output_path: Path,
    config: Config
) -> None:
    """
    Save network metrics to a CSV file.
    
    Includes FD as a mandatory covariate column for subjects who passed
    the motion threshold.

    Args:
        metrics: List of dictionaries containing metrics for each subject
        output_path: Path to output CSV file
        config: Configuration object
    """
    if not metrics:
        logger.warning("No metrics to save")
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define CSV columns
    # Include FD as a mandatory covariate column
    fieldnames = [
        'subject_id',
        'scan_type',
        'modularity_q',
        'global_efficiency',
        'local_efficiency',
        'mean_fd',  # Mandatory covariate per T015
        'mean_translation',
        'mean_rotation',
        'passed_motion_check'
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for metric in metrics:
            row = {
                'subject_id': metric.get('subject_id', ''),
                'scan_type': metric.get('scan_type', ''),
                'modularity_q': metric.get('modularity_q', ''),
                'global_efficiency': metric.get('global_efficiency', ''),
                'local_efficiency': metric.get('local_efficiency', ''),
                'mean_fd': metric.get('mean_fd', ''),  # FD saved for passed subjects
                'mean_translation': metric.get('mean_translation', ''),
                'mean_rotation': metric.get('mean_rotation', ''),
                'passed_motion_check': metric.get('passed_motion_check', True)
            }
            writer.writerow(row)

    logger.info(f"Saved metrics to {output_path}")


def run_save_metrics(
    metrics: List[Dict[str, Any]],
    output_dir: Path,
    config: Config
) -> Path:
    """
    Run the save metrics process.

    Args:
        metrics: List of metric dictionaries
        output_dir: Output directory
        config: Configuration object

    Returns:
        Path to the saved CSV file
    """
    output_path = output_dir / 'network_metrics.csv'
    save_metrics_to_csv(metrics, output_path, config)
    return output_path


def main():
    """Main entry point."""
    print("Save metrics module loaded")


if __name__ == "__main__":
    main()
