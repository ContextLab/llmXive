"""
Greedy Execution Runner for User Story 2.

This script implements the execution runner for the Greedy traversal strategy.
It loads tasks from the raw LoCoMo dataset, builds memory graphs, runs the
Greedy strategy, and logs results to a CSV file.

Output: data/processed/greedy_results.csv
Columns: task_id, accuracy, nodes_visited, latency_ms, status
"""
import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports
from strategies.greedy import run_greedy_strategy
from data_loader import load_raw_data, load_graphs, process_in_chunks
from runner import run_task, save_results_to_csv, ensure_output_dirs
from graph_utils import validate_graph, get_graph_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DATA_PATH = DATA_DIR / "raw" / "locomo.csv"
GRAPHS_PATH = PROCESSED_DIR / "graphs" / "graphs_raw.json"
OUTPUT_PATH = PROCESSED_DIR / "greedy_results.csv"

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    return answer.strip().lower()

def load_tasks() -> List[Dict[str, Any]]:
    """Load tasks from the raw LoCoMo dataset."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    tasks = load_raw_data(RAW_DATA_PATH)
    logger.info(f"Loaded {len(tasks)} tasks from {RAW_DATA_PATH}")
    return tasks

def evaluate_task(
    task: Dict[str, Any],
    graphs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a single task using the Greedy strategy.

    Args:
        task: Dictionary containing 'task_id', 'question', 'context', 'answer'
        graphs: Dictionary mapping task_id to graph edges

    Returns:
        Dictionary with results: task_id, accuracy, nodes_visited, latency_ms, status
    """
    task_id = task.get("task_id", "unknown")
    question = task.get("question", "")
    context = task.get("context", "")
    ground_truth = normalize_answer(task.get("answer", ""))

    # Initialize result
    result = {
        "task_id": task_id,
        "accuracy": 0.0,
        "nodes_visited": 0,
        "latency_ms": 0.0,
        "status": "pending"
    }

    try:
        # Get graph for this task
        if task_id not in graphs:
            logger.warning(f"No graph found for task {task_id}. Marking as unresolved.")
            result["status"] = "unresolved"
            return result

        graph_edges = graphs[task_id]

        # Validate graph
        is_valid, stats = validate_graph(graph_edges)
        if not is_valid:
            logger.warning(f"Invalid graph for task {task_id}: {stats.get('error', 'Unknown error')}")
            result["status"] = "invalid_graph"
            return result

        # Handle degenerate graphs (single node or disconnected)
        if stats.get("num_nodes", 0) <= 1:
            logger.warning(f"Degenerate graph (single node) for task {task_id}")
            result["status"] = "degenerate"
            return result

        # Build networkx graph from edges
        import networkx as nx
        G = nx.DiGraph()
        for edge in graph_edges:
            source = edge.get("source")
            target = edge.get("target")
            relation = edge.get("relation_string", "")
            if source and target:
                G.add_edge(source, target, relation=relation)

        # Run Greedy strategy
        start_time = time.time()
        strategy_result = run_greedy_strategy(G, question)
        end_time = time.time()

        latency_ms = (end_time - start_time) * 1000
        nodes_visited = strategy_result.get("nodes_visited", 0)
        predicted_answer = strategy_result.get("predicted_answer", "")
        status = strategy_result.get("status", "completed")

        # Calculate accuracy
        predicted_normalized = normalize_answer(predicted_answer)
        is_correct = (predicted_normalized == ground_truth)
        accuracy = 1.0 if is_correct else 0.0

        result.update({
            "accuracy": accuracy,
            "nodes_visited": nodes_visited,
            "latency_ms": latency_ms,
            "status": status
        })

    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}", exc_info=True)
        result["status"] = "error"
        result["error_message"] = str(e)

    return result

def main():
    """Main entry point for the Greedy Execution Runner."""
    logger.info("Starting Greedy Execution Runner")

    # Ensure output directories exist
    ensure_output_dirs([OUTPUT_PATH])

    # Load tasks
    try:
        tasks = load_tasks()
    except FileNotFoundError as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)

    # Load pre-computed graphs
    if not GRAPHS_PATH.exists():
        logger.error(f"Graphs file not found: {GRAPHS_PATH}. Run data_loader.py first.")
        sys.exit(1)

    try:
        with open(GRAPHS_PATH, 'r', encoding='utf-8') as f:
            graphs = json.load(f)
        logger.info(f"Loaded graphs for {len(graphs)} tasks")
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        sys.exit(1)

    # Process tasks
    results = []
    total_tasks = len(tasks)
    logger.info(f"Processing {total_tasks} tasks with Greedy strategy")

    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{total_tasks}: {task.get('task_id', 'unknown')}")
        result = evaluate_task(task, graphs)
        results.append(result)

        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Completed {i+1}/{total_tasks} tasks")

    # Save results to CSV
    if results:
        save_results_to_csv(results, OUTPUT_PATH)
        logger.info(f"Results saved to {OUTPUT_PATH}")
    else:
        logger.warning("No results to save.")

    # Print summary
    total_completed = sum(1 for r in results if r["status"] == "completed")
    total_errors = sum(1 for r in results if r["status"] == "error")
    total_unresolved = sum(1 for r in results if r["status"] == "unresolved")
    avg_accuracy = sum(r["accuracy"] for r in results) / len(results) if results else 0.0

    logger.info(f"Greedy Execution Summary:")
    logger.info(f"  Total tasks: {total_tasks}")
    logger.info(f"  Completed: {total_completed}")
    logger.info(f"  Errors: {total_errors}")
    logger.info(f"  Unresolved: {total_unresolved}")
    logger.info(f"  Average Accuracy: {avg_accuracy:.4f}")

    logger.info("Greedy Execution Runner completed successfully")

if __name__ == "__main__":
    main()