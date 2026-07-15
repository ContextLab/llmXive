"""
Baseline execution runner for the 'Full' active reconstruction strategy.
Executes tasks from the LoCoMo benchmark using the FullTraversal strategy
and logs results to data/processed/baseline_results.csv.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from data_loader import fetch_locomo_dataset, save_raw_data, ensure_output_dirs
from graph_utils import build_memory_graph, validate_graph
from strategies.full import FullTraversal
from runner import run_batch, TimeoutHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path("data/processed")
RESULTS_FILE = OUTPUT_DIR / "baseline_results.csv"
DATASET_NAME = "locomo/locomo-benchmark"
DATASET_SPLIT = "test"
TIMEOUT_SECONDS = 300

def evaluate_task(task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single LoCoMo task using the Full traversal strategy.
    
    Args:
        task_id: Unique identifier for the task.
        context: Dictionary containing 'question', 'context', 'answer', and graph data.
    
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms.
    """
    start_time = time.time()
    
    try:
        # Extract task components
        question = context.get("question", "")
        context_text = context.get("context", "")
        ground_truth = context.get("answer", "")
        
        # Build memory graph from context
        # Note: graph_utils.build_memory_graph expects specific input format.
        # Assuming it takes the text context and constructs the graph.
        graph = build_memory_graph(context_text)
        
        if not validate_graph(graph):
            logger.warning(f"Task {task_id}: Graph validation failed. Skipping.")
            return {
                "task_id": task_id,
                "accuracy": 0.0,
                "nodes_visited": 0,
                "latency_ms": (time.time() - start_time) * 1000,
                "status": "graph_invalid"
            }
        
        # Initialize the Full Traversal strategy
        strategy = FullTraversal()
        
        # Execute the strategy
        # The strategy should return a result containing the answer and traversal stats
        result = strategy.execute(graph, question)
        
        # Determine accuracy (simple string match or semantic similarity)
        # For this implementation, we assume the strategy returns a 'predicted_answer'
        predicted_answer = result.get("predicted_answer", "")
        
        # Simple evaluation: exact match or contains key entities
        # In a real scenario, use a more robust metric (e.g., BLEU, ROUGE, or LLM-based judge)
        accuracy = 1.0 if predicted_answer.lower() == ground_truth.lower() else 0.0
        
        # Fallback: if the strategy returns a confidence score or partial match logic
        # For now, we rely on the strategy's internal logic to provide the answer.
        # If the strategy returns 'success' and the answer is close enough, we count it.
        if result.get("success", False) and not accuracy:
            # Heuristic check: if the predicted answer contains the ground truth
            if ground_truth.lower() in predicted_answer.lower():
                accuracy = 0.5 # Partial credit
            else:
                accuracy = 0.0
        
        nodes_visited = result.get("nodes_visited", 0)
        
        return {
            "task_id": task_id,
            "accuracy": accuracy,
            "nodes_visited": nodes_visited,
            "latency_ms": (time.time() - start_time) * 1000,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": (time.time() - start_time) * 1000,
            "status": "error",
            "error": str(e)
        }

def load_tasks() -> List[Dict[str, Any]]:
    """
    Load tasks from the LoCoMo dataset.
    
    Returns:
        List of task dictionaries with 'id', 'context' (question, context, answer).
    """
    logger.info(f"Loading dataset {DATASET_NAME} (split: {DATASET_SPLIT})...")
    
    # Ensure output directories exist for raw data
    ensure_output_dirs()
    
    try:
        # Fetch the dataset (this function is expected to download and cache the data)
        dataset = fetch_locomo_dataset(DATASET_NAME, split=DATASET_SPLIT)
        
        tasks = []
        for i, item in enumerate(dataset):
            task = {
                "id": f"locoma_test_{i}",
                "context": {
                    "question": item.get("question", ""),
                    "context": item.get("context", ""),
                    "answer": item.get("answer", "")
                }
            }
            tasks.append(task)
        
        logger.info(f"Loaded {len(tasks)} tasks.")
        return tasks
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def main():
    """Main entry point for the baseline execution runner."""
    logger.info("Starting Baseline Execution Runner (Full Strategy)")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load tasks
    tasks = load_tasks()
    
    if not tasks:
        logger.warning("No tasks loaded. Exiting.")
        return
    
    # Define the executor function
    executor_func = evaluate_task
    
    # Run the batch
    output_path = str(RESULTS_FILE)
    logger.info(f"Executing {len(tasks)} tasks with timeout={TIMEOUT_SECONDS}s...")
    
    run_batch(
        tasks=tasks,
        executor=executor_func,
        output_path=output_path,
        timeout_seconds=TIMEOUT_SECONDS
    )
    
    logger.info(f"Baseline execution complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()