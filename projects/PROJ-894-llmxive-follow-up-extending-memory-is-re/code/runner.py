"""
Runner module for executing strategies on memory graphs.

This module provides the core execution logic, including timeout handling,
task loading, graph loading, and batch execution.
"""

import os
import time
import signal
import logging
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock

# Import strategy runners as needed
# Note: We assume the strategy modules are importable from the code directory
try:
    from strategies.full import run_full_strategy
    from strategies.lazy import run_lazy_strategy
    from strategies.greedy import run_greedy_strategy
except ImportError:
    # Fallback for environment where strategies might not be fully implemented yet
    # In a real run, these should be present
    run_full_strategy = None
    run_lazy_strategy = None
    run_greedy_strategy = None

from data_loader import load_graphs, load_noisy_graphs
from graph_utils import validate_graph, get_graph_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/runner.log')
    ]
)
logger = logging.getLogger(__name__)

# Global lock for signal handler to prevent race conditions in multi-threaded envs
signal_lock = Lock()

@dataclass
class TimeoutError(Exception):
    """Custom exception for task timeout."""
    message: str = "Task execution exceeded the configured timeout limit."

@dataclass
class TaskResult:
    """Data structure for storing task execution results."""
    task_id: str
    accuracy: float
    nodes_visited: int
    latency_ms: float
    status: str  # "COMPLETED", "TIMEOUT", "DEGENERATE", "UNRESOLVED"
    strategy: str
    noise_level: Optional[float] = None
    error_message: Optional[str] = None

class TimeoutHandler:
    """
    OS Signal Handler for enforcing hard timeouts.
    
    Uses SIGALRM on Unix-like systems to interrupt long-running tasks.
    Registered within a context manager to ensure clean state management
    and prevent global state conflicts.
    """
    
    def __init__(self, timeout_seconds: int):
        if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
            raise ValueError("Timeout must be a positive integer.")
        self.timeout_seconds = timeout_seconds
        self._old_handler = None
        self._active = False

    def __enter__(self):
        """Register the signal handler and set the alarm."""
        if os.name == 'nt':
            # Windows does not support SIGALRM natively in the same way
            # We raise an error if timeout is strictly enforced on Windows
            # or use a fallback mechanism (not implemented here for strictness)
            if self.timeout_seconds < 1000: # Arbitrary large number for "no timeout"
                logger.warning("SIGALRM not supported on Windows. Timeout enforcement skipped.")
                return self
        
        self._old_handler = signal.signal(signal.SIGALRM, self._handle_timeout)
        signal.alarm(self.timeout_seconds)
        self._active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cancel the alarm and restore the old signal handler."""
        if self._active:
            signal.alarm(0)  # Cancel the alarm
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)
            self._active = False
        
        # If a TimeoutError was raised, we handle it here by re-raising or converting
        if exc_type is TimeoutError:
            logger.warning(f"Task timed out after {self.timeout_seconds} seconds.")
            # Allow the exception to propagate or handle it
            return False
        
        return False

    def _handle_timeout(self, signum, frame):
        """Signal callback that raises TimeoutError."""
        with signal_lock:
            raise TimeoutError(f"Task execution exceeded {self.timeout_seconds} seconds.")

@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for task timeout.
    Ensures the signal handler is registered only for the duration of the block.
    """
    handler = TimeoutHandler(seconds)
    with handler:
        yield

def ensure_output_dirs(output_path: str) -> Path:
    """Ensure the output directory exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSON or JSONL file.
    Supports both list of dicts and newline-delimited JSON.
    """
    tasks = []
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    content = path.read_text(encoding='utf-8')
    lines = content.strip().split('\n')
    
    if not lines:
        return tasks
    
    try:
        # Try parsing as a single JSON list first
        data = json.loads(content)
        if isinstance(data, list):
            tasks = data
        else:
            # If it's a single object, wrap it
            tasks = [data]
    except json.JSONDecodeError:
        # Fallback to JSONL
        for line in lines:
            if line.strip():
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line: {e}")
    
    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    return tasks

def load_graph(graph_path: str, noisy: bool = False) -> Dict[str, Any]:
    """
    Load graph data from file.
    
    Args:
        graph_path: Path to the graph JSON file.
        noisy: If True, attempts to load noisy graphs structure.
    
    Returns:
        Dictionary mapping task_id to graph structure.
    """
    if not Path(graph_path).exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")
    
    try:
        if noisy:
            return load_noisy_graphs(graph_path)
        else:
            return load_graphs(graph_path)
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        raise

def run_task(
    task: Dict[str, Any],
    graph: Dict[str, Any],
    strategy: str,
    timeout_seconds: int,
    threshold: Optional[float] = None,
    topk: Optional[int] = None
) -> TaskResult:
    """
    Execute a single task with the specified strategy and timeout.
    
    Args:
        task: Task dictionary containing 'task_id', 'question', 'context', etc.
        graph: Full graph dictionary.
        strategy: Strategy name ('full', 'lazy', 'greedy').
        timeout_seconds: Hard timeout for the task execution.
        threshold: Optional threshold for lazy strategy.
        topk: Optional top-k for greedy strategy.
    
    Returns:
        TaskResult object.
    """
    task_id = task.get('task_id', 'unknown')
    logger.info(f"Processing task {task_id} with strategy {strategy}")
    
    # Determine graph substructure if needed (e.g., task-specific subgraph)
    # For now, we assume the graph is global and the strategy handles traversal
    task_graph = graph.get(task_id, graph.get('default', None))
    
    if task_graph is None:
        logger.warning(f"No graph found for task {task_id}. Skipping.")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status="UNRESOLVED",
            strategy=strategy,
            error_message="No graph data available"
        )
    
    # Validate graph
    if not validate_graph(task_graph):
        logger.warning(f"Graph for task {task_id} is invalid. Skipping.")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status="DEGENERATE",
            strategy=strategy,
            error_message="Invalid graph structure"
        )
    
    start_time = time.time()
    result_data = {
        "task_id": task_id,
        "accuracy": 0.0,
        "nodes_visited": 0,
        "status": "COMPLETED"
    }
    
    try:
        with timeout_context(timeout_seconds):
            if strategy == 'full':
                if run_full_strategy is None:
                    raise ImportError("Full strategy module not found")
                result_data = run_full_strategy(task, task_graph)
            elif strategy == 'lazy':
                if run_lazy_strategy is None:
                    raise ImportError("Lazy strategy module not found")
                result_data = run_lazy_strategy(task, task_graph, threshold=threshold)
            elif strategy == 'greedy':
                if run_greedy_strategy is None:
                    raise ImportError("Greedy strategy module not found")
                result_data = run_greedy_strategy(task, task_graph, topk=topk)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
    
    except TimeoutError:
        logger.warning(f"Task {task_id} timed out.")
        result_data["status"] = "TIMEOUT"
        result_data["accuracy"] = 0.0 # Or partial accuracy if tracked
        result_data["nodes_visited"] = 0 # Reset or partial count?
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        result_data["status"] = "UNRESOLVED"
        result_data["error_message"] = str(e)
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    return TaskResult(
        task_id=result_data.get("task_id", task_id),
        accuracy=result_data.get("accuracy", 0.0),
        nodes_visited=result_data.get("nodes_visited", 0),
        latency_ms=latency_ms,
        status=result_data.get("status", "UNRESOLVED"),
        strategy=strategy,
        error_message=result_data.get("error_message")
    )

def run_batch(
    tasks: List[Dict[str, Any]],
    graph: Dict[str, Any],
    strategy: str,
    output_path: str,
    timeout_seconds: int = 60,
    threshold: Optional[float] = None,
    topk: Optional[int] = None,
    noisy: bool = False
) -> List[TaskResult]:
    """
    Run a batch of tasks and save results to CSV.
    
    Args:
        tasks: List of task dictionaries.
        graph: Graph dictionary.
        strategy: Strategy to use.
        output_path: Path to output CSV.
        timeout_seconds: Timeout per task.
        threshold: Strategy-specific threshold.
        topk: Strategy-specific top-k.
        noisy: Whether the graph is noisy.
    
    Returns:
        List of TaskResult objects.
    """
    results = []
    output_file = ensure_output_dirs(output_path)
    
    logger.info(f"Starting batch run for strategy {strategy} on {len(tasks)} tasks.")
    logger.info(f"Output will be written to {output_path}")
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status', 'strategy', 'noise_level']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in tasks:
            result = run_task(
                task=task,
                graph=graph,
                strategy=strategy,
                timeout_seconds=timeout_seconds,
                threshold=threshold,
                topk=topk
            )
            results.append(result)
            
            # Write row immediately to prevent memory buildup
            row = {
                'task_id': result.task_id,
                'accuracy': result.accuracy,
                'nodes_visited': result.nodes_visited,
                'latency_ms': result.latency_ms,
                'status': result.status,
                'strategy': result.strategy,
                'noise_level': 0.1 if noisy else 0.0 # Assumed noise level if noisy
            }
            writer.writerow(row)
    
    logger.info(f"Batch run completed. Results saved to {output_path}")
    return results

def process_in_chunks_streaming(
    tasks_stream: Any,
    graph: Dict[str, Any],
    strategy: str,
    output_path: str,
    chunk_size: int = 10,
    timeout_seconds: int = 60,
    threshold: Optional[float] = None,
    topk: Optional[int] = None,
    noisy: bool = False
) -> None:
    """
    Process tasks in chunks from a stream to manage memory.
    """
    output_file = ensure_output_dirs(output_path)
    logger.info(f"Starting streaming batch run for strategy {strategy}.")
    
    # Open file once and write header
    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status', 'strategy', 'noise_level']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        chunk = []
        for task in tasks_stream:
            chunk.append(task)
            if len(chunk) >= chunk_size:
                for t in chunk:
                    result = run_task(
                        task=t,
                        graph=graph,
                        strategy=strategy,
                        timeout_seconds=timeout_seconds,
                        threshold=threshold,
                        topk=topk
                    )
                    row = {
                        'task_id': result.task_id,
                        'accuracy': result.accuracy,
                        'nodes_visited': result.nodes_visited,
                        'latency_ms': result.latency_ms,
                        'status': result.status,
                        'strategy': result.strategy,
                        'noise_level': 0.1 if noisy else 0.0
                    }
                    writer.writerow(row)
                chunk = []
        
        # Process remaining
        if chunk:
            for t in chunk:
                result = run_task(
                    task=t,
                    graph=graph,
                    strategy=strategy,
                    timeout_seconds=timeout_seconds,
                    threshold=threshold,
                    topk=topk
                )
                row = {
                    'task_id': result.task_id,
                    'accuracy': result.accuracy,
                    'nodes_visited': result.nodes_visited,
                    'latency_ms': result.latency_ms,
                    'status': result.status,
                    'strategy': result.strategy,
                    'noise_level': 0.1 if noisy else 0.0
                }
                writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Runner for LLM Memory Reconstruction Strategies")
    parser.add_argument("--strategy", type=str, required=True, choices=['full', 'lazy', 'greedy'],
                        help="Strategy to use: full, lazy, or greedy")
    parser.add_argument("--input", type=str, required=True, help="Path to input tasks (JSON/JSONL)")
    parser.add_argument("--graph", type=str, required=True, help="Path to graph data (JSON)")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV results")
    parser.add_argument("--threshold", type=float, default=None, help="Threshold for lazy strategy")
    parser.add_argument("--topk", type=int, default=None, help="Top-k for greedy strategy")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per task in seconds")
    parser.add_argument("--streaming", action="store_true", help="Enable streaming processing")
    parser.add_argument("--chunk-size", type=int, default=10, help="Chunk size for streaming")
    parser.add_argument("--noisy", action="store_true", help="Use noisy graph data")
    
    args = parser.parse_args()
    
    logger.info(f"Starting runner with strategy: {args.strategy}")
    logger.info(f"Input tasks: {args.input}")
    logger.info(f"Graph data: {args.graph}")
    logger.info(f"Output: {args.output}")
    
    try:
        # Load tasks
        tasks = load_tasks(args.input)
        if not tasks:
            logger.error("No tasks loaded. Exiting.")
            sys.exit(1)
        
        # Load graph
        graph = load_graph(args.graph, noisy=args.noisy)
        
        if args.streaming:
            # Simple generator for streaming if input is a list
            def task_gen():
                for t in tasks:
                    yield t
            process_in_chunks_streaming(
                tasks_stream=task_gen(),
                graph=graph,
                strategy=args.strategy,
                output_path=args.output,
                chunk_size=args.chunk_size,
                timeout_seconds=args.timeout,
                threshold=args.threshold,
                topk=args.topk,
                noisy=args.noisy
            )
        else:
            run_batch(
                tasks=tasks,
                graph=graph,
                strategy=args.strategy,
                output_path=args.output,
                timeout_seconds=args.timeout,
                threshold=args.threshold,
                topk=args.topk,
                noisy=args.noisy
            )
        
        logger.info("Runner completed successfully.")
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()