"""
Runner for the Greedy traversal strategy on LoCoMo benchmark tasks.
Executes tasks using the Greedy strategy and logs results to CSV.
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
from strategies.greedy import GreedyTraversal
from graph_utils import build_memory_graph, validate_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default top-k for Greedy strategy (can be overridden)
DEFAULT_TOP_K = 3

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

def evaluate_task(task_id: str, context: Dict[str, Any], top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
    """
    Evaluate a single task using the Greedy traversal strategy.
    
    Args:
        task_id: Unique identifier for the task.
        context: Dictionary containing 'question', 'context', and 'answer'.
        top_k: Number of top edges to select at each step.
    
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

        # Initialize Greedy Traversal
        strategy = GreedyTraversal(top_k=top_k)
        
        # Execute traversal
        start_time = time.time()
        result = strategy.traverse(graph, question)
        elapsed_ms = (time.time() - start_time) * 1000

        # Determine accuracy
        predicted_answer = result.get("answer", "")
        accuracy = (predicted_answer.strip().lower() == ground_truth.strip().lower())

        return {
            "task_id": task_id,
            "status": "success",
            "accuracy": accuracy,
            "nodes_visited": result.get("nodes_visited", 0),
            "latency_ms": elapsed_ms,
            "strategy": "greedy",
            "top_k": top_k
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
    Main entry point to run the Greedy strategy on the LoCoMo benchmark.
    """
    # Configuration
    dataset_name = "locomo/locomo-benchmark"
    split = "test"
    top_k = DEFAULT_TOP_K
    output_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    output_file = output_dir / "greedy_results.csv"
    timeout_seconds = 300

    ensure_output_dirs([output_dir])

    logger.info(f"Starting Greedy Strategy execution with top_k {top_k}")
    
    # Load tasks
    tasks = load_tasks(dataset_name, split)
    
    # Define executor with fixed top_k
    def executor(task_id, context):
        return evaluate_task(task_id, context, top_k=top_k)

    # Run batch
    run_batch(
        tasks=tasks,
        executor=executor,
        output_path=str(output_file),
        timeout_seconds=timeout_seconds
    )

    logger.info(f"Greedy strategy execution complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()