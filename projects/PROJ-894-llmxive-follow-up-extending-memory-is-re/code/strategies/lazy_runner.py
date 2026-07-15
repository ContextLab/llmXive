"""
Runner for the Lazy traversal strategy on LoCoMo benchmark tasks.
Executes tasks using the Lazy strategy and logs results to CSV.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import fetch_locomo_dataset, ensure_output_dirs
from runner import run_batch, TimeoutHandler
from strategies.lazy import LazyTraversal
from graph_utils import build_memory_graph, validate_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default threshold for Lazy strategy (can be overridden)
DEFAULT_THRESHOLD = 0.8

def load_tasks(dataset_name: str = "locomo/locomo-benchmark", split: str = "test") -> List[Dict[str, Any]]:
    """
    Load tasks from the specified dataset.
    Returns a list of task dictionaries with 'id', 'context' (question, context, answer).
    """
    try:
        data = fetch_locomo_dataset(dataset_name, split)
        tasks = []
        for idx, item in enumerate(data):
            task = {
                "id": f"locomo_{idx}",
                "context": {
                    "question": item.get("question", ""),
                    "context": item.get("context", ""),
                    "answer": item.get("answer", "")
                }
            }
            tasks.append(task)
        logger.info(f"Loaded {len(tasks)} tasks from {dataset_name} split {split}")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        raise

def evaluate_task(task_id: str, context: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """
    Evaluate a single task using the Lazy traversal strategy.
    
    Args:
        task_id: Unique identifier for the task.
        context: Dictionary containing 'question', 'context', and 'answer'.
        threshold: Evidence threshold for the Lazy strategy.
    
    Returns:
        Dictionary with task_id, accuracy (bool), nodes_visited, and latency_ms.
    """
    question = context.get("question", "")
    memory_context = context.get("context", "")
    ground_truth = context.get("answer", "")

    if not question or not memory_context:
        logger.warning(f"Task {task_id} missing question or context, skipping.")
        return {
            "task_id": task_id,
            "status": "skipped",
            "accuracy": None,
            "nodes_visited": 0,
            "latency_ms": 0
        }

    try:
        # Build memory graph from context
        # Note: build_memory_graph expects a list of text chunks or a single string
        # We pass the context string directly, assuming it will be tokenized/split internally
        graph = build_memory_graph([memory_context])
        
        if not validate_graph(graph):
            logger.warning(f"Task {task_id} generated invalid graph, skipping.")
            return {
                "task_id": task_id,
                "status": "invalid_graph",
                "accuracy": None,
                "nodes_visited": 0,
                "latency_ms": 0
            }

        # Initialize Lazy Traversal
        strategy = LazyTraversal(threshold=threshold)
        
        # Execute traversal
        start_time = time.time()
        result = strategy.traverse(graph, question)
        elapsed_ms = (time.time() - start_time) * 1000

        # Determine accuracy (simple string match for now, can be extended)
        # In a real scenario, this might involve an LLM judge or semantic similarity
        predicted_answer = result.get("answer", "")
        accuracy = (predicted_answer.strip().lower() == ground_truth.strip().lower())

        return {
            "task_id": task_id,
            "status": "success",
            "accuracy": accuracy,
            "nodes_visited": result.get("nodes_visited", 0),
            "latency_ms": elapsed_ms,
            "strategy": "lazy",
            "threshold": threshold
        }

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "accuracy": None,
            "nodes_visited": 0,
            "latency_ms": 0
        }

def main():
    """
    Main entry point to run the Lazy strategy on the LoCoMo benchmark.
    """
    # Configuration
    dataset_name = "locomo/locomo-benchmark"
    split = "test"
    threshold = DEFAULT_THRESHOLD
    output_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    output_file = output_dir / "lazy_results.csv"
    timeout_seconds = 300

    ensure_output_dirs([output_dir])

    logger.info(f"Starting Lazy Strategy execution with threshold {threshold}")
    
    # Load tasks
    tasks = load_tasks(dataset_name, split)
    
    # Define executor with fixed threshold
    def executor(task_id, context):
        return evaluate_task(task_id, context, threshold=threshold)

    # Run batch
    run_batch(
        tasks=tasks,
        executor=executor,
        output_path=str(output_file),
        timeout_seconds=timeout_seconds
    )

    logger.info(f"Lazy strategy execution complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()
