"""
Runner module for executing strategies on tasks.
"""

import os
import time
import signal
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import strategy modules
from strategies.full import run_full_strategy
from strategies.lazy import run_lazy_strategy
from strategies.greedy import run_greedy_strategy
from data_loader import load_raw_data, load_graphs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

class TimeoutHandler:
    def __init__(self, timeout: int):
        self.timeout = timeout
        self.original_handler = None

    def handle_timeout(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.timeout} seconds")

    def __enter__(self):
        self.original_handler = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.original_handler:
            signal.signal(signal.SIGALRM, self.original_handler)

def load_tasks(input_path: Path) -> List[Dict[str, Any]]:
    """Load tasks from a JSONL file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    return tasks

def load_graph(graph_path: Path) -> Dict[str, Any]:
    """Load graph data from a JSON file."""
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_task(task: Dict[str, Any], graph_data: Dict[str, Any], strategy: str, **kwargs) -> Dict[str, Any]:
    """
    Run a single task with the specified strategy.

    Args:
        task: The task dictionary.
        graph_data: The graph data dictionary.
        strategy: The strategy name ('full', 'lazy', 'greedy').
        **kwargs: Additional arguments for the strategy.

    Returns:
        Dictionary containing the execution results.
    """
    strategy_map = {
        'full': run_full_strategy,
        'lazy': run_lazy_strategy,
        'greedy': run_greedy_strategy
    }

    if strategy not in strategy_map:
        raise ValueError(f"Unknown strategy: {strategy}")

    try:
        result = strategy_map[strategy](task, graph_data, **kwargs)
        result['status'] = result.get('status', 'success')
        return result
    except Exception as e:
        logger.error(f"Error running task {task.get('task_id')}: {e}")
        return {
            'task_id': task.get('task_id', 'unknown'),
            'status': 'error',
            'error': str(e),
            'nodes_visited': 0,
            'latency_ms': 0,
            'accuracy': 0.0
        }

def run_batch(tasks: List[Dict[str, Any]], graph_data: Dict[str, Any], strategy: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Run a batch of tasks with the specified strategy.

    Args:
        tasks: List of task dictionaries.
        graph_data: The graph data dictionary.
        strategy: The strategy name.
        **kwargs: Additional arguments for the strategy.

    Returns:
        List of result dictionaries.
    """
    results = []
    for task in tasks:
        result = run_task(task, graph_data, strategy, **kwargs)
        results.append(result)
    return results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: Path):
    """
    Save results to a CSV file.

    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.warning("No results to save.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status']
    # Add strategy-specific fields
    for key in results[0].keys():
        if key not in fieldnames:
            fieldnames.append(key)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            # Ensure all fields are present
            row = {k: result.get(k, '') for k in fieldnames}
            writer.writerow(row)

def process_in_chunks_streaming(tasks: List[Dict[str, Any]], graph_data: Dict[str, Any], strategy: str, chunk_size: int, **kwargs):
    """
    Process tasks in chunks using streaming mode.

    Args:
        tasks: List of task dictionaries.
        graph_data: The graph data dictionary.
        strategy: The strategy name.
        chunk_size: Number of tasks per chunk.
        **kwargs: Additional arguments for the strategy.
    """
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        results = run_batch(chunk, graph_data, strategy, **kwargs)
        # Process results immediately
        for result in results:
            logger.info(f"Processed task {result.get('task_id')}: {result.get('status')}")

def ensure_output_dirs():
    """Create output directories if they don't exist."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for the runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run strategies on tasks.")
    parser.add_argument('--streaming', action='store_true', help="Enable streaming mode")
    parser.add_argument('--chunk-size', type=int, default=10, help="Chunk size for streaming")
    parser.add_argument('--timeout', type=int, default=60, help="Timeout in seconds per task")
    parser.add_argument('--strategy', type=str, choices=['full', 'lazy', 'greedy'], required=True, help="Strategy to use")
    parser.add_argument('--input', type=str, required=True, help="Input tasks file (JSONL)")
    parser.add_argument('--graph', type=str, required=True, help="Graph data file (JSON)")
    parser.add_argument('--output', type=str, required=True, help="Output CSV file")
    parser.add_argument('--threshold', type=float, default=0.7, help="Threshold for lazy strategy")
    parser.add_argument('--topk', type=int, default=5, help="Top-k for greedy strategy")
    parser.add_argument('--subset', type=int, default=None, help="Number of tasks to process")

    args = parser.parse_args()

    ensure_output_dirs()

    # Load tasks
    logger.info(f"Loading tasks from {args.input}")
    tasks = load_tasks(Path(args.input))

    if args.subset:
        tasks = tasks[:args.subset]
        logger.info(f"Processing subset of {len(tasks)} tasks")

    # Load graph
    logger.info(f"Loading graph from {args.graph}")
    graph_data = load_graph(Path(args.graph))

    # Prepare strategy arguments
    strategy_kwargs = {}
    if args.strategy == 'lazy':
        strategy_kwargs['threshold'] = args.threshold
    elif args.strategy == 'greedy':
        strategy_kwargs['topk'] = args.topk

    # Run tasks
    logger.info(f"Running {args.strategy} strategy on {len(tasks)} tasks")
    
    if args.streaming:
        process_in_chunks_streaming(tasks, graph_data, args.strategy, args.chunk_size, **strategy_kwargs)
        # For streaming, we might save results incrementally
        # Here we collect all results for simplicity
        results = run_batch(tasks, graph_data, args.strategy, **strategy_kwargs)
    else:
        results = run_batch(tasks, graph_data, args.strategy, **strategy_kwargs)

    # Save results
    output_path = Path(args.output)
    save_results_to_csv(results, output_path)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
