"""
Baseline execution runner for User Story 1 (US1).
Executes the "Full" active reconstruction strategy on LoCoMo benchmark tasks.
Outputs results to data/processed/baseline_results.csv.
"""
import os
import sys
import time
import json
import logging
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runner import run_batch, save_results_to_csv, ensure_output_dirs
from strategies.full import FullTraversal
from data_loader import load_noisy_graphs, ensure_output_dirs as data_ensure_dirs
from config import get_model_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer for exact string match: lowercasing, stripping punctuation."""
    if not answer:
        return ""
    # Lowercase
    normalized = answer.lower()
    # Strip common punctuation
    import string
    normalized = normalized.translate(str.maketrans('', '', string.punctuation))
    # Strip whitespace
    normalized = normalized.strip()
    return normalized

def load_tasks() -> List[Dict[str, Any]]:
    """
    Load tasks from the raw LoCoMo dataset.
    Expected input: data/raw/locomo.csv
    Returns list of dicts with keys: task_id, question, context, answer
    """
    input_file = PROJECT_ROOT / "data" / "raw" / "locomo.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    tasks = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Ensure task_id exists
            task_id = row.get('task_id', f"task_{idx}")
            tasks.append({
                'task_id': task_id,
                'question': row.get('question', ''),
                'context': row.get('context', ''),
                'answer': row.get('answer', '')
            })
    logger.info(f"Loaded {len(tasks)} tasks from {input_file}")
    return tasks

def evaluate_task(task: Dict[str, Any], graph_data: Dict[str, Any], strategy: FullTraversal) -> Dict[str, Any]:
    """
    Evaluate a single task using the Full traversal strategy.
    Returns a result dict with: task_id, accuracy, nodes_visited, latency_ms, status
    """
    task_id = task['task_id']
    question = task['question']
    context = task['context']
    expected_answer = task['answer']

    # Get graph for this task
    graph = graph_data.get(task_id)
    if graph is None:
        logger.warning(f"No graph found for task {task_id}. Skipping.")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': 0.0,
            'status': 'unresolved'
        }

    # Check for degenerate graphs (handled by strategy, but log here)
    if graph.number_of_nodes() == 0:
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': 0.0,
            'status': 'degenerate'
        }

    start_time = time.time()
    try:
        # Run traversal
        result = strategy.run(task=task, graph=graph)
        nodes_visited = result.get('nodes_visited', 0)
        inferred_answer = result.get('inferred_answer', '')
        status = result.get('status', 'completed')
    except Exception as e:
        logger.error(f"Error running strategy for task {task_id}: {e}")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': 0.0,
            'status': 'unresolved'
        }
    finally:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000.0

    # Calculate accuracy (normalized exact string match)
    normalized_expected = normalize_answer(expected_answer)
    normalized_inferred = normalize_answer(inferred_answer)
    accuracy = 1.0 if normalized_expected == normalized_inferred else 0.0

    return {
        'task_id': task_id,
        'accuracy': accuracy,
        'nodes_visited': nodes_visited,
        'latency_ms': latency_ms,
        'status': status
    }

def main():
    """Main entry point for baseline execution."""
    logger.info("Starting baseline execution runner (T013)...")

    # Ensure output directories exist
    ensure_output_dirs()
    data_ensure_dirs()

    # Load tasks
    tasks = load_tasks()
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        return

    # Load graphs (raw graphs from T011a-1)
    # Note: T013 uses clean graphs (not noisy). Noisy graphs are for T013b.
    graphs_file = PROJECT_ROOT / "data" / "intermediate" / "graphs_raw.json"
    if not graphs_file.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_file}")

    with open(graphs_file, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

    # Initialize strategy
    model_path = get_model_path()
    if not model_path:
        logger.warning("No model path configured. Using mock inference for testing.")
    strategy = FullTraversal(model_path=model_path)

    # Run batch evaluation
    results = run_batch(
        tasks=tasks,
        evaluate_func=lambda t: evaluate_task(t, graph_data, strategy),
        logger=logger
    )

    # Save results to CSV
    output_file = PROJECT_ROOT / "data" / "processed" / "baseline_results.csv"
    save_results_to_csv(results, output_file)

    logger.info(f"Baseline execution complete. Results saved to {output_file}")
    logger.info(f"Total tasks: {len(results)}, Completed: {sum(1 for r in results if r['status'] == 'completed')}")

if __name__ == "__main__":
    main()