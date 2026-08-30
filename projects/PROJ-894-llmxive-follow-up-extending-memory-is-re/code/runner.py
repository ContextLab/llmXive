import os
import sys
import time
import signal
import logging
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager

# Import from existing API surface
from data_loader import load_graphs, load_noisy_graphs, load_locomo_strict
from strategies.full import run_full_strategy
from strategies.lazy import run_lazy_strategy
from strategies.greedy import run_greedy_strategy
from graph_utils import validate_graph, get_graph_statistics
from config import get_model_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TaskResult:
    task_id: str
    strategy: str
    accuracy: float
    nodes_visited: int
    latency_ms: float
    evidence_threshold: float
    status: str = "COMPLETED"
    error_message: Optional[str] = None

class TimeoutError(Exception):
    pass

class TimeoutHandler:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.original_handler = None

    def handle_timeout(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.seconds} seconds")

    def __enter__(self):
        self.original_handler = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.original_handler:
            signal.signal(signal.SIGALRM, self.original_handler)
        return False

@contextmanager
def timeout_context(seconds: int):
    """Context manager for enforcing hard timeouts."""
    handler = TimeoutHandler(seconds)
    with handler:
        yield

def ensure_output_dirs(output_path: str):
    """Ensure the directory for the output file exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def load_tasks(graph_path: str, noisy: bool = False) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph file.
    If noisy is True, load noisy graphs; otherwise load clean graphs.
    """
    if noisy:
        graphs = load_noisy_graphs(graph_path)
    else:
        graphs = load_graphs(graph_path)
    
    tasks = []
    for task_id, graph_data in graphs.items():
        # Assuming graph_data contains task context
        tasks.append({
            "task_id": task_id,
            "graph": graph_data,
            "context": graph_data.get("context", "")
        })
    return tasks

def load_graph(graph_path: str, noisy: bool = False) -> Dict[str, Any]:
    """Load a specific graph structure."""
    if noisy:
        return load_noisy_graphs(graph_path)
    return load_graphs(graph_path)

def run_task(
    task: Dict[str, Any], 
    strategy: str, 
    model_path: str, 
    timeout_seconds: int = 60
) -> TaskResult:
    """
    Execute a single task with the specified strategy.
    """
    start_time = time.time()
    nodes_visited = 0
    accuracy = 0.0
    status = "COMPLETED"
    error_message = None
    evidence_threshold = 0.5  # Default threshold

    try:
        with timeout_context(timeout_seconds):
            graph = task["graph"]
            
            # Validate graph before traversal
            if not validate_graph(graph):
                logger.warning(f"Invalid graph for task {task['task_id']}")
                status = "DEGENERATE"
                return TaskResult(
                    task_id=task["task_id"],
                    strategy=strategy,
                    accuracy=0.0,
                    nodes_visited=0,
                    latency_ms=(time.time() - start_time) * 1000,
                    evidence_threshold=evidence_threshold,
                    status=status,
                    error_message="Invalid graph structure"
                )

            # Execute strategy
            if strategy == "Full":
                result = run_full_strategy(graph, task.get("context", ""), model_path)
            elif strategy == "Lazy":
                result = run_lazy_strategy(graph, task.get("context", ""), model_path)
            elif strategy == "Greedy":
                result = run_greedy_strategy(graph, task.get("context", ""), model_path)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            nodes_visited = result.get("nodes_visited", 0)
            accuracy = result.get("accuracy", 0.0)
            evidence_threshold = result.get("evidence_threshold", 0.5)
            
            # Check for specific status flags
            if result.get("status") == "UNREACHABLE":
                status = "UNREACHABLE"
            elif result.get("status") == "TIMEOUT":
                status = "TIMEOUT"

    except TimeoutError as e:
        status = "TIMEOUT"
        error_message = str(e)
    except Exception as e:
        status = "ERROR"
        error_message = str(e)
        logger.exception(f"Error executing task {task['task_id']}: {e}")

    latency_ms = (time.time() - start_time) * 1000

    return TaskResult(
        task_id=task["task_id"],
        strategy=strategy,
        accuracy=accuracy,
        nodes_visited=nodes_visited,
        latency_ms=latency_ms,
        evidence_threshold=evidence_threshold,
        status=status,
        error_message=error_message
    )

def run_batch(
    tasks: List[Dict[str, Any]],
    strategy: str,
    output_path: str,
    model_path: str,
    timeout_seconds: int = 60,
    chunk_size: int = 10
):
    """
    Run a batch of tasks and save results to CSV.
    """
    ensure_output_dirs(output_path)
    
    results = []
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1}: {len(chunk)} tasks")
        
        for task in chunk:
            result = run_task(task, strategy, model_path, timeout_seconds)
            results.append(result)
            
            # Log progress
            if result.status != "COMPLETED":
                logger.warning(f"Task {result.task_id} failed: {result.status} - {result.error_message}")

    # Write results to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'task_id', 'strategy', 'accuracy', 'nodes_visited', 
            'latency_ms', 'evidence_threshold', 'status', 'error_message'
        ])
        for r in results:
            writer.writerow([
                r.task_id, r.strategy, r.accuracy, r.nodes_visited,
                r.latency_ms, r.evidence_threshold, r.status, r.error_message
            ])
    
    logger.info(f"Results written to {output_path}")
    return results

def process_in_chunks_streaming(
    tasks_iter: Any, 
    strategy: str, 
    output_path: str, 
    model_path: str, 
    timeout_seconds: int = 60,
    batch_size: int = 5
):
    """
    Process tasks in a streaming fashion to avoid memory overflow.
    Tasks are yielded from an iterator.
    """
    ensure_output_dirs(output_path)
    
    # Initialize CSV with headers
    header_written = False
    fieldnames = ['task_id', 'strategy', 'accuracy', 'nodes_visited', 
                 'latency_ms', 'evidence_threshold', 'status', 'error_message']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        batch = []
        for task in tasks_iter:
            batch.append(task)
            
            if len(batch) >= batch_size:
                if not header_written:
                    writer.writeheader()
                    header_written = True
                
                for task in batch:
                    result = run_task(task, strategy, model_path, timeout_seconds)
                    writer.writerow({
                        'task_id': result.task_id,
                        'strategy': result.strategy,
                        'accuracy': result.accuracy,
                        'nodes_visited': result.nodes_visited,
                        'latency_ms': result.latency_ms,
                        'evidence_threshold': result.evidence_threshold,
                        'status': result.status,
                        'error_message': result.error_message
                    })
                batch = []
        
        # Process remaining tasks
        if batch:
            if not header_written:
                writer.writeheader()
                header_written = True
            for task in batch:
                result = run_task(task, strategy, model_path, timeout_seconds)
                writer.writerow({
                    'task_id': result.task_id,
                    'strategy': result.strategy,
                    'accuracy': result.accuracy,
                    'nodes_visited': result.nodes_visited,
                    'latency_ms': result.latency_ms,
                    'evidence_threshold': result.evidence_threshold,
                    'status': result.status,
                    'error_message': result.error_message
                })
    
    logger.info(f"Streaming results written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run memory graph traversal strategies")
    parser.add_argument("--strategy", type=str, required=True, 
                      choices=["Full", "Lazy", "Greedy"], 
                      help="Traversal strategy to use")
    parser.add_argument("--input", type=str, required=True,
                      help="Path to the input graph file (JSON)")
    parser.add_argument("--output", type=str, required=True,
                      help="Path to the output CSV file")
    parser.add_argument("--noisy", action="store_true",
                      help="Use noisy graphs instead of clean ones")
    parser.add_argument("--timeout", type=int, default=60,
                      help="Timeout in seconds per task")
    parser.add_argument("--threshold", type=float, default=0.5,
                      help="Evidence threshold for decision making")
    
    args = parser.parse_args()

    # T070: Fix Data Flow Dependency - Verify existence of graphs_raw.json
    # If the input is the intermediate graph file, verify it exists first
    input_path = Path(args.input)
    if args.input.endswith("graphs_raw.json") or "intermediate" in args.input:
        if not input_path.exists():
            logger.error(f"Critical dependency missing: {args.input}")
            logger.error("Please run the data extraction pipeline (T011a-1a, T011a-1b-serialize) first.")
            sys.exit(1)
    
    # Load model path
    model_path = get_model_path()
    if not model_path or not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}. Using placeholder logic.")
        # In a real scenario, we might exit or use a mock
    
    # Load tasks
    logger.info(f"Loading tasks from {args.input}")
    try:
        tasks = load_tasks(args.input, noisy=args.noisy)
    except FileNotFoundError as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        sys.exit(1)

    if not tasks:
        logger.warning("No tasks found in the input file.")
        # Create an empty output file with headers
        ensure_output_dirs(args.output)
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'strategy', 'accuracy', 'nodes_visited', 
                           'latency_ms', 'evidence_threshold', 'status', 'error_message'])
        return

    logger.info(f"Running strategy '{args.strategy}' on {len(tasks)} tasks")
    
    # Run batch
    run_batch(
        tasks=tasks,
        strategy=args.strategy,
        output_path=args.output,
        model_path=model_path,
        timeout_seconds=args.timeout
    )

    logger.info("Execution completed successfully.")

if __name__ == "__main__":
    main()