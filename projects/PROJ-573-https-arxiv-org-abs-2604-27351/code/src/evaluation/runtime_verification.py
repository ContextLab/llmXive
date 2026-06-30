"""
Runtime Verification Module for Per-Task Inference Checks.

This module implements verification logic to ensure per-task inference
completes within the 5-minute (300 seconds) limit as specified in SC-002.
It records pass/fail status and detailed timing metrics to data/runtime_metrics.yaml.
"""

import os
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import logging

from src.utils.logging import get_logger

# Constants
PER_TASK_TIMEOUT_SECONDS = 300  # 5 minutes
METRICS_FILE_PATH = "data/runtime_metrics.yaml"
PROJECT_ROOT = Path(__file__).parent.parent.parent

logger = get_logger(__name__)


def load_runtime_metrics() -> Dict[str, Any]:
    """
    Load existing runtime metrics from the YAML file.
    Creates the file with an empty structure if it doesn't exist.
    """
    metrics_path = PROJECT_ROOT / METRICS_FILE_PATH
    if not metrics_path.exists():
        # Ensure data directory exists
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "benchmark_start": None,
            "benchmark_end": None,
            "total_runtime_seconds": None,
            "per_task_metrics": [],
            "verification_summary": {
                "total_tasks": 0,
                "passed": 0,
                "failed": 0,
                "max_allowed_seconds": PER_TASK_TIMEOUT_SECONDS
            }
        }

    try:
        with open(metrics_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Failed to load runtime metrics: {e}")
        return {
            "benchmark_start": None,
            "benchmark_end": None,
            "total_runtime_seconds": None,
            "per_task_metrics": [],
            "verification_summary": {
                "total_tasks": 0,
                "passed": 0,
                "failed": 0,
                "max_allowed_seconds": PER_TASK_TIMEOUT_SECONDS
            }
        }


def save_runtime_metrics(metrics: Dict[str, Any]) -> None:
    """
    Save runtime metrics to the YAML file.
    """
    metrics_path = PROJECT_ROOT / METRICS_FILE_PATH
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    with open(metrics_path, 'w', encoding='utf-8') as f:
        yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Runtime metrics saved to {metrics_path}")


def verify_total_runtime(metrics: Dict[str, Any]) -> bool:
    """
    Verify that total benchmark runtime does not exceed 4 hours (14400 seconds).
    Note: This is a soft check for the overall benchmark, distinct from per-task checks.
    """
    total_runtime = metrics.get("total_runtime_seconds")
    if total_runtime is None:
        logger.warning("Total runtime not recorded yet.")
        return False

    max_total_seconds = 14400  # 4 hours
    if total_runtime > max_total_seconds:
        logger.error(f"Total runtime {total_runtime}s exceeds limit {max_total_seconds}s")
        return False
    return True


def verify_per_task_inference(task_id: str, duration_seconds: float) -> bool:
    """
    Verify that a single task's inference duration is within the 5-minute limit.

    Args:
        task_id: The unique identifier of the task.
        duration_seconds: The measured duration in seconds.

    Returns:
        True if within limit, False otherwise.
    """
    if duration_seconds <= PER_TASK_TIMEOUT_SECONDS:
        logger.info(f"Task {task_id}: {duration_seconds:.2f}s <= {PER_TASK_TIMEOUT_SECONDS}s (PASS)")
        return True
    else:
        logger.error(f"Task {task_id}: {duration_seconds:.2f}s > {PER_TASK_TIMEOUT_SECONDS}s (FAIL)")
        return False


def record_task_verification(
    task_id: str,
    duration_seconds: float,
    passed: bool,
    start_time: float,
    end_time: float
) -> None:
    """
    Record the verification result for a single task to the metrics file.

    Args:
        task_id: The unique identifier of the task.
        duration_seconds: The measured duration in seconds.
        passed: Whether the task passed the time limit check.
        start_time: Start timestamp (float).
        end_time: End timestamp (float).
    """
    metrics = load_runtime_metrics()

    task_record = {
        "task_id": task_id,
        "start_time": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
        "end_time": datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat(),
        "duration_seconds": round(duration_seconds, 3),
        "limit_seconds": PER_TASK_TIMEOUT_SECONDS,
        "status": "PASS" if passed else "FAIL"
    }

    metrics["per_task_metrics"].append(task_record)

    # Update summary counts
    if "verification_summary" not in metrics:
        metrics["verification_summary"] = {
            "total_tasks": 0,
            "passed": 0,
            "failed": 0,
            "max_allowed_seconds": PER_TASK_TIMEOUT_SECONDS
        }

    metrics["verification_summary"]["total_tasks"] += 1
    if passed:
        metrics["verification_summary"]["passed"] += 1
    else:
        metrics["verification_summary"]["failed"] += 1

    save_runtime_metrics(metrics)


def generate_runtime_summary() -> Dict[str, Any]:
    """
    Generate a summary of all runtime verification results.
    """
    metrics = load_runtime_metrics()
    summary = {
        "total_tasks": metrics["verification_summary"]["total_tasks"],
        "passed": metrics["verification_summary"]["passed"],
        "failed": metrics["verification_summary"]["failed"],
        "pass_rate": 0.0,
        "max_allowed_seconds": PER_TASK_TIMEOUT_SECONDS,
        "details": metrics["per_task_metrics"]
    }

    if summary["total_tasks"] > 0:
        summary["pass_rate"] = round(summary["passed"] / summary["total_tasks"], 4)

    return summary


def run_task_with_timing(task_id: str, task_func: Callable, *args, **kwargs) -> tuple:
    """
    Execute a task function while measuring its runtime and verifying against the limit.

    This is a wrapper utility to ensure consistent timing and verification.

    Args:
        task_id: The unique identifier for the task.
        task_func: The callable function to execute.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        A tuple of (result, duration_seconds, passed)
    """
    start_time = time.time()
    try:
        result = task_func(*args, **kwargs)
        duration = time.time() - start_time
        passed = verify_per_task_inference(task_id, duration)
        record_task_verification(task_id, duration, passed, start_time, time.time())
        return result, duration, passed
    except Exception as e:
        duration = time.time() - start_time
        # Treat exceptions as failures for timing purposes if they occur within the time limit
        # or if the timeout caused the exception
        logger.error(f"Task {task_id} failed with exception after {duration:.2f}s: {e}")
        # We still record the time, but mark as failed
        record_task_verification(task_id, duration, False, start_time, time.time())
        raise


def main():
    """
    Main entry point for standalone verification testing.
    Simulates a few tasks to demonstrate the verification logic.
    """
    logger.info("Starting Runtime Verification Demo...")

    # Simulate a few tasks
    def mock_task_1():
        time.sleep(0.5)
        return "Task 1 Result"

    def mock_task_2():
        time.sleep(1.2)
        return "Task 2 Result"

    def mock_task_3():
        time.sleep(0.1)
        return "Task 3 Result"

    tasks = [
        ("T022", mock_task_1),
        ("T023", mock_task_2),
        ("T024", mock_task_3),
    ]

    results = []
    for tid, func in tasks:
        try:
            res, dur, passed = run_task_with_timing(tid, func)
            results.append({"id": tid, "duration": dur, "passed": passed})
        except Exception as e:
            results.append({"id": tid, "error": str(e), "passed": False})

    summary = generate_runtime_summary()
    print(f"\nVerification Summary: {summary['passed']}/{summary['total_tasks']} tasks passed.")
    print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
    logger.info("Runtime Verification Demo Complete.")


if __name__ == "__main__":
    main()