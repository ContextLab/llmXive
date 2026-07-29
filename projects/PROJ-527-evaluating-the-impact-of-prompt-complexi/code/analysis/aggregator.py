"""
Aggregation logic for execution results.

Calculates pass rates per complexity level from execution outcomes.
"""

import os
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

import pandas as pd

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_pass_rates(
    execution_results_path: Optional[Path] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate pass rates per complexity level from execution results.

    Args:
        execution_results_path: Path to execution_outcomes.csv. If None, uses
            the default path from config.

    Returns:
        Dictionary mapping complexity labels to their statistics:
        {
            'simple': {
                'total': int,
                'passed': int,
                'failed': int,
                'pass_rate': float
            },
            ...
        }
    """
    if execution_results_path is None:
        execution_results_path = Paths.DATA_RESULTS / "execution_outcomes.csv"

    if not execution_results_path.exists():
        raise FileNotFoundError(
            f"Execution results file not found at {execution_results_path}. "
            "Run the execution pipeline first (T030)."
        )

    df = pd.read_csv(execution_results_path)

    # Ensure required columns exist
    required_cols = ['complexity_label', 'execution_status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {execution_results_path}: {missing_cols}"
        )

    # Group by complexity level
    results = {}
    complexity_labels = df['complexity_label'].unique()

    for label in complexity_labels:
        subset = df[df['complexity_label'] == label]
        total = len(subset)
        passed = subset[subset['execution_status'] == 'pass'].shape[0]
        failed = total - passed
        pass_rate = passed / total if total > 0 else 0.0

        results[label] = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate
        }
        logger.info(
            f"Complexity '{label}': {passed}/{total} passed ({pass_rate:.2%})"
        )

    return results


def write_aggregation_to_csv(
    pass_rates: Dict[str, Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write aggregated pass rates to a CSV file.

    Args:
        pass_rates: Dictionary of pass rate statistics per complexity level.
        output_path: Path to output CSV. If None, uses default results path.

    Returns:
        Path to the written CSV file.
    """
    if output_path is None:
        output_path = Paths.DATA_RESULTS / "aggregation_results.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for label, stats in pass_rates.items():
        rows.append({
            'complexity_level': label,
            'total_samples': stats['total'],
            'passed_count': stats['passed'],
            'failed_count': stats['failed'],
            'pass_rate': stats['pass_rate']
        })

    # Sort by a logical order if possible, otherwise alphabetically
    priority_order = ['simple', 'moderate', 'complex', 'very_complex', 'degenerate']
    def sort_key(row):
        try:
            return priority_order.index(row['complexity_level'])
        except ValueError:
            return 999

    rows.sort(key=sort_key)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'complexity_level', 'total_samples', 'passed_count',
            'failed_count', 'pass_rate'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Aggregation results written to {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point for aggregation task.
    Reads execution_outcomes.csv, calculates pass rates, and writes results.
    """
    logger.info("Starting aggregation of execution results...")

    try:
        # Calculate pass rates
        pass_rates = calculate_pass_rates()

        if not pass_rates:
            logger.warning("No execution results found to aggregate.")
            return

        # Write to CSV
        output_file = write_aggregation_to_csv(pass_rates)

        logger.info("Aggregation completed successfully.")
        logger.info(f"Output file: {output_file}")

        # Print summary to stdout for quick verification
        print("\n--- Aggregation Summary ---")
        for label, stats in pass_rates.items():
            print(
                f"{label:15} | "
                f"Total: {stats['total']:3} | "
                f"Passed: {stats['passed']:3} | "
                f"Rate: {stats['pass_rate']:.2%}"
            )
        print("---------------------------")

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()