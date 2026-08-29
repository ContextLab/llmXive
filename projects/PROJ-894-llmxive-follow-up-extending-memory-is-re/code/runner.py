"""
Runner module for the llmXive automated science pipeline.
Executes tasks with timeout handling and logs results to CSV.
"""

import os
import sys
import time
import signal
import logging
import csv
import json
import argparse
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Project relative imports
from strategies.full import run_full_strategy
from strategies.lazy import run_lazy_strategy
from strategies.greedy import run_greedy_strategy
from inference import LLMInferenceEngine
from graph_utils import validate_graph, get_graph_statistics
from data_loader import load_graphs, load_noisy_graphs, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for status
STATUS_COMPLETED = "COMPLETED"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_DEGENERATE = "DEGENERATE"
STATUS_UNRESOLVED = "UNRESOLVED"
STATUS_ERROR = "ERROR"

VALID_STATUSES = [STATUS_COMPLETED, STATUS_TIMEOUT, STATUS_DEGENERATE, STATUS_UNRESOLVED, STATUS_ERROR]

@dataclass
class TaskResult:
    """Data class to hold the result of a single task execution."""
    task_id: str
    accuracy: float
    nodes_visited: int
    latency_ms: float
    status: str
    error_message: Optional[str] = None

    def to_row(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for CSV row."""
        return {
            'task_id': self.task_id,
            'accuracy': self.accuracy,
            'nodes_visited': self.nodes_visited,
            'latency_ms': self.latency_ms,
            'status': self.status,
            'error_message': self.error_message or ''
        }

class TimeoutError(Exception):
    """Custom exception for timeout events."""
    pass

class TimeoutHandler:
    """Handler for OS signal timeouts."""
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.old_handler = None

    def _handler(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        # Set the signal handler
        self.old_handler = signal.signal(signal.SIGALRM, self._handler)
        signal.alarm(self.timeout_seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset the alarm and handler
        signal.alarm(0)
        if self.old_handler is not None:
            signal.signal(signal.SIGALRM, self.old_handler)
        # Don't suppress exceptions
        return False

@contextmanager
def timeout_context(timeout_seconds: int):
    """Context manager for timeout handling."""
    handler = TimeoutHandler(timeout_seconds)
    with handler:
        yield

def ensure_output_dirs(output_path: str):
    """Ensure the directory for the output file exists."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

def load_tasks(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract tasks from the loaded graph data.
    Expects graph_data to be a dict where keys are task_ids and values are graph structures.
    """
    tasks = []
    for task_id, graph_info in graph_data.items():
        # We assume the graph_info contains the necessary context for the task.
        # In a real scenario, we might need to load the specific context/answer from the raw data.
        # For this runner, we assume the graph structure itself is the task input.
        tasks.append({
            'task_id': task_id,
            'graph': graph_info.get('edges', []),
            # Placeholder for context/answer if needed by the strategy
            'context': graph_info.get('context', ''),
            'answer': graph_info.get('answer', '')
        })
    return tasks

def load_graph(graph_path: str, is_noisy: bool = False) -> Dict[str, Any]:
    """Load graph data from file."""
    if is_noisy:
        return load_noisy_graphs(graph_path)
    return load_graphs(graph_path)

def run_task(
    task: Dict[str, Any],
    strategy_name: str,
    llm_engine: LLMInferenceEngine,
    timeout_seconds: int = 300
) -> TaskResult:
    """
    Execute a single task using the specified strategy.
    Maps degenerate/unresolved states to the CSV status column.
    """
    task_id = task['task_id']
    graph_edges = task['graph']
    
    # Construct a simple graph structure for the strategy
    # Strategies expect a NetworkX graph or a compatible structure.
    # We'll build a minimal graph from edges for the strategy to traverse.
    import networkx as nx
    G = nx.DiGraph()
    for edge in graph_edges:
        G.add_edge(edge['source'], edge['target'], relation=edge.get('relation_string', ''))

    # Check for degenerate graphs (T037 requirement)
    if len(G.nodes()) == 0 or (len(G.nodes()) == 1 and len(G.edges()) == 0):
        logger.warning(f"Task {task_id}: Degenerate graph detected (single node or no edges).")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status=STATUS_DEGENERATE,
            error_message="Degenerate graph: single node or no edges."
        )

    start_time = time.time()
    try:
        with timeout_context(timeout_seconds):
            # Select strategy
            if strategy_name == "Full":
                result = run_full_strategy(G, task.get('context', ''), task.get('answer', ''), llm_engine)
            elif strategy_name == "Lazy":
                # Lazy might need a threshold, defaulting to 0.7 for now if not passed
                result = run_lazy_strategy(G, task.get('context', ''), task.get('answer', ''), llm_engine, evidence_threshold=0.7)
            elif strategy_name == "Greedy":
                result = run_greedy_strategy(G, task.get('context', ''), task.get('answer', ''), llm_engine, top_k=5)
            else:
                raise ValueError(f"Unknown strategy: {strategy_name}")

        # Extract metrics from strategy result
        # Strategies return dict: {'accuracy': float, 'nodes_visited': int, 'latency_ms': float, ...}
        accuracy = float(result.get('accuracy', 0.0))
        nodes_visited = int(result.get('nodes_visited', 0))
        latency_ms = float(result.get('latency_ms', 0.0))
        
        # Determine status
        # If the strategy returned a specific flag for unresolved, map it.
        # Assuming standard return contract for now.
        status = STATUS_COMPLETED

        # Check if the result indicates an unresolved state (e.g., if accuracy is 0 and nodes visited > 0 but no answer found)
        # This depends on the strategy implementation's return values.
        # For robustness, if the strategy explicitly sets a status in its return dict, we respect it.
        if 'status' in result:
            status = result['status']
            if status not in VALID_STATUSES:
                logger.warning(f"Invalid status returned by strategy for {task_id}: {status}. Defaulting to UNRESOLVED.")
                status = STATUS_UNRESOLVED

        return TaskResult(
            task_id=task_id,
            accuracy=accuracy,
            nodes_visited=nodes_visited,
            latency_ms=latency_ms,
            status=status
        )

    except TimeoutError as e:
        logger.error(f"Task {task_id} timed out.")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status=STATUS_TIMEOUT,
            error_message=str(e)
        )
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}", exc_info=True)
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status=STATUS_ERROR,
            error_message=str(e)
        )

def run_batch(
    tasks: List[Dict[str, Any]],
    strategy_name: str,
    output_path: str,
    llm_engine: LLMInferenceEngine,
    timeout_seconds: int = 300
):
    """Run a batch of tasks and save results to CSV."""
    ensure_output_dirs(output_path)
    
    results = []
    for task in tasks:
        logger.info(f"Running task {task['task_id']} with strategy {strategy_name}")
        result = run_task(task, strategy_name, llm_engine, timeout_seconds)
        results.append(result)
        # Log progress
        logger.info(f"Task {task['task_id']} finished: status={result.status}, accuracy={result.accuracy}")

    # Write to CSV
    fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status', 'error_message']
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(res.to_row())
    
    logger.info(f"Results saved to {output_path}")

def process_in_chunks_streaming(tasks, strategy_name, output_path, llm_engine, timeout_seconds=300):
    """
    Process tasks in chunks (streaming) to manage memory.
    For this implementation, it's similar to run_batch but could be extended to yield results.
    """
    run_batch(tasks, strategy_name, output_path, llm_engine, timeout_seconds)

def main():
    """Main entry point for the runner."""
    parser = argparse.ArgumentParser(description="Run baseline/heuristic strategies on graph memory tasks.")
    parser.add_argument('--strategy', type=str, required=True, choices=['Full', 'Lazy', 'Greedy'],
                        help='Traversal strategy to use.')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to the input graph JSON file (clean or noisy).')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to the output CSV file for results.')
    parser.add_argument('--noisy', action='store_true',
                        help='Set if the input graph is a noisy graph.')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Timeout in seconds per task.')
    parser.add_argument('--model-path', type=str, default=None,
                        help='Path to the quantized model (optional, will use config default).')
    
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    # Initialize LLM Engine
    model_path = args.model_path or config.get('model_path', None)
    if not model_path:
        logger.warning("No model path provided. LLM inference will likely fail or use a default if configured.")
    
    llm_engine = LLMInferenceEngine(model_path=model_path)

    # Load Graph Data
    logger.info(f"Loading graph from {args.input}")
    try:
        graph_data = load_graph(args.input, is_noisy=args.noisy)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading graph: {e}")
        sys.exit(1)

    # Extract tasks
    tasks = load_tasks(graph_data)
    if not tasks:
        logger.warning("No tasks found in the input graph file.")
        # Create an empty output file with headers
        ensure_output_dirs(args.output)
        with open(args.output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status', 'error_message'])
            writer.writeheader()
        return

    # Run batch
    logger.info(f"Starting execution for {len(tasks)} tasks with strategy {args.strategy}")
    run_batch(
        tasks=tasks,
        strategy_name=args.strategy,
        output_path=args.output,
        llm_engine=llm_engine,
        timeout_seconds=args.timeout
    )

if __name__ == '__main__':
    main()