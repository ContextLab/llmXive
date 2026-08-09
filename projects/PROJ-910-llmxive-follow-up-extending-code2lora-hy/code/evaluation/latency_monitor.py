import time
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def measure_inference_latency(
    task_id: str,
    inference_func,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Measure the inference latency of a single task.

    Args:
        task_id: Unique identifier for the task.
        inference_func: Callable that performs the inference.
        *args: Positional arguments to pass to the inference function.
        **kwargs: Keyword arguments to pass to the inference function.

    Returns:
        A dictionary containing the task_id and latency in milliseconds.
    """
    logger.info(f"Measuring latency for task: {task_id}")
    start_time = time.perf_counter()
    try:
        result = inference_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error during inference for task {task_id}: {e}")
        # Return a latency entry with 0 or -1 to indicate failure, or raise
        # Depending on runner logic, we might want to record the failure time too
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        return {
            "task_id": task_id,
            "latency_ms": latency_ms,
            "status": "error",
            "error": str(e)
        }
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000

    logger.debug(f"Task {task_id} completed in {latency_ms:.2f} ms")
    return {
        "task_id": task_id,
        "latency_ms": latency_ms,
        "status": "success"
    }


def save_latency_results(
    results: List[Dict[str, Any]],
    output_path: str
) -> Path:
    """
    Save latency results to a CSV file.

    Args:
        results: List of dictionaries containing task_id and latency_ms.
        output_path: Path to the output CSV file.

    Returns:
        The Path object of the created file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving latency results to {output_file}")

    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['task_id', 'latency_ms', 'status', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            # Ensure all fields are present, filling with empty string if missing
            row = {
                'task_id': result.get('task_id', ''),
                'latency_ms': result.get('latency_ms', 0),
                'status': result.get('status', 'unknown'),
                'error': result.get('error', '')
            }
            writer.writerow(row)

    logger.info(f"Successfully saved {len(results)} latency records to {output_file}")
    return output_file


def collect_latency_stats(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate basic statistics from latency results.

    Args:
        results: List of dictionaries containing latency_ms.

    Returns:
        Dictionary with min, max, mean, and median latency.
    """
    latencies = [r['latency_ms'] for r in results if r.get('status') == 'success']

    if not latencies:
        return {
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "count": 0
        }

    latencies.sort()
    n = len(latencies)
    return {
        "min": latencies[0],
        "max": latencies[-1],
        "mean": sum(latencies) / n,
        "median": latencies[n // 2] if n % 2 == 1 else (latencies[n // 2 - 1] + latencies[n // 2]) / 2,
        "count": n
    }
