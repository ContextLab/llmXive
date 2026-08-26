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
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TaskResult:
    task_id: str
    accuracy: float
    nodes_visited: int
    latency_ms: float
    status: str
    token_count: int
    evidence_threshold: float = 0.0

class TimeoutError(Exception):
    """Custom timeout error for strategy execution."""
    pass

class TimeoutHandler:
    """
    Context manager for enforcing a hard timeout on a block of code.
    Uses signal.SIGALRM on Unix systems.
    """
    def __init__(self, duration: int = 1800):
        self.duration = duration
        self.old_handler = None

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f"Operation timed out after {self.duration} seconds")

    def __enter__(self):
        # Only set signal handler if we are in the main thread (Unix)
        if os.name != 'nt' and hasattr(signal, 'SIGALRM'):
            self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.duration)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.name != 'nt' and hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel the alarm
            if self.old_handler:
                signal.signal(signal.SIGALRM, self.old_handler)
        return False  # Don't suppress exceptions

def ensure_output_dirs(path: Path):
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def load_graph(graph_path: str) -> Any:
    """
    Load a graph from a JSON file.
    Expected format: {"nodes": [...], "edges": [...]} or a serialized NetworkX graph structure.
    Returns a NetworkX DiGraph or None if loading fails.
    """
    import networkx as nx
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Try to reconstruct NetworkX graph from JSON
        # Assuming standard serialization: {"nodes": [...], "edges": [{"source": ..., "target": ..., "relation": ...}]}
        G = nx.DiGraph()
        
        if 'nodes' in data:
            for node in data['nodes']:
                if isinstance(node, dict):
                    G.add_node(node.get('id', node))
                else:
                    G.add_node(node)
        
        if 'edges' in data:
            for edge in data['edges']:
                if isinstance(edge, dict):
                    src = edge.get('source')
                    tgt = edge.get('target')
                    if src and tgt:
                        G.add_edge(src, tgt, **{k: v for k, v in edge.items() if k not in ['source', 'target']})
                else:
                    # Assume tuple format if not dict
                    src, tgt = edge[0], edge[1]
                    G.add_edge(src, tgt)
        
        logger.info(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    except Exception as e:
        logger.error(f"Failed to load graph from {graph_path}: {e}")
        return None

def load_tasks(tasks_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSON or JSONL file.
    Returns a list of dictionaries.
    """
    tasks = []
    try:
        with open(tasks_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            
            if content.startswith('['):
                # JSON list
                tasks = json.loads(content)
            else:
                # JSONL
                for line in content.split('\n'):
                    if line.strip():
                        tasks.append(json.loads(line))
        
        # Validate schema
        for i, task in enumerate(tasks):
            if 'task_id' not in task:
                logger.warning(f"Task {i} missing 'task_id', using index")
                task['task_id'] = f"task_{i}"
            if 'question' not in task:
                task['question'] = ""
            if 'context' not in task:
                task['context'] = ""
            if 'answer' not in task:
                task['answer'] = ""
        
        return tasks
    except Exception as e:
        logger.error(f"Failed to load tasks from {tasks_path}: {e}")
        return []

def run_task(
    task: Dict[str, Any],
    graph: Any,
    strategy_func: Callable,
    evaluate_func: Callable,
    timeout_handler: TimeoutHandler
) -> TaskResult:
    """
    Run a single task with the given strategy and evaluation function.
    Wraps execution in the timeout handler.
    """
    return evaluate_func(task, graph, strategy_func, timeout_handler)

def run_batch(
    tasks: List[Dict[str, Any]],
    graph: Any,
    strategy_func: Callable,
    evaluate_func: Callable,
    timeout_handler: TimeoutHandler,
    strategy_kwargs: Optional[Dict] = None
) -> List[TaskResult]:
    """
    Run a batch of tasks.
    Note: The timeout handler is applied per task in evaluate_func.
    """
    results = []
    logger.info(f"Starting batch execution of {len(tasks)} tasks")
    
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id', 'unknown')}")
        try:
            result = run_task(task, graph, strategy_func, evaluate_func, timeout_handler)
            results.append(result)
        except Exception as e:
            logger.error(f"Critical error in task {task.get('task_id', i)}: {e}")
            # Record a failure result
            results.append(TaskResult(
                task_id=task.get('task_id', f"task_{i}"),
                accuracy=0.0,
                nodes_visited=0,
                latency_ms=0.0,
                status="UNRESOLVED",
                token_count=0,
                evidence_threshold=0.0
            ))
    
    logger.info(f"Batch execution completed. {len(results)} results recorded.")
    return results

def main():
    """
    CLI entry point for the runner.
    Usage: python runner.py --strategy {full,lazy,greedy} --input GRAPH --tasks TASKS --output OUTPUT [--timeout TIMEOUT] [--topk TOPK]
    """
    import argparse
    from strategies.full import run_full_strategy
    from strategies.lazy import run_lazy_strategy
    from strategies.greedy import run_greedy_strategy

    parser = argparse.ArgumentParser(description="Strategy Execution Runner")
    parser.add_argument('--strategy', type=str, required=True, choices=['full', 'lazy', 'greedy'], 
                        help='Strategy to execute')
    parser.add_argument('--input', type=str, required=True, help='Path to input graph JSON')
    parser.add_argument('--tasks', type=str, required=True, help='Path to tasks JSONL/JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV')
    parser.add_argument('--timeout', type=int, default=1800, help='Timeout in seconds')
    parser.add_argument('--threshold', type=float, default=0.7, help='Evidence threshold for lazy strategy')
    parser.add_argument('--topk', type=int, default=5, help='Top-k edges for greedy strategy')
    
    args = parser.parse_args()

    # Map strategy name to function
    strategy_map = {
        'full': run_full_strategy,
        'lazy': run_lazy_strategy,
        'greedy': run_greedy_strategy
    }
    strategy_func = strategy_map[args.strategy]

    # Load Data
    graph = load_graph(args.input)
    if graph is None:
        raise ValueError("Failed to load graph")
    
    tasks = load_tasks(args.tasks)
    if not tasks:
        raise ValueError("No tasks loaded")

    # Initialize Timeout Handler
    timeout_handler = TimeoutHandler(duration=args.timeout)

    # Define Evaluation Function specific to strategy
    def evaluate_func(task, graph, strat_func, handler):
        from strategies.greedy_runner import evaluate_task as greedy_eval
        from strategies.lazy_runner import evaluate_task as lazy_eval
        from strategies.baseline_runner import evaluate_task as baseline_eval

        if args.strategy == 'greedy':
            return greedy_eval(task, graph, strat_func, handler, topk=args.topk)
        elif args.strategy == 'lazy':
            return lazy_eval(task, graph, strat_func, handler, threshold=args.threshold)
        else:
            return baseline_eval(task, graph, strat_func, handler)

    # Run Batch
    results = run_batch(
        tasks=tasks,
        graph=graph,
        strategy_func=strategy_func,
        evaluate_func=evaluate_func,
        timeout_handler=timeout_handler,
        strategy_kwargs={'threshold': args.threshold, 'topk': args.topk}
    )

    # Save Results
    ensure_output_dirs(Path(args.output))
    fieldnames = [
        'task_id', 'accuracy', 'nodes_visited', 'latency_ms', 
        'status', 'token_count', 'evidence_threshold'
    ]
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    
    logger.info(f"Results written to {args.output}")

if __name__ == "__main__":
    main()
