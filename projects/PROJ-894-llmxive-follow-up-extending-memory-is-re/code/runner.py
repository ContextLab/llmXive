"""
Runner module for executing tasks with timeout enforcement and streaming support.
Processes tasks in configurable chunks to manage memory usage.
"""
import os
import time
import signal
import logging
import csv
import json
from typing import List, Dict, Any, Optional, Callable, Iterator
from pathlib import Path

from data_loader import process_in_chunks, load_noisy_graphs, fetch_locomo_dataset
from strategies.full import FullTraversal
from strategies.lazy import LazyTraversal
from strategies.greedy import GreedyTraversal
from inference import LLMInferenceEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom exception for timeout events."""
    pass

class TimeoutHandler:
    """Handles timeout enforcement for task execution."""

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self.old_handler = None

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        if os.name == 'posix':
            self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.timeout_seconds)
        else:
            # Windows doesn't support SIGALRM, use a different mechanism or skip
            logger.warning("Timeout enforcement not fully supported on Windows.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.name == 'posix':
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self.old_handler)
        return False

def run_task(
    task: Dict[str, Any],
    strategy: Callable,
    llm_engine: LLMInferenceEngine,
    timeout_seconds: int = 60
) -> Dict[str, Any]:
    """
    Run a single task with a given strategy and LLM engine.

    Args:
        task: The task dictionary (must contain 'task_id', 'question', 'context', 'answer').
        strategy: A callable that returns a traversal strategy instance.
        llm_engine: The LLM inference engine instance.
        timeout_seconds: Maximum time allowed for the task.

    Returns:
        A dictionary with results: task_id, accuracy, nodes_visited, latency_ms, status.
    """
    task_id = task.get("task_id", "unknown")
    start_time = time.time()
    status = "completed"
    accuracy = 0.0
    nodes_visited = 0

    try:
        with TimeoutHandler(timeout_seconds=timeout_seconds):
            # Initialize strategy
            strategy_instance = strategy()
            # Run strategy (this would typically involve graph traversal and LLM calls)
            # For now, we simulate the execution to demonstrate the structure
            # In a real implementation, this would call strategy_instance.run(task, llm_engine)

            # Simulate work
            time.sleep(0.1)  # Placeholder for actual computation

            # Calculate accuracy (normalized exact match)
            predicted = "simulated_answer" # Placeholder
            expected = task.get("answer", "").lower().strip()
            predicted_clean = predicted.lower().strip()
            accuracy = 1.0 if predicted_clean == expected else 0.0

            # Simulate nodes visited
            nodes_visited = 10 # Placeholder

    except TimeoutError:
        status = "timeout"
        logger.warning(f"Task {task_id} timed out.")
    except Exception as e:
        status = "unresolved"
        logger.error(f"Task {task_id} failed with error: {e}")

    latency_ms = (time.time() - start_time) * 1000

    return {
        "task_id": task_id,
        "accuracy": accuracy,
        "nodes_visited": nodes_visited,
        "latency_ms": latency_ms,
        "status": status
    }

def run_batch(
    tasks: List[Dict[str, Any]],
    strategy: Callable,
    llm_engine: LLMInferenceEngine,
    timeout_seconds: int = 60
) -> List[Dict[str, Any]]:
    """
    Run a batch of tasks.

    Args:
        tasks: List of task dictionaries.
        strategy: Strategy callable.
        llm_engine: LLM engine instance.
        timeout_seconds: Timeout per task.

    Returns:
        List of result dictionaries.
    """
    results = []
    for task in tasks:
        result = run_task(task, strategy, llm_engine, timeout_seconds)
        results.append(result)
    return results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Save results to a CSV file.

    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = ["task_id", "accuracy", "nodes_visited", "latency_ms", "status"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.info(f"Saved {len(results)} results to {output_path}")

def process_in_chunks(
    dataset_iterator: Iterator[Dict[str, Any]],
    chunk_size: int = 100,
    strategy: Callable = None,
    llm_engine: LLMInferenceEngine = None,
    timeout_seconds: int = 60,
    output_path: str = None
):
    """
    Process dataset items in chunks, running tasks and saving results incrementally.

    Args:
        dataset_iterator: Iterator over tasks.
        chunk_size: Number of tasks per chunk.
        strategy: Strategy callable.
        llm_engine: LLM engine instance.
        timeout_seconds: Timeout per task.
        output_path: Path to save results.
    """
    if strategy is None or llm_engine is None:
        raise ValueError("Strategy and LLM engine must be provided.")

    ensure_output_dirs()
    results_file = open(output_path, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(results_file, fieldnames=["task_id", "accuracy", "nodes_visited", "latency_ms", "status"])
    writer.writeheader()

    try:
        for chunk in process_in_chunks(dataset_iterator, chunk_size=chunk_size):
            chunk_results = run_batch(chunk, strategy, llm_engine, timeout_seconds)
            for res in chunk_results:
                writer.writerow(res)
            results_file.flush() # Ensure data is written to disk
            logger.info(f"Processed chunk of {len(chunk)} tasks.")
    finally:
        results_file.close()

def ensure_output_dirs():
    """Create necessary output directories."""
    os.makedirs("data/processed", exist_ok=True)

def main():
    """
    Main entry point for running tasks with streaming support.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run tasks with streaming support.")
    parser.add_argument("--streaming", action="store_true", help="Enable streaming mode.")
    parser.add_argument("--chunk-size", type=int, default=100, help="Number of tasks per chunk.")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per task in seconds.")
    parser.add_argument("--strategy", type=str, default="full", choices=["full", "lazy", "greedy"], help="Traversal strategy.")
    parser.add_argument("--output", type=str, default="data/processed/results.csv", help="Output CSV path.")
    parser.add_argument("--subset", type=str, default="test", help="Dataset split.")

    args = parser.parse_args()

    # Initialize LLM Engine
    llm_engine = LLMInferenceEngine()

    # Select Strategy
    if args.strategy == "full":
        strategy = FullTraversal
    elif args.strategy == "lazy":
        strategy = LazyTraversal
    elif args.strategy == "greedy":
        strategy = GreedyTraversal
    else:
        raise ValueError(f"Unknown strategy: {args.strategy}")

    # Fetch dataset
    ds_iter = fetch_locomo_dataset(subset=args.subset, streaming=args.streaming)

    # Process in chunks
    process_in_chunks(
        ds_iter,
        chunk_size=args.chunk_size,
        strategy=strategy,
        llm_engine=llm_engine,
        timeout_seconds=args.timeout,
        output_path=args.output
    )

if __name__ == "__main__":
    main()