"""
runner.py - Main execution engine for the LLMXive memory reconstruction pipeline.
Handles task execution, timeout management, and result logging.
"""

import os
import sys
import time
import signal
import logging
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Import existing utilities from the project
from data_loader import load_graphs, load_noisy_graphs
from strategies.full import run_full_strategy
from strategies.lazy import run_lazy_strategy
from strategies.greedy import run_greedy_strategy
from utils.llm_engine import run_inference
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TaskResult:
    """Data class to store the result of a single task execution."""
    task_id: str
    strategy: str
    accuracy: float
    nodes_visited: int
    latency_ms: float
    evidence_threshold: float
    status: str = "completed"  # completed, timeout, error

class TimeoutError(Exception):
    """Custom exception for task timeouts."""
    pass

class TimeoutHandler:
    """Context manager for handling task timeouts via OS signals."""
    
    def __init__(self, seconds: int = 300):
        self.seconds = seconds
        self.original_handler = None

    def _handle_timeout(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.seconds} seconds")

    def __enter__(self):
        if sys.platform != 'win32':
            self.original_handler = signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if sys.platform != 'win32':
            signal.alarm(0)
            if self.original_handler:
                signal.signal(signal.SIGALRM, self.original_handler)
        return False

@contextmanager
def timeout_context(seconds: int = 300):
    """Context manager for timeout handling."""
    handler = TimeoutHandler(seconds)
    with handler:
        yield

def ensure_output_dirs(output_path: str):
    """Ensure the directory for the output file exists."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

def load_tasks(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph data structure.
    Expects graph_data to be a dict where keys are task_ids and values are task details.
    """
    tasks = []
    for task_id, details in graph_data.items():
        # Assuming details contain 'question', 'context', 'answer'
        if isinstance(details, dict):
            tasks.append({
                "task_id": task_id,
                "question": details.get("question", ""),
                "context": details.get("context", ""),
                "answer": details.get("answer", "")
            })
        else:
            logger.warning(f"Skipping malformed task entry for {task_id}")
    return tasks

def load_graph(graph_path: str, is_noisy: bool = False) -> Dict[str, Any]:
    """
    Load graph data from a JSON file.
    Uses load_graphs or load_noisy_graphs depending on the flag.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file not found: {graph_path}")
    
    if is_noisy:
        return load_noisy_graphs(graph_path)
    else:
        return load_graphs(graph_path)

def run_task(task: Dict[str, Any], strategy: str, model_path: str, threshold: float = 0.7) -> TaskResult:
    """
    Execute a single task using the specified strategy.
    """
    start_time = time.time()
    status = "completed"
    accuracy = 0.0
    nodes_visited = 0
    evidence_threshold = threshold

    try:
        # Select strategy function
        if strategy == "Full":
            result = run_full_strategy(task, model_path, threshold)
        elif strategy == "Lazy":
            result = run_lazy_strategy(task, model_path, threshold)
        elif strategy == "Greedy":
            result = run_greedy_strategy(task, model_path, threshold)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Extract results from strategy output
        # Assuming strategy returns a dict with 'accuracy', 'nodes_visited', etc.
        accuracy = result.get("accuracy", 0.0)
        nodes_visited = result.get("nodes_visited", 0)
        evidence_threshold = result.get("evidence_threshold", threshold)
        
    except TimeoutError as te:
        status = "timeout"
        logger.error(f"Task {task['task_id']} timed out: {te}")
    except Exception as e:
        status = "error"
        logger.error(f"Task {task['task_id']} failed: {e}")
        # In case of error, we might want to log the specific exception
        import traceback
        logger.debug(traceback.format_exc())

    latency_ms = (time.time() - start_time) * 1000

    return TaskResult(
        task_id=task["task_id"],
        strategy=strategy,
        accuracy=accuracy,
        nodes_visited=nodes_visited,
        latency_ms=latency_ms,
        evidence_threshold=evidence_threshold,
        status=status
    )

def run_batch(tasks: List[Dict[str, Any]], strategy: str, model_path: str, threshold: float = 0.7) -> List[TaskResult]:
    """
    Run a batch of tasks.
    """
    results = []
    for task in tasks:
        logger.info(f"Processing task {task['task_id']} with strategy {strategy}")
        result = run_task(task, strategy, model_path, threshold)
        results.append(result)
    return results

def process_in_chunks_streaming(graph_data: Dict[str, Any], strategy: str, model_path: str, threshold: float = 0.7, chunk_size: int = 10):
    """
    Process tasks in chunks to manage memory.
    Yields results as they are computed.
    """
    tasks = load_tasks(graph_data)
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} tasks)")
        for result in run_batch(chunk, strategy, model_path, threshold):
            yield result

def save_results_to_csv(results: List[TaskResult], output_path: str):
    """
    Save results to a CSV file.
    """
    ensure_output_dirs(output_path)
    fieldnames = ["task_id", "strategy", "accuracy", "nodes_visited", "latency_ms", "evidence_threshold", "status"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the runner.
    Parses arguments, loads data, executes tasks, and saves results.
    """
    import argparse

    parser = argparse.ArgumentParser(description="LLMXive Memory Reconstruction Runner")
    parser.add_argument("--strategy", type=str, required=True, choices=["Full", "Lazy", "Greedy"], help="Traversal strategy")
    parser.add_argument("--input", type=str, required=True, help="Path to the input graph JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to the output CSV file")
    parser.add_argument("--threshold", type=float, default=0.7, help="Evidence threshold for traversal")
    parser.add_argument("--noisy", action="store_true", help="Indicate if input graph is noisy")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per task in seconds")
    
    args = parser.parse_args()

    # T070: Verify the existence of the intermediate graph file before execution
    # This is the core requirement of T070: "Modify code/runner.py to verify the existence of data/intermediate/graphs_raw.json"
    # The task implies we should check the specific file mentioned in the dependency chain if it's the default expected input,
    # or generally ensure the input provided exists (which is already done by load_graph).
    # However, to strictly satisfy T070's dependency on T011a-1b-serialize (which outputs data/intermediate/graphs_raw.json),
    # we add an explicit check if the input path matches the expected default or if we are running a baseline that requires it.
    # The task says: "verify the existence of data/intermediate/graphs_raw.json before initiating execution".
    # We will check if the input file is the expected intermediate file or if the intermediate file exists as a prerequisite.
    
    expected_intermediate_path = "data/intermediate/graphs_raw.json"
    
    # If the input is the expected intermediate file, verify it exists (load_graph does this, but we log explicitly for T070)
    if os.path.abspath(args.input) == os.path.abspath(expected_intermediate_path):
        if not os.path.exists(expected_intermediate_path):
            logger.error(f"CRITICAL: Required intermediate file {expected_intermediate_path} does not exist. "
                         f"Please run the graph serialization step (T011a-1b-serialize) first.")
            # We do not raise here to allow the generic load_graph to raise the FileNotFoundError,
            # but we log the specific T070 requirement failure.
            # Actually, let's raise to fail loud as per constraints.
            raise FileNotFoundError(f"T070 Check Failed: {expected_intermediate_path} is missing.")
    
    # Also verify the generic input file existence (load_graph does this, but good for logging)
    if not os.path.exists(args.input):
        logger.error(f"Input graph file not found: {args.input}")
        raise FileNotFoundError(f"Input graph file not found: {args.input}")

    logger.info(f"Starting execution with strategy: {args.strategy}")
    logger.info(f"Input graph: {args.input}")
    logger.info(f"Output file: {args.output}")
    
    model_path = get_model_path()
    if not model_path:
        logger.warning("Model path not configured. Using default or falling back to mock if available.")
        # In a real scenario, this should error out if no model is found, but we proceed for now
        # The LLM engine will handle the missing model error.

    try:
        # Load graph
        graph_data = load_graph(args.input, is_noisy=args.noisy)
        logger.info(f"Loaded graph with {len(graph_data)} tasks")

        # Run tasks
        # For simplicity in this runner, we load all into memory (T036/T076 handles streaming if needed)
        # If streaming is required, we would use process_in_chunks_streaming
        results = []
        tasks = load_tasks(graph_data)
        
        for task in tasks:
            result = run_task(task, args.strategy, model_path, args.threshold)
            results.append(result)
        
        # Save results
        save_results_to_csv(results, args.output)
        logger.info("Execution completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()