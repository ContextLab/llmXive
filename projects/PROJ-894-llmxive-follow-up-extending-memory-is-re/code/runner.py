"""
Runner module with timeout enforcement and task execution logic.
Implements chunked processing for large datasets to stay within RAM limits.
"""
import os
import time
import signal
import logging
import csv
import json
from pathlib import Path
from typing import Callable, Any, Dict, Optional, List, Iterator
from threading import Timer

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000

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

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str, columns: List[str]):
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
            # Ensure all columns are present, fill with defaults if missing
            row = {col: res.get(col, "") for col in columns}
            writer.writerow(row)

def process_in_chunks(data_iterator: Iterator[Any], process_func: Callable, chunk_size: int = CHUNK_SIZE, timeout: float = 300):
    """
    Process an iterator of data in chunks to manage memory usage.
    
    Args:
        data_iterator: Iterator yielding data items.
        process_func: Function to process a batch (list) of items. Should return a list of results.
        chunk_size: Number of items per chunk.
        timeout: Timeout for each chunk processing.
        
    Yields:
        Individual result dictionaries.
    """
    chunk = []
    total_processed = 0
    
    for item in data_iterator:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            logger.info(f"Processing chunk of {len(chunk)} items (total: {total_processed})...")
            chunk_results = run_batch(
                [(process_func, (task,), {}) for task in chunk],
                timeout=timeout
            )
            for res in chunk_results:
                if res['status'] == 'success':
                    yield res['data']
                else:
                    # Log error but continue
                    logger.error(f"Chunk processing failed: {res.get('error')}")
                    yield {
                        "task_id": "unknown",
                        "status": "error",
                        "error": res.get('error')
                    }
            total_processed += len(chunk)
            chunk = []
    
    # Process remaining items
    if chunk:
        logger.info(f"Processing final chunk of {len(chunk)} items...")
        chunk_results = run_batch(
            [(process_func, (task,), {}) for task in chunk],
            timeout=timeout
        )
        for res in chunk_results:
            if res['status'] == 'success':
                yield res['data']
            else:
                logger.error(f"Final chunk processing failed: {res.get('error')}")
                yield {
                    "task_id": "unknown",
                    "status": "error",
                    "error": res.get('error')
                }
        total_processed += len(chunk)
    
    logger.info(f"Total items processed: {total_processed}")

def main():
    """Example usage of the runner."""
    def sample_task(task):
        time.sleep(0.1)
        return {
            "task_id": task.get('id', 'unknown'),
            "accuracy": 0.85,
            "nodes_visited": 10,
            "latency_ms": 1000.0
        }

    # Simulate an iterator
    def mock_iterator():
        for i in range(5):
            yield {'id': f'task_{i}'}

    results = list(process_in_chunks(mock_iterator(), sample_task, chunk_size=2))
    save_results_to_csv(results, "data/processed/test_results.csv", ["task_id", "accuracy", "nodes_visited", "latency_ms"])
    print(f"Saved {len(results)} results.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
