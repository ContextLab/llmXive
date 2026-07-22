"""
Runner module with timeout enforcement and task execution logic.
"""
import os
import time
import signal
import logging
import csv
import json
from pathlib import Path
from typing import Callable, Any, Dict, Optional
from threading import Timer

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom exception for task timeout."""
    pass

class TimeoutHandler:
    """Context manager for enforcing task timeouts."""
    
    def __init__(self, timeout: float):
        self.timeout = timeout
        self.timer = None

    def _timeout_handler(self):
        raise TimeoutError(f"Task timed out after {self.timeout} seconds")

    def __enter__(self):
        self.timer = Timer(self.timeout, self._timeout_handler)
        self.timer.daemon = True
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        return False

def run_task(task_func: Callable, timeout: float = 300, *args, **kwargs) -> Dict[str, Any]:
    """
    Run a task with a timeout.
    
    Args:
        task_func: The function to execute.
        timeout: Maximum time in seconds.
        *args, **kwargs: Arguments to pass to the function.
        
    Returns:
        A dictionary with status, data, and error (if any).
    """
    start_time = time.time()
    try:
        with TimeoutHandler(timeout=timeout):
            result = task_func(*args, **kwargs)
        elapsed = time.time() - start_time
        return {
            "status": "success",
            "data": result,
            "elapsed_time": elapsed
        }
    except TimeoutError as e:
        elapsed = time.time() - start_time
        logger.warning(f"Task timed out after {elapsed:.2f}s: {e}")
        return {
            "status": "timeout",
            "error": str(e),
            "elapsed_time": elapsed
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Task failed with error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "elapsed_time": elapsed
        }

def run_batch(tasks: list, timeout: float = 300) -> list:
    """
    Run a batch of tasks.
    
    Args:
        tasks: List of (func, args, kwargs) tuples.
        timeout: Timeout per task.
        
    Returns:
        List of results.
    """
    results = []
    for i, (func, args, kwargs) in enumerate(tasks):
        logger.info(f"Running task {i+1}/{len(tasks)}")
        res = run_task(func, timeout, *args, **kwargs)
        results.append(res)
    return results

def save_results_to_csv(results: list, output_path: str, columns: list):
    """
    Save task results to a CSV file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
        columns: List of column names to include.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        
        for res in results:
            if res["status"] == "success":
                row = {col: res["data"].get(col, "") for col in columns}
                # Add metadata
                row["task_id"] = res["data"].get("task_id", "unknown")
                row["accuracy"] = res["data"].get("accuracy", 0.0)
                row["nodes_visited"] = res["data"].get("nodes_visited", 0)
                row["latency_ms"] = res["data"].get("latency_ms", 0.0)
                writer.writerow(row)
            else:
                # Log failed tasks
                logger.warning(f"Skipping failed task in CSV: {res.get('error', 'unknown error')}")

def main():
    """Example usage of the runner."""
    def sample_task():
        time.sleep(1)
        return {
            "task_id": "sample_001",
            "accuracy": 0.85,
            "nodes_visited": 10,
            "latency_ms": 1000.0
        }

    result = run_task(sample_task, timeout=5.0)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()