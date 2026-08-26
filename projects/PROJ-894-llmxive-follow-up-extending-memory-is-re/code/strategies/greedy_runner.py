"""
Greedy Execution Runner for T019b.

Implements the execution runner for the Greedy strategy, logging results to
data/processed/greedy_results.csv.

This script:
1. Loads tasks from the intermediate triples/graphs or raw data.
2. Iterates through tasks, running the Greedy traversal strategy.
3. Measures accuracy, nodes_visited, latency, and status.
4. Writes results incrementally to the CSV file.
"""

import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.greedy import run_greedy_strategy
from runner import ensure_output_dirs, load_tasks, load_graph, run_task, TimeoutError
from graph_utils import validate_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison."""
    if not answer:
        return ""
    return answer.lower().strip()

def load_tasks_from_graph(graph_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph JSON file.
    The graph file contains a mapping of task_id -> graph structure.
    We need to reconstruct task objects with question, context, and answer.
    Note: In a real pipeline, we would load tasks from the raw data file
    and match them with graphs. For this runner, we assume the graph file
    contains task metadata or we load tasks separately.
    """
    # For this implementation, we assume tasks are loaded from a separate
    # source (e.g., data/intermediate/triples_raw.jsonl or similar).
    # However, since the runner expects a graph input, we'll try to load
    # tasks from a standard location or generate minimal task objects.

    # Check if we have a corresponding task file
    base_path = Path(graph_path)
    task_file = base_path.parent.parent / "intermediate" / "triples_raw.jsonl"

    if task_file.exists():
        tasks = []
        with open(task_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    task_data = json.loads(line)
                    # Ensure we have the required fields
                    task = {
                        'task_id': task_data.get('task_id', 'unknown'),
                        'question': task_data.get('question', ''),
                        'context': task_data.get('context', ''),
                        'answer': task_data.get('answer', '')
                    }
                    tasks.append(task)
        return tasks
    else:
        # Fallback: try to load from raw data
        raw_file = base_path.parent.parent.parent / "raw" / "locomo.jsonl"
        if raw_file.exists():
            tasks = []
            with open(raw_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        task_data = json.loads(line)
                        task = {
                            'task_id': task_data.get('id', f'task_{len(tasks)}'),
                            'question': task_data.get('question', ''),
                            'context': task_data.get('context', ''),
                            'answer': task_data.get('answer', '')
                        }
                        tasks.append(task)
            return tasks
        else:
            logger.error(f"Could not find task data at {task_file} or {raw_file}")
            return []

def evaluate_task(task: Dict[str, Any], graph: Dict[str, Any], topk: int = 5) -> Dict[str, Any]:
    """
    Execute a single task using the specified strategy.

    Args:
        task: Task dictionary with question, context, answer
        graph: Graph structure for this task
        topk: Number of top edges to consider (for greedy strategy)

    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms, status
    """
    task_id = task.get('task_id', 'unknown')
    logger.info(f"Evaluating task: {task_id}")

    start_time = time.time()
    status = "COMPLETED"
    accuracy = 0.0
    nodes_visited = 0

    try:
        # Run the greedy strategy
        result = run_greedy_strategy(
            question=task.get('question', ''),
            graph=graph,
            topk=topk
        )

        # Extract results
        nodes_visited = result.get('nodes_visited', 0)
        predicted_answer = result.get('predicted_answer', '')

        # Calculate accuracy
        if normalize_answer(predicted_answer) == normalize_answer(task.get('answer', '')):
            accuracy = 1.0
        else:
            accuracy = 0.0

        # Check for special statuses
        if result.get('status') == 'UNRESOLVED':
            status = "UNRESOLVED"
        elif result.get('status') == 'DEGENERATE':
            status = "DEGENERATE"

    except TimeoutError as e:
        logger.warning(f"Task {task_id} timed out: {e}")
        status = "TIMEOUT"
        accuracy = 0.0
        nodes_visited = 0
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}")
        status = "ERROR"
        accuracy = 0.0
        nodes_visited = 0

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    return {
        'task_id': task_id,
        'accuracy': accuracy,
        'nodes_visited': nodes_visited,
        'latency_ms': latency_ms,
        'status': status
    }

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """Save results to CSV file."""
    ensure_output_dirs(output_path)

    fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Greedy Strategy Execution Runner')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input graph JSON file')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to output CSV file')
    parser.add_argument('--topk', type=int, default=5,
                        help='Number of top edges to consider (default: 5)')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Timeout in seconds per task (default: 300)')

    args = parser.parse_args()

    logger.info(f"Starting Greedy Runner with input: {args.input}, output: {args.output}")
    logger.info(f"Top-k: {args.topk}, Timeout: {args.timeout}s")

    # Load tasks
    tasks = load_tasks_from_graph(args.input)
    if not tasks:
        logger.error("No tasks found. Exiting.")
        sys.exit(1)

    logger.info(f"Loaded {len(tasks)} tasks")

    # Load graph
    try:
        graph_data = load_graph(args.input)
    except Exception as e:
        logger.error(f"Failed to load graph: {e}")
        sys.exit(1)

    # Process tasks
    results = []
    for i, task in enumerate(tasks):
        task_id = task.get('task_id', f'task_{i}')

        # Get graph for this task
        # The graph_data might be a dict of task_id -> graph
        if isinstance(graph_data, dict):
            if task_id in graph_data:
                task_graph = graph_data[task_id]
            else:
                # Try to find a graph that matches
                task_graph = None
                for tid, g in graph_data.items():
                    if tid == task_id:
                        task_graph = g
                        break
                if task_graph is None:
                    logger.warning(f"No graph found for task {task_id}, skipping")
                    continue
        else:
            # Assume single graph for all tasks
            task_graph = graph_data

        if not validate_graph(task_graph):
            logger.warning(f"Invalid graph for task {task_id}, skipping")
            continue

        # Evaluate task
        result = evaluate_task(task, task_graph, args.topk)
        results.append(result)

        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(tasks)} tasks")

    # Save results
    save_results_to_csv(results, args.output)

    logger.info(f"Greedy Runner completed. Total tasks: {len(results)}")

if __name__ == '__main__':
    main()