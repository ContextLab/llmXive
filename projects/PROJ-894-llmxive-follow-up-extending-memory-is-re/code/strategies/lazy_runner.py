"""
Execution runner for the Lazy traversal strategy.

This script executes the Lazy strategy on the LoCoMo benchmark tasks
and logs results to data/processed/lazy_results.csv.

Parameters:
    - Evidence threshold: 0.7 (default)
    - Output Schema: task_id, accuracy, nodes_visited, latency_ms, status
"""
import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from strategies.lazy import LazyTraversal
from runner import run_batch, save_results_to_csv, ensure_output_dirs
from data_loader import load_noisy_graphs, fetch_locomo_dataset, save_raw_data
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'lazy_runner.log')
    ]
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer for exact string match comparison."""
    if not isinstance(answer, str):
        return str(answer)
    return answer.lower().strip().replace(" ", "").replace(".", "").replace(",", "").replace("!", "").replace("?", "")

def load_tasks(data_dir: Path) -> list:
    """
    Load tasks from the raw LoCoMo dataset.
    Returns a list of dicts with keys: task_id, question, context, answer
    """
    raw_csv_path = data_dir / 'raw' / 'locomo.csv'
    if not raw_csv_path.exists():
        logger.error(f"Raw data file not found: {raw_csv_path}. Run data_loader.py first.")
        raise FileNotFoundError(f"Raw data file not found: {raw_csv_path}")

    tasks = []
    with open(raw_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            tasks.append({
                'task_id': row.get('task_id', f'task_{idx}'),
                'question': row['question'],
                'context': row['context'],
                'answer': row['answer']
            })
    return tasks

def evaluate_task(task: dict, graph: dict, threshold: float = 0.7) -> dict:
    """
    Evaluate a single task using the Lazy strategy.

    Args:
        task: Dict with task_id, question, context, answer
        graph: Dict representing the memory graph for this task
        threshold: Evidence threshold for lazy expansion (default 0.7)

    Returns:
        Dict with task_id, accuracy, nodes_visited, latency_ms, status
    """
    task_id = task['task_id']
    question = task['question']
    expected_answer = task['answer']

    logger.info(f"Evaluating task: {task_id}")

    start_time = time.time()
    status = 'completed'
    accuracy = 0.0
    nodes_visited = 0

    try:
        # Initialize Lazy Traversal with the specified threshold
        strategy = LazyTraversal(evidence_threshold=threshold)

        # Run the strategy
        # Note: The strategy expects a graph object and task context
        # We pass the graph dict and the question
        result = strategy.run(graph, question)

        if result is None:
            logger.warning(f"Task {task_id}: Strategy returned None")
            status = 'unresolved'
            accuracy = 0.0
        else:
            # Extract result components
            predicted_answer = result.get('answer', '')
            nodes_visited = result.get('nodes_visited', 0)
            latency_ms = (time.time() - start_time) * 1000

            # Normalize answers for comparison
            normalized_predicted = normalize_answer(predicted_answer)
            normalized_expected = normalize_answer(expected_answer)

            # Calculate accuracy (binary: exact match)
            if normalized_predicted == normalized_expected:
                accuracy = 1.0
            else:
                accuracy = 0.0

            logger.info(f"Task {task_id}: Predicted='{predicted_answer}', Expected='{expected_answer}', Acc={accuracy}")

    except Exception as e:
        logger.error(f"Task {task_id} failed with exception: {e}", exc_info=True)
        status = 'unresolved'
        accuracy = 0.0
        nodes_visited = 0
        latency_ms = (time.time() - start_time) * 1000

    return {
        'task_id': task_id,
        'accuracy': accuracy,
        'nodes_visited': nodes_visited,
        'latency_ms': latency_ms,
        'status': status
    }

def main():
    """Main entry point for the Lazy strategy runner."""
    parser = argparse.ArgumentParser(description="Run Lazy traversal strategy on LoCoMo benchmark")
    parser.add_argument('--threshold', type=float, default=0.7, help="Evidence threshold for lazy expansion")
    parser.add_argument('--data-dir', type=str, default=str(project_root / 'data'), help="Data directory path")
    parser.add_argument('--output', type=str, default='lazy_results.csv', help="Output filename in data/processed/")
    parser.add_argument('--graph-file', type=str, default='graphs/graph_noise_42.json', help="Path to graph file (relative to data/)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_path = data_dir / 'processed' / args.output
    graph_file_path = data_dir / args.graph_file

    # Ensure output directories exist
    ensure_output_dirs(data_dir)

    logger.info(f"Starting Lazy strategy execution with threshold={args.threshold}")
    logger.info(f"Graph file: {graph_file_path}")
    logger.info(f"Output file: {output_path}")

    # Load tasks
    try:
        tasks = load_tasks(data_dir)
        logger.info(f"Loaded {len(tasks)} tasks")
    except FileNotFoundError as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)

    # Load graphs
    if not graph_file_path.exists():
        logger.error(f"Graph file not found: {graph_file_path}. Run data_loader.py with --generate-graphs first.")
        sys.exit(1)

    try:
        graphs = load_noisy_graphs(graph_file_path)
        logger.info(f"Loaded {len(graphs)} graphs")
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        sys.exit(1)

    # Prepare results list
    results = []

    # Process each task
    for task in tasks:
        task_id = task['task_id']
        # Get the corresponding graph for this task
        # Assuming graphs dict is keyed by task_id
        graph = graphs.get(task_id)

        if graph is None:
            logger.warning(f"No graph found for task {task_id}, skipping")
            results.append({
                'task_id': task_id,
                'accuracy': 0.0,
                'nodes_visited': 0,
                'latency_ms': 0.0,
                'status': 'unresolved'
            })
            continue

        # Evaluate the task
        result = evaluate_task(task, graph, args.threshold)
        results.append(result)

    # Save results to CSV
    save_results_to_csv(results, output_path)
    logger.info(f"Results saved to {output_path}")

    # Summary
    completed = sum(1 for r in results if r['status'] == 'completed')
    total = len(results)
    avg_accuracy = sum(r['accuracy'] for r in results) / total if total > 0 else 0
    avg_latency = sum(r['latency_ms'] for r in results) / total if total > 0 else 0

    logger.info(f"Execution complete: {completed}/{total} completed, Avg Accuracy: {avg_accuracy:.4f}, Avg Latency: {avg_latency:.2f}ms")

if __name__ == '__main__':
    main()