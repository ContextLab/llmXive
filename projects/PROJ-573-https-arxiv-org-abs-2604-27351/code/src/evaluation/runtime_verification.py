import os
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.utils.logging import get_logger
from src.utils.runtime_monitor import measure_per_task_time, get_monitor

logger = get_logger(__name__)

# Constants
PER_TASK_TIMEOUT_SECONDS = 300  # 5 minutes as per SC-002
DATA_DIR = Path("data")
RUNTIME_METRICS_PATH = DATA_DIR / "runtime_metrics.yaml"


def load_runtime_metrics() -> Dict[str, Any]:
    """Load existing runtime metrics from disk or return an empty structure."""
    if RUNTIME_METRICS_PATH.exists():
        with open(RUNTIME_METRICS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "per_task_verification": [],
        "total_runtime_verification": {"status": "pending", "timestamp": None},
        "metadata": {
            "threshold_per_task_seconds": PER_TASK_TIMEOUT_SECONDS,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    }


def save_runtime_metrics(metrics: Dict[str, Any]) -> None:
    """Save runtime metrics to disk, ensuring the data directory exists."""
    RUNTIME_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(RUNTIME_METRICS_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(metrics, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Runtime metrics saved to {RUNTIME_METRICS_PATH}")


def verify_total_runtime(total_time: float, threshold: float = 14400.0) -> Dict[str, Any]:
    """
    Verify total benchmark runtime against the 4-hour threshold (SC-003).
    Returns a status dictionary.
    """
    status = "PASS" if total_time <= threshold else "FAIL"
    result = {
        "check": "total_runtime",
        "threshold_seconds": threshold,
        "actual_seconds": total_time,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"Total runtime verification: {status} ({total_time:.2f}s <= {threshold}s)")
    return result


def verify_per_task_inference(task_id: str, execution_time: float) -> Dict[str, Any]:
    """
    Verify per-task inference time against the 5-minute threshold (SC-002).
    
    Args:
        task_id: The identifier of the task being verified.
        execution_time: The time taken to execute the task in seconds.
        
    Returns:
        A dictionary containing the verification result.
    """
    threshold = PER_TASK_TIMEOUT_SECONDS
    status = "PASS" if execution_time <= threshold else "FAIL"
    
    result = {
        "task_id": task_id,
        "check": "per_task_inference",
        "threshold_seconds": threshold,
        "actual_seconds": execution_time,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if status == "FAIL":
        logger.warning(f"Task {task_id} exceeded time limit: {execution_time:.2f}s > {threshold}s")
    else:
        logger.info(f"Task {task_id} runtime verification: {status} ({execution_time:.2f}s <= {threshold}s)")
        
    return result


def record_task_verification(task_id: str, execution_time: float) -> Dict[str, Any]:
    """
    Verify a single task's runtime and update the persistent metrics file.
    
    This function implements the core logic for T055c:
    1. Verifies the execution time against SC-002 (5 minutes).
    2. Records the pass/fail status to data/runtime_metrics.yaml.
    """
    # Perform verification
    verification_result = verify_per_task_inference(task_id, execution_time)
    
    # Load existing metrics
    metrics = load_runtime_metrics()
    
    # Initialize per_task_verification list if missing
    if "per_task_verification" not in metrics:
        metrics["per_task_verification"] = []
        
    # Append new result
    metrics["per_task_verification"].append(verification_result)
    
    # Save back to disk
    save_runtime_metrics(metrics)
    
    return verification_result


def generate_runtime_summary() -> Dict[str, Any]:
    """
    Generate a summary of all runtime verifications performed so far.
    """
    metrics = load_runtime_metrics()
    per_task_results = metrics.get("per_task_verification", [])
    
    if not per_task_results:
        return {
            "total_tasks_checked": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "details": []
        }
        
    passed = sum(1 for r in per_task_results if r["status"] == "PASS")
    failed = sum(1 for r in per_task_results if r["status"] == "FAIL")
    total = len(per_task_results)
    
    return {
        "total_tasks_checked": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total) if total > 0 else 0.0,
        "threshold_seconds": PER_TASK_TIMEOUT_SECONDS,
        "details": per_task_results
    }


def main():
    """
    CLI entry point for runtime verification.
    Can be used to:
    1. Verify a specific task if --task-id and --time are provided.
    2. Generate a summary of all recorded verifications.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify runtime constraints (SC-002, SC-003)")
    parser.add_argument("--task-id", type=str, help="Task ID to verify")
    parser.add_argument("--time", type=float, help="Execution time in seconds (required with --task-id)")
    parser.add_argument("--summary", action="store_true", help="Print summary of all verifications")
    
    args = parser.parse_args()
    
    if args.task_id:
        if args.time is None:
            logger.error("--time is required when --task-id is specified")
            return 1
        
        result = record_task_verification(args.task_id, args.time)
        print(f"Verification Result: {result['status']}")
        print(f"Task: {result['task_id']}")
        print(f"Time: {result['actual_seconds']:.2f}s (Limit: {result['threshold_seconds']}s)")
        
    elif args.summary:
        summary = generate_runtime_summary()
        print(f"Runtime Verification Summary:")
        print(f"  Total Tasks: {summary['total_tasks_checked']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Pass Rate: {summary['pass_rate']:.2%}")
        print(f"  Threshold: {summary['threshold_seconds']}s")
    else:
        # Default: Show summary if no specific action requested
        summary = generate_runtime_summary()
        print(f"Current Runtime Metrics Status:")
        print(f"  Tasks Recorded: {summary['total_tasks_checked']}")
        print(f"  Pass Rate: {summary['pass_rate']:.2%}")
        
    return 0


if __name__ == "__main__":
    exit(main())
