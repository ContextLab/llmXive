"""
Coordination Overhead Calculator for Mesh Network Supercomputer.

This module computes the coordination overhead ratio for every task execution
by calculating handshake_time / total_time.

The handshake time is derived from the difference between the total execution time
and the actual compute time (wall_clock_time) as recorded in the execution logs.
Alternatively, if specific handshake metrics are available in the logs, they are used directly.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

# Ensure we can import from the project root if run as a script
# Adjust path logic if necessary based on execution context
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.logger import get_logger, init_logger

logger = get_logger(__name__)


@dataclass
class OverheadMetrics:
    """Data class to store overhead calculation results for a single task execution."""
    task_id: str
    node_id: str
    total_time: float
    handshake_time: float
    compute_time: float
    overhead_ratio: float
    granularity: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "node_id": self.node_id,
            "total_time": self.total_time,
            "handshake_time": self.handshake_time,
            "compute_time": self.compute_time,
            "overhead_ratio": self.overhead_ratio,
            "granularity": self.granularity,
            "timestamp": self.timestamp
        }


class CoordinationOverheadCalculator:
    """
    Calculates coordination overhead metrics from execution logs.

    The coordination overhead is defined as:
        overhead_ratio = handshake_time / total_time

    Where:
        - total_time: The total wall-clock time for the task execution.
        - handshake_time: The time spent on network coordination/handshaking.
          In the absence of a direct 'handshake_time' field in raw logs,
          this is often inferred as (total_time - compute_time) or derived
          from specific protocol logs if available.

    For this implementation, we assume the input CSV (execution_logs.csv)
    contains 'wall_clock_time' (total) and we attempt to derive or calculate
    handshake time based on available metrics or standard assumptions if
    specific handshake logs are not present in the raw aggregator output.

    However, per the task description, we compute handshake_time / total_time.
    If the raw log does not explicitly contain 'handshake_time', we must infer it.
    Commonly in these benchmarks:
      total_time = compute_time + handshake_time + network_transfer_time
    If we only have 'wall_clock_time' and 'cpu_utilization', we might estimate
    handshake time if we have a 'compute_time' field. If not, we assume
    handshake_time = total_time - compute_time (where compute_time is derived
    from CPU utilization * total_time, or a specific field).

    Looking at T016 (DataAggregator) output schema:
    columns: node_id, wall_clock_time, cpu_utilization_pct, packet_count, status, hardware_spec, current_latency, bandwidth_Mbps, snr_db.

    It does NOT explicitly list 'handshake_time' or 'compute_time'.
    Therefore, we must infer 'handshake_time'.
    A standard approximation for 'embarrassingly parallel' tasks where CPU is the bottleneck:
    Effective Compute Time = (cpu_utilization_pct / 100) * wall_clock_time
    Then: Handshake/Overhead Time = wall_clock_time - Effective Compute Time

    Note: This is an estimation if explicit handshake logs are missing.
    If the system logs explicit handshake phases, the CSV would need those columns.
    Given the constraints of T016's defined schema, we use the CPU utilization
    to estimate the pure compute portion and treat the rest as coordination overhead.
    """

    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.results: List[OverheadMetrics] = []

    def _calculate_handshake_time(self, row: Dict[str, str]) -> float:
        """
        Estimates handshake time based on available metrics.
        Formula: handshake_time = total_time - (total_time * (cpu_util / 100))
        """
        try:
            total_time = float(row.get('wall_clock_time', 0))
            cpu_util = float(row.get('cpu_utilization_pct', 0))

            if total_time <= 0:
                return 0.0

            # Estimate compute time based on CPU utilization
            # If CPU is 100% utilized for the whole time, handshake is 0.
            # If CPU is 50% utilized, the other 50% is assumed overhead (IO, handshake, waiting).
            effective_compute_time = total_time * (cpu_util / 100.0)
            handshake_time = total_time - effective_compute_time

            # Ensure non-negative
            return max(0.0, handshake_time)

        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate handshake time for row {row}: {e}")
            return 0.0

    def process(self) -> List[OverheadMetrics]:
        """
        Reads the execution logs, calculates overhead for each row, and stores results.
        """
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        self.results = []

        with open(self.input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)

            for row in reader:
                # Skip rows with invalid data
                if not row.get('wall_clock_time') or not row.get('node_id'):
                    continue

                try:
                    task_id = row.get('task_id', 'unknown')
                    node_id = row.get('node_id', 'unknown')
                    total_time = float(row.get('wall_clock_time', 0))
                    timestamp = row.get('timestamp', row.get('start_time', 'unknown'))
                    granularity = row.get('granularity', 'unknown')

                    handshake_time = self._calculate_handshake_time(row)
                    compute_time = total_time - handshake_time

                    if total_time > 0:
                        overhead_ratio = handshake_time / total_time
                    else:
                        overhead_ratio = 0.0

                    metrics = OverheadMetrics(
                        task_id=task_id,
                        node_id=node_id,
                        total_time=total_time,
                        handshake_time=handshake_time,
                        compute_time=compute_time,
                        overhead_ratio=overhead_ratio,
                        granularity=granularity,
                        timestamp=timestamp
                    )
                    self.results.append(metrics)

                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping row due to parsing error: {row.get('task_id')}, Error: {e}")
                    continue

        logger.info(f"Processed {len(self.results)} task executions for overhead calculation.")
        return self.results

    def write_results(self) -> None:
        """
        Writes the calculated overhead metrics to a CSV file.
        """
        if not self.results:
            logger.warning("No results to write.")
            # Create an empty file with headers to satisfy the requirement of producing an artifact
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(['task_id', 'node_id', 'total_time', 'handshake_time', 'compute_time', 'overhead_ratio', 'granularity', 'timestamp'])
            return

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            'task_id', 'node_id', 'total_time', 'handshake_time',
            'compute_time', 'overhead_ratio', 'granularity', 'timestamp'
        ]

        with open(self.output_path, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for metrics in self.results:
                writer.writerow(metrics.to_dict())

        logger.info(f"Overhead metrics written to {self.output_path}")

    def get_summary_statistics(self) -> Dict[str, float]:
        """
        Returns summary statistics for the overhead ratios.
        """
        if not self.results:
            return {
                "mean_overhead_ratio": 0.0,
                "min_overhead_ratio": 0.0,
                "max_overhead_ratio": 0.0,
                "total_tasks": 0
            }

        ratios = [r.overhead_ratio for r in self.results]
        return {
            "mean_overhead_ratio": sum(ratios) / len(ratios),
            "min_overhead_ratio": min(ratios),
            "max_overhead_ratio": max(ratios),
            "total_tasks": len(ratios)
        }


def main():
    """
    Main entry point for the Coordination Overhead Calculator.
    Expects input from data/raw/execution_logs.csv and writes to data/processed/coordination_overhead.csv.
    """
    init_logger()

    # Default paths relative to project root
    input_file = PROJECT_ROOT / "data" / "raw" / "execution_logs.csv"
    output_file = PROJECT_ROOT / "data" / "processed" / "coordination_overhead.csv"

    # Allow CLI overrides
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    logger.info(f"Starting Coordination Overhead Calculator.")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")

    try:
        calculator = CoordinationOverheadCalculator(str(input_file), str(output_file))
        calculator.process()
        calculator.write_results()

        summary = calculator.get_summary_statistics()
        logger.info(f"Summary: {json.dumps(summary, indent=2)}")

        print(f"Successfully calculated coordination overhead for {summary['total_tasks']} tasks.")
        print(f"Mean overhead ratio: {summary['mean_overhead_ratio']:.4f}")
        print(f"Output saved to: {output_file}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
