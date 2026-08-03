"""
Metrics Collector for agent execution.

Records step-level metrics including wall-clock time, success flags, and
blocked operation times. Supports streaming and memory-safe accumulation.
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates metrics during agent execution."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.records: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Ensure the output directory exists."""
        dir_name = os.path.dirname(self.output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def reset(self):
        """Reset the collector state."""
        self.records = []
        self.start_time = None

    def record_step(
        self,
        task_id: str,
        latency_ms: float,
        status: str,
        blocked_time_ms: float = 0.0,
        task_type: Optional[str] = None,
        agent_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Record a single step metric.

        Args:
            task_id: Unique identifier for the task.
            latency_ms: Wall-clock time for the step in milliseconds.
            status: 'success' or 'failure'.
            blocked_time_ms: Time spent in blocked operations (excluded from latency).
            task_type: Type of task (e.g., 'occlusion', 'depth').
            agent_type: Type of agent ('2d' or '3d').

        Returns:
            The recorded dictionary.
        """
        record = {
            'task_id': task_id,
            'task_type': task_type or 'unknown',
            'agent_type': agent_type,
            'wall_clock_time_ms': latency_ms,
            'blocked_time_ms': blocked_time_ms,
            'success_flag': status == 'success',
            'timestamp': datetime.now().isoformat()
        }
        self.records.append(record)
        return record

    def save(self):
        """Save collected metrics to the output CSV file."""
        if not self.records:
            logger.warning("No records to save.")
            return

        fieldnames = [
            'task_id', 'task_type', 'agent_type', 'wall_clock_time_ms',
            'blocked_time_ms', 'success_flag', 'timestamp'
        ]

        with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

        logger.info(f"Saved {len(self.records)} records to {self.output_path}")

    def get_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not self.records:
            return {}

        total_time = sum(r['wall_clock_time_ms'] for r in self.records)
        success_count = sum(1 for r in self.records if r['success_flag'])
        total_count = len(self.records)

        return {
            'total_steps': total_count,
            'success_rate': success_count / total_count if total_count > 0 else 0.0,
            'total_time_ms': total_time,
            'avg_time_per_step_ms': total_time / total_count if total_count > 0 else 0.0
        }


def main():
    """CLI entry point for testing the collector."""
    import argparse
    parser = argparse.ArgumentParser(description="Test MetricsCollector")
    parser.add_argument("--output", default="data/test_metrics.csv", help="Output CSV path")
    args = parser.parse_args()

    collector = MetricsCollector(args.output)
    
    # Simulate some data
    collector.record_step("task_1", 100.5, "success", 0.0, "occlusion", "2d")
    collector.record_step("task_2", 200.0, "failure", 5.0, "depth", "2d")
    
    collector.save()
    print(collector.get_summary())


if __name__ == "__main__":
    main()