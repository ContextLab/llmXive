"""
Runner module for executing tasks with timeout enforcement and batch processing.
"""
import os
import time
import signal
import logging
import csv
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout error for task execution."""
    pass

class TimeoutHandler:
    """Handler for timeout events."""
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
    
    def handle_timeout(self, task_id: str) -> Dict[str, Any]:
        """Handle a timeout event for a specific task."""
        logger.warning(f"Task {task_id} timed out after {self.timeout_seconds}s")
        return {
            "task_id": task_id,
            "status": "timeout",
            "error": f"Task exceeded {self.timeout_seconds}s timeout"
        }

def _run_task_with_timeout(task: Dict[str, Any], executor_func: Callable, timeout_seconds: float) -> Dict[str, Any]:
    """
    Run a single task with a hard timeout.
    Uses multiprocessing to enforce the timeout strictly.
    """
    task_id = task["id"]
    context = task.get("context", {})
    
    def worker(q, task_id, context):
        try:
            result = executor_func(task_id, context)
            q.put(("success", result))
        except Exception as e:
            q.put(("error", str(e)))
    
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=worker, 
        args=(queue, task_id, context)
    )
    process.start()
    process.join(timeout=timeout_seconds)
    
    if process.is_alive():
        process.terminate()
        process.join()
        logger.warning(f"Task {task_id} forcibly terminated due to timeout")
        return {
            "task_id": task_id,
            "status": "timeout",
            "error": f"Task exceeded {timeout_seconds}s timeout"
        }
    
    try:
        status, result = queue.get(timeout=1)
        if status == "error":
            return {
                "task_id": task_id,
                "status": "error",
                "error": result
            }
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve result for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e)
        }

def run_task(task: Dict[str, Any], executor: Callable, timeout_seconds: float = 300) -> Dict[str, Any]:
    """
    Execute a single task with timeout enforcement.
    
    Args:
        task: Task dictionary with 'id' and 'context'.
        executor: Callable(task_id, context) -> result dict.
        timeout_seconds: Maximum execution time in seconds.
    
    Returns:
        Result dictionary or timeout/error dictionary.
    """
    logger.info(f"Starting task {task['id']}")
    start_time = time.time()
    
    result = _run_task_with_timeout(task, executor, timeout_seconds)
    
    elapsed = time.time() - start_time
    if "latency_ms" not in result:
        result["latency_ms"] = elapsed * 1000
    
    logger.info(f"Task {task['id']} completed in {elapsed:.2f}s")
    return result

def run_batch(
    tasks: List[Dict[str, Any]], 
    executor: Callable, 
    output_path: str, 
    timeout_seconds: float = 300
) -> None:
    """
    Run a batch of tasks and write results to a CSV file.
    
    Args:
        tasks: List of task dictionaries.
        executor: Callable(task_id, context) -> result dict.
        output_path: Path to the output CSV file.
        timeout_seconds: Timeout per task.
    """
    logger.info(f"Starting batch execution of {len(tasks)} tasks")
    results = []
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    for task in tasks:
        result = run_task(task, executor, timeout_seconds)
        results.append(result)
    
    # Write results to CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Results written to {output_path}")
    else:
        logger.warning("No results to write")

def main():
    """Example usage of the runner."""
    # This is a placeholder for command-line execution if needed
    pass

if __name__ == "__main__":
    main()