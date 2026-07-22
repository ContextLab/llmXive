"""
Baseline runner for executing the 'Full' active reconstruction strategy on LoCoMo tasks.
Uses the FullTraversal strategy to process tasks and logs results to CSV.
"""
import os
import sys
import time
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.full import FullTraversal
from inference import LLMInferenceEngine
from config import get_model_path
from data_loader import fetch_locomo_dataset, save_raw_data
from graph_utils import build_memory_graph, validate_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_tasks() -> List[Dict[str, Any]]:
    """
    Load tasks from the LoCoMo benchmark dataset.
    Fetches the 'test' split and returns a list of task dictionaries.
    """
    logger.info("Loading LoCoMo benchmark tasks...")
    try:
        # Fetch the dataset
        dataset = fetch_locomo_dataset(split="test")
        
        tasks = []
        for idx, item in enumerate(dataset):
            task = {
                "id": f"locomo_test_{idx}",
                "context": {
                    "question": item["question"],
                    "context": item["context"],
                    "answer": item["answer"]
                }
            }
            tasks.append(task)
        
        logger.info(f"Loaded {len(tasks)} tasks from LoCoMo benchmark")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        raise

def evaluate_task(task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single task using the FullTraversal strategy.
    
    Args:
        task_id: Unique identifier for the task.
        context: Dictionary containing 'question', 'context', and 'answer'.
    
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, and latency_ms.
    """
    start_time = time.time()
    
    try:
        # Initialize the LLM engine
        model_path = get_model_path()
        engine = LLMInferenceEngine(model_path=model_path)
        
        # Build the memory graph from context
        graph = build_memory_graph(context["context"])
        
        # Validate the graph
        if not validate_graph(graph):
            logger.warning(f"Graph for task {task_id} is invalid, skipping")
            return {
                "task_id": task_id,
                "accuracy": 0.0,
                "nodes_visited": 0,
                "latency_ms": 0,
                "status": "invalid_graph"
            }
        
        # Initialize the FullTraversal strategy
        strategy = FullTraversal(engine=engine)
        
        # Execute the traversal
        result = strategy.traverse(
            graph=graph,
            question=context["question"],
            target_answer=context["answer"]
        )
        
        # Calculate accuracy (simple string matching for now)
        # In a real scenario, this might use semantic similarity
        predicted_answer = result.get("predicted_answer", "")
        expected_answer = context["answer"]
        
        # Simple accuracy check (exact match or substring)
        is_correct = (predicted_answer.lower().strip() == expected_answer.lower().strip() or 
                     expected_answer.lower().strip() in predicted_answer.lower())
        accuracy = 1.0 if is_correct else 0.0
        
        # Get nodes visited count
        nodes_visited = result.get("nodes_visited", 0)
        
        elapsed = time.time() - start_time
        
        return {
            "task_id": task_id,
            "accuracy": accuracy,
            "nodes_visited": nodes_visited,
            "latency_ms": elapsed * 1000,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}")
        elapsed = time.time() - start_time
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": elapsed * 1000,
            "status": "error",
            "error": str(e)
        }

def main():
    """
    Main entry point for the baseline execution runner.
    Loads tasks, evaluates them, and writes results to CSV.
    """
    logger.info("Starting baseline execution runner...")
    
    # Define output path
    output_path = Path("data/processed/baseline_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load tasks
    tasks = load_tasks()
    
    # Evaluate each task
    results = []
    for task in tasks:
        logger.info(f"Evaluating task {task['id']}")
        result = evaluate_task(task["id"], task["context"])
        results.append(result)
    
    # Write results to CSV
    if results:
        fieldnames = ["task_id", "accuracy", "nodes_visited", "latency_ms", "status"]
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Results written to {output_path}")
        logger.info(f"Total tasks processed: {len(results)}")
    else:
        logger.warning("No results to write")
    
    logger.info("Baseline execution runner completed")

if __name__ == "__main__":
    main()
