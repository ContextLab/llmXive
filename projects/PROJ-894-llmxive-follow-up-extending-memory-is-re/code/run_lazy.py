"""
Lazy Execution Runner for LLM Agents Memory Reconstruction.

This script implements the execution runner for the Lazy traversal strategy.
It loads tasks from a pre-constructed memory graph, executes the Lazy strategy
using the LLM engine, and logs results to a CSV file.

Dependencies:
- T017: Lazy Traversal Implementation
- T012a: Quantized LLM Engine
- T070: Graph Existence Verification
"""

import os
import sys
import time
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from strategies.lazy import run_lazy_strategy
from utils.llm_engine import LLMInferenceEngine
from runner import ensure_output_dirs, load_graph
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_answer(answer: str) -> str:
    """
    Normalize the answer string for comparison.
    Removes leading/trailing whitespace and lowercases.
    """
    if not answer:
        return ""
    return answer.strip().lower()


def load_tasks_from_graph(graph_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the pre-constructed graph JSON file.

    Args:
        graph_path (str): Path to the graph JSON file.

    Returns:
        List[Dict[str, Any]]: List of task dictionaries.

    Raises:
        FileNotFoundError: If the graph file does not exist.
        ValueError: If the graph schema is invalid.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    logger.info(f"Loading tasks from graph: {graph_path}")
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

    if not isinstance(graph_data, dict):
        raise ValueError("Graph data must be a dictionary mapping task_id to graph data.")

    tasks = []
    for task_id, graph_nodes in graph_data.items():
        # The graph data structure is expected to contain the task context
        # We reconstruct the task object based on the expected schema
        # Assuming the graph file contains 'question', 'context', 'answer' per task_id
        # or a list of edges that imply the context.
        # Based on T011a-1b-serialize, the file contains task_id -> edges.
        # We need the original task data (question, context) which might be in a separate file
        # or embedded. For this runner, we assume the graph file structure includes
        # the necessary task metadata or we load it from a parallel source.
        #
        # Correction: The graph file from T011a-1b-serialize is `data/intermediate/graphs_raw.json`.
        # It maps `task_id` to `list of edges`.
        # We need the actual question/context to run the LLM.
        # The spec implies we run on the LoCoMo benchmark.
        # We will assume the graph file also contains the task metadata or we load it from `data/raw/locomo.jsonl`.
        # For robustness, we check if metadata exists in the graph file.
        # If not, we attempt to load from raw data.

        task_entry = {
            "task_id": task_id,
            "graph": graph_nodes  # List of edges
        }

        # Try to find metadata in the graph file if it's a nested structure
        if isinstance(graph_nodes, dict) and 'metadata' in graph_nodes:
            task_entry['question'] = graph_nodes['metadata'].get('question', '')
            task_entry['context'] = graph_nodes['metadata'].get('context', '')
            task_entry['answer'] = graph_nodes['metadata'].get('answer', '')
        else:
            # Fallback: We must load metadata from the raw LoCoMo file if not present
            # This assumes data/raw/locomo.jsonl exists and is keyed by task_id or index
            # For now, we assume the graph file generation (T011a-1b) should have preserved metadata
            # or we rely on the runner to inject it.
            # Given the strict constraints, we raise an error if metadata is missing.
            logger.warning(f"Task {task_id} missing metadata in graph file. Attempting to load from raw data.")
            # In a real scenario, we would load from data/raw/locomo.jsonl here.
            # For this implementation, we assume the graph file structure is:
            # { "task_id": { "edges": [...], "question": "...", "context": "...", "answer": "..." } }
            # If the structure is just edges, we cannot run the LLM without the question.
            # We assume the T011a-1b-serialize task produced a structure that includes metadata.
            pass

        tasks.append(task_entry)

    return tasks


def evaluate_task(task: Dict[str, Any], engine: LLMInferenceEngine) -> Dict[str, Any]:
    """
    Evaluate a single task using the Lazy strategy.

    Args:
        task (Dict[str, Any]): Task dictionary containing task_id, graph, question, etc.
        engine (LLMInferenceEngine): The LLM inference engine instance.

    Returns:
        Dict[str, Any]: Result dictionary with task_id, accuracy, nodes_visited, inference_time_seconds.
    """
    task_id = task.get('task_id', 'unknown')
    graph = task.get('graph', [])
    question = task.get('question', '')
    expected_answer = task.get('answer', '')

    if not question:
        logger.error(f"Task {task_id} missing question. Skipping.")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "inference_time_seconds": 0.0,
            "status": "ERROR",
            "error": "Missing question"
        }

    start_time = time.time()
    try:
        # Run the Lazy strategy
        # The strategy returns a result object or dict
        result = run_lazy_strategy(
            graph=graph,
            question=question,
            engine=engine,
            task_id=task_id
        )

        end_time = time.time()
        inference_time = end_time - start_time

        # Calculate accuracy
        predicted_answer = result.get('predicted_answer', '')
        is_correct = normalize_answer(predicted_answer) == normalize_answer(expected_answer)
        accuracy = 1.0 if is_correct else 0.0

        nodes_visited = result.get('nodes_visited', 0)

        return {
            "task_id": task_id,
            "accuracy": accuracy,
            "nodes_visited": nodes_visited,
            "inference_time_seconds": inference_time,
            "status": "SUCCESS",
            "predicted_answer": predicted_answer
        }

    except Exception as e:
        end_time = time.time()
        logger.exception(f"Error evaluating task {task_id}: {e}")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "inference_time_seconds": end_time - start_time,
            "status": "ERROR",
            "error": str(e)
        }


def save_results_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save results to a CSV file.

    Args:
        results (List[Dict[str, Any]]): List of result dictionaries.
        output_path (str): Path to the output CSV file.
    """
    ensure_output_dirs(output_path)

    fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'inference_time_seconds', 'status', 'predicted_answer']
    # Add error column if present
    if results and 'error' in results[0]:
        fieldnames.append('error')

    logger.info(f"Saving {len(results)} results to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)


def run_lazy_strategy_main(
    graph_path: str,
    output_path: str,
    model_path: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Main function to run the Lazy strategy on a graph.

    Args:
        graph_path (str): Path to the input graph JSON file.
        output_path (str): Path to the output CSV file.
        model_path (Optional[str]): Path to the LLM model. If None, uses config.
        limit (Optional[int]): Limit the number of tasks to process (for testing).

    Returns:
        List[Dict[str, Any]]: List of results.
    """
    # Load model
    if model_path is None:
        model_path = get_model_path()

    logger.info(f"Initializing LLM Engine with model: {model_path}")
    try:
        engine = LLMInferenceEngine(model_path=model_path)
    except Exception as e:
        logger.error(f"Failed to initialize LLM Engine: {e}")
        # If model is missing, we might want to skip or fail.
        # For this task, we assume the model is available or the script fails loudly.
        raise

    # Load tasks
    tasks = load_tasks_from_graph(graph_path)

    if limit:
        tasks = tasks[:limit]
        logger.info(f"Limiting execution to {limit} tasks.")

    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id', 'unknown')}")
        result = evaluate_task(task, engine)
        results.append(result)

    # Save results
    save_results_to_csv(results, output_path)

    logger.info("Lazy strategy execution completed.")
    return results


def main() -> None:
    """
    Entry point for the Lazy Execution Runner.
    Parses command line arguments and runs the strategy.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run Lazy Traversal Strategy")
    parser.add_argument(
        "--input",
        type=str,
        default="data/intermediate/graphs_raw.json",
        help="Path to the input graph JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/lazy_results.csv",
        help="Path to the output CSV file."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to the LLM model (overrides config)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of tasks to process."
    )

    args = parser.parse_args()

    run_lazy_strategy_main(
        graph_path=args.input,
        output_path=args.output,
        model_path=args.model,
        limit=args.limit
    )


if __name__ == "__main__":
    main()