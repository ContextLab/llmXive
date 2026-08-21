"""
Noisy Baseline Execution Runner for T013b.

Executes the 'Full' active reconstruction strategy on synthetic noisy graphs
(generated in T011c) and logs results to data/processed/noisy_baseline_results.csv.

This script explicitly handles degenerate graphs and timeout states as per T037/T006-1.
"""
import os
import sys
import time
import json
import logging
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from runner import (
    TimeoutError,
    TimeoutHandler,
    load_tasks,
    load_graph,
    run_batch,
    save_results_to_csv,
    process_in_chunks_streaming,
    ensure_output_dirs
)
from strategies.full import run_full_strategy
from graph_utils import validate_graph, get_graph_statistics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the noisy graph input file.
    The input file is expected to be a JSON file where keys are task_ids
    and values are graph structures (edges) or task data associated with the graph.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tasks = []
    # The noisy graph file structure from T011c is expected to be:
    # { "task_id_1": [edges...], "task_id_2": [edges...] }
    # or potentially a list of dicts. We adapt to the most common structure.
    if isinstance(data, dict):
        for task_id, edges in data.items():
            tasks.append({
                "task_id": task_id,
                "graph_edges": edges,
                # We assume the question/answer context is embedded or we need to fetch it.
                # For this runner, we focus on the graph traversal metrics.
                # If the original task data is needed for accuracy, it should be merged here.
                # Since T011c produces graphs, we assume the 'accuracy' metric is derived
                # from a separate oracle or the task context is implicit in the graph structure.
                # However, to be robust, we try to load context if available.
                "context": None,
                "question": None,
                "answer": None
            })
    elif isinstance(data, list):
        # Fallback if it's a list of task objects
        for item in data:
            tasks.append(item)

    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    return tasks

def evaluate_task(task: Dict[str, Any], strategy_func, timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Execute a single task with the specified strategy and timeout handling.
    """
    task_id = task.get("task_id", "unknown")
    graph_edges = task.get("graph_edges", [])

    # Initialize result with default failure state
    result = {
        "task_id": task_id,
        "accuracy": None,
        "nodes_visited": 0,
        "latency_ms": 0.0,
        "status": "UNKNOWN"
    }

    if not graph_edges:
        logger.warning(f"Task {task_id} has no graph edges. Marking as DEGENERATE.")
        result["status"] = "DEGENERATE"
        return result

    # Construct a graph from edges for the strategy
    # We expect edges to be in a format compatible with graph_utils or networkx
    # Assuming edges is a list of dicts: [{"source": "A", "target": "B", ...}]
    # We need to convert this to a format the strategy can use.
    # The strategy expects a networkx graph or similar structure.
    # We'll construct the graph here to pass to the strategy.
    import networkx as nx
    G = nx.DiGraph()
    for edge in graph_edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src and tgt:
            G.add_edge(src, tgt, **edge)

    # Validate graph
    if not validate_graph(G):
        logger.warning(f"Task {task_id} graph validation failed. Marking as DEGENERATE.")
        result["status"] = "DEGENERATE"
        return result

    # Check for degenerate cases (single node, disconnected)
    stats = get_graph_statistics(G)
    if stats.get("node_count", 0) <= 1:
        logger.warning(f"Task {task_id} graph has <= 1 node. Marking as DEGENERATE.")
        result["status"] = "DEGENERATE"
        return result

    # Check connectivity if necessary (though Full strategy handles it)
    if not nx.is_weakly_connected(G):
        logger.info(f"Task {task_id} graph is disconnected. Strategy will handle component traversal.")

    # Execute with timeout
    start_time = time.time()
    try:
        # Use the TimeoutHandler context manager if available, or wrap
        # The runner.py provides a TimeoutHandler class
        with TimeoutHandler(seconds=timeout_seconds):
            # Run the strategy
            # The strategy function is expected to return a result dict
            # We pass the graph G and any necessary task context
            strategy_result = strategy_func(G, task)
            
            elapsed = (time.time() - start_time) * 1000
            
            result["nodes_visited"] = strategy_result.get("nodes_visited", 0)
            result["latency_ms"] = round(elapsed, 2)
            result["accuracy"] = strategy_result.get("accuracy")
            result["status"] = strategy_result.get("status", "COMPLETED")

    except TimeoutError:
        logger.error(f"Task {task_id} timed out after {timeout_seconds}s.")
        result["status"] = "TIMEOUT"
        result["latency_ms"] = round(timeout_seconds * 1000, 2)
    except Exception as e:
        logger.error(f"Task {task_id} failed with exception: {e}", exc_info=True)
        result["status"] = "ERROR"
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)

    return result

def main():
    parser = argparse.ArgumentParser(description="Noisy Baseline Execution Runner (T013b)")
    parser.add_argument("--input", type=str, required=True, help="Path to noisy graphs JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per task in seconds")
    parser.add_argument("--chunk-size", type=int, default=10, help="Number of tasks to process in a batch")
    parser.add_argument("--streaming", action="store_true", help="Enable streaming mode for large datasets")
    args = parser.parse_args()

    # Ensure output directory exists
    ensure_output_dirs(args.output)

    logger.info(f"Starting Noisy Baseline Runner. Input: {args.input}, Output: {args.output}")

    # Load tasks
    tasks = load_tasks(args.input)
    if not tasks:
        logger.warning("No tasks loaded. Exiting.")
        return

    results = []

    if args.streaming:
        # Process in chunks/streaming
        logger.info("Running in streaming mode.")
        # For streaming, we might need to adapt the input loader to yield tasks
        # For now, we assume load_tasks returns a list or generator
        # If it's a list, we can still iterate in chunks
        batch_results = process_in_chunks_streaming(
            tasks, 
            args.chunk_size, 
            lambda task_batch: [evaluate_task(t, run_full_strategy, args.timeout) for t in task_batch]
        )
        for batch in batch_results:
            results.extend(batch)
    else:
        # Process all at once or in batches
        logger.info("Running in batch mode.")
        for i in range(0, len(tasks), args.chunk_size):
            batch = tasks[i:i+args.chunk_size]
            logger.info(f"Processing batch {i//args.chunk_size + 1} ({len(batch)} tasks)")
            batch_results = [evaluate_task(task, run_full_strategy, args.timeout) for task in batch]
            results.extend(batch_results)

    # Save results
    if results:
        save_results_to_csv(results, args.output)
        logger.info(f"Results saved to {args.output}")
    else:
        logger.warning("No results to save.")

if __name__ == "__main__":
    main()