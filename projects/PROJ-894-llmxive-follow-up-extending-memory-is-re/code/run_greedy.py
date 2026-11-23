"""
Greedy Execution Runner for the LLMXive Memory Reconstruction Pipeline.

This script executes the "Greedy" traversal strategy on LoCoMo benchmark tasks.
It reads tasks from the graph data, evaluates them using the Greedy strategy,
and logs results to a CSV file.

Dependencies:
  - T018: Greedy traversal implementation (code/strategies/greedy.py)
  - T012a: LLM Inference Engine (code/utils/llm_engine.py)
  - T070: Data flow verification (runner.py checks for graph existence)
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

# Add project root to path to ensure imports work when running from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategies.greedy import run_greedy_strategy
from utils.llm_engine import run_inference
from runner import ensure_output_dirs, TaskResult, TimeoutHandler, timeout_context
from data_loader import load_graphs
from graph_utils import validate_graph, detect_degenerate_graph, handle_degenerate_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "greedy_runner.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize the answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def load_tasks_from_graph(graph_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph JSON file.
    Expects a structure where keys are task_ids and values contain task data.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

    tasks = []
    for task_id, task_data in graph_data.items():
        # Ensure required fields exist
        if 'question' not in task_data or 'context' not in task_data:
            logger.warning(f"Skipping task {task_id} due to missing fields")
            continue

        tasks.append({
            'task_id': task_id,
            'question': task_data['question'],
            'context': task_data['context'],
            'answer': task_data.get('answer', ''),
            'graph': task_data.get('graph', {}), # The subgraph for this task
            'edges': task_data.get('edges', [])  # Explicit edge list if available
        })

    logger.info(f"Loaded {len(tasks)} tasks from {graph_path}")
    return tasks

def evaluate_task(task: Dict[str, Any], model_path: str, evidence_threshold: float = 0.5) -> TaskResult:
    """
    Evaluate a single task using the Greedy strategy.

    Args:
        task: Dictionary containing task data (question, context, graph, etc.)
        model_path: Path to the quantized LLM model
        evidence_threshold: Threshold for evidence accumulation

    Returns:
        TaskResult object containing accuracy, nodes_visited, latency, etc.
    """
    task_id = task['task_id']
    question = task['question']
    context = task['context']
    expected_answer = task.get('answer', '')
    graph_data = task.get('graph', {})
    edges = task.get('edges', [])

    # Handle degenerate graphs
    is_degenerate = detect_degenerate_graph(graph_data, edges)
    if is_degenerate:
        logger.warning(f"Task {task_id}: Degenerate graph detected. Applying fallback.")
        # Fallback: use full context as a single node or skip
        # For now, we log and proceed with a minimal traversal
        nodes_visited = 1
        start_time = time.time()
        with timeout_context(timeout=30): # Short timeout for degenerate cases
            try:
                prompt = f"Question: {question}\nContext: {context}\nAnswer:"
                inferred_answer = run_inference(model_path, prompt)
            except Exception as e:
                logger.error(f"Task {task_id}: Inference failed: {e}")
                inferred_answer = ""
        latency = (time.time() - start_time) * 1000
        accuracy = 1.0 if normalize_answer(inferred_answer) == normalize_answer(expected_answer) else 0.0
        return TaskResult(
            task_id=task_id,
            strategy='Greedy',
            accuracy=accuracy,
            nodes_visited=nodes_visited,
            latency_ms=latency,
            evidence_threshold=evidence_threshold,
            status='degenerate_fallback'
        )

    # Run Greedy Strategy
    logger.info(f"Executing Greedy strategy for task: {task_id}")
    start_time = time.time()

    try:
        # The run_greedy_strategy function handles the traversal and inference
        # It returns the inferred answer and traversal stats
        result = run_greedy_strategy(
            question=question,
            context=context,
            graph=graph_data,
            edges=edges,
            model_path=model_path,
            evidence_threshold=evidence_threshold
        )

        inferred_answer = result.get('answer', '')
        nodes_visited = result.get('nodes_visited', 0)
        evidence_score = result.get('evidence_score', 0.0)
        status = result.get('status', 'completed')

    except Exception as e:
        logger.error(f"Task {task_id}: Greedy strategy execution failed: {e}")
        inferred_answer = ""
        nodes_visited = 0
        status = 'error'

    latency = (time.time() - start_time) * 1000

    # Calculate accuracy
    accuracy = 1.0 if normalize_answer(inferred_answer) == normalize_answer(expected_answer) else 0.0

    return TaskResult(
        task_id=task_id,
        strategy='Greedy',
        accuracy=accuracy,
        nodes_visited=nodes_visited,
        latency_ms=latency,
        evidence_threshold=evidence_threshold,
        status=status
    )

def save_results_to_csv(results: List[TaskResult], output_path: str):
    """Save the list of TaskResults to a CSV file."""
    ensure_output_dirs(output_path)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'task_id', 'strategy', 'accuracy', 'nodes_visited',
            'latency_ms', 'evidence_threshold', 'status'
        ])

        for res in results:
            writer.writerow([
                res.task_id,
                res.strategy,
                res.accuracy,
                res.nodes_visited,
                res.latency_ms,
                res.evidence_threshold,
                res.status
            ])

    logger.info(f"Results saved to {output_path}")

def run_greedy_strategy_main(
    input_graph: str,
    output_csv: str,
    model_path: str,
    evidence_threshold: float = 0.5,
    subset_size: Optional[int] = None
):
    """
    Main entry point for running the Greedy strategy.

    Args:
        input_graph: Path to the input graph JSON file.
        output_csv: Path to the output CSV file.
        model_path: Path to the LLM model.
        evidence_threshold: Threshold for evidence accumulation.
        subset_size: Optional limit on the number of tasks to process.
    """
    logger.info(f"Starting Greedy Execution Runner")
    logger.info(f"Input Graph: {input_graph}")
    logger.info(f"Output CSV: {output_csv}")
    logger.info(f"Model Path: {model_path}")
    logger.info(f"Evidence Threshold: {evidence_threshold}")

    # Verify input file exists (T070 constraint)
    if not os.path.exists(input_graph):
        raise FileNotFoundError(
            f"Input graph file not found: {input_graph}. "
            "Please ensure T011a-1b-serialize has completed."
        )

    # Load tasks
    tasks = load_tasks_from_graph(input_graph)

    if subset_size and subset_size < len(tasks):
        logger.info(f"Processing subset of {subset_size} tasks")
        tasks = tasks[:subset_size]

    if not tasks:
        logger.error("No tasks found to process.")
        # Create an empty CSV with headers to indicate run completion
        save_results_to_csv([], output_csv)
        return

    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task['task_id']}")
        try:
            result = evaluate_task(task, model_path, evidence_threshold)
            results.append(result)
        except Exception as e:
            logger.exception(f"Critical error in task {task['task_id']}: {e}")
            # Record a failure result to keep the run going
            results.append(TaskResult(
                task_id=task['task_id'],
                strategy='Greedy',
                accuracy=0.0,
                nodes_visited=0,
                latency_ms=0.0,
                evidence_threshold=evidence_threshold,
                status='exception'
            ))

    # Save results
    save_results_to_csv(results, output_csv)

    # Summary
    total = len(results)
    completed = sum(1 for r in results if r.status == 'completed')
    accuracy_avg = sum(r.accuracy for r in results) / total if total > 0 else 0.0
    logger.info(f"Greedy Execution Complete. Total: {total}, Completed: {completed}, Avg Accuracy: {accuracy_avg:.2f}")

def main():
    parser = argparse.ArgumentParser(description="Run Greedy Strategy on LoCoMo Tasks")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input graph JSON file (e.g., data/intermediate/graphs_raw.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output CSV file (e.g., data/processed/greedy_results.csv)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/llama-2-7b.Q4_0.gguf",
        help="Path to the quantized LLM model"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Evidence threshold for traversal"
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=None,
        help="Limit processing to the first N tasks"
    )

    args = parser.parse_args()

    run_greedy_strategy_main(
        input_graph=args.input,
        output_csv=args.output,
        model_path=args.model,
        evidence_threshold=args.threshold,
        subset_size=args.subset
    )

if __name__ == "__main__":
    main()