"""
Baseline execution runner for User Story 1.
Executes the 'Full' active reconstruction strategy on LoCoMo benchmark tasks
and logs results to data/processed/baseline_results.csv.
"""
import os
import sys
import time
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from data_loader import fetch_locomo_dataset, ensure_output_dirs
from strategies.full import FullTraversal
from graph_utils import build_memory_graph, validate_graph
from runner import run_task, TimeoutError, save_results_to_csv
from inference import LLMInferenceEngine
from config import get_model_path

logger = logging.getLogger(__name__)

def load_tasks() -> List[Dict[str, Any]]:
    """
    Load tasks from the LoCoMo dataset.
    Returns a list of task dictionaries.
    """
    logger.info("Fetching LoCoMo dataset...")
    try:
        # Fetch the dataset - this will download if not cached
        dataset = fetch_locomo_dataset()
        tasks = []
        for i, item in enumerate(dataset):
            tasks.append({
                "task_id": f"locomo_test_{i}",
                "question": item["question"],
                "context": item["context"],
                "answer": item["answer"]
            })
        logger.info(f"Loaded {len(tasks)} tasks from LoCoMo dataset")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        raise

def evaluate_task(task: Dict[str, Any], timeout: float = 300) -> Dict[str, Any]:
    """
    Evaluate a single task using the Full traversal strategy.
    
    Args:
        task: Task dictionary with question, context, answer.
        timeout: Maximum time in seconds for the task.
        
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms.
    """
    task_id = task["task_id"]
    question = task["question"]
    context = task["context"]
    expected_answer = task["answer"]
    
    logger.info(f"Evaluating task {task_id}...")
    
    try:
        # Build memory graph from context
        graph = build_memory_graph(context)
        
        # Validate graph
        if not validate_graph(graph):
            logger.warning(f"Graph validation failed for task {task_id}, skipping")
            return {
                "task_id": task_id,
                "accuracy": 0.0,
                "nodes_visited": 0,
                "latency_ms": 0.0,
                "status": "invalid_graph"
            }
        
        # Initialize LLM engine
        model_path = get_model_path()
        llm_engine = LLMInferenceEngine(model_path=model_path)
        
        # Initialize Full traversal strategy
        strategy = FullTraversal(llm_engine=llm_engine)
        
        # Execute traversal with timeout
        start_time = time.time()
        
        def run_traversal():
            result = strategy.traverse(graph, question)
            return result
        
        execution_result = run_task(run_traversal, timeout=timeout)
        
        elapsed_time = time.time() - start_time
        
        if execution_result["status"] == "timeout":
            logger.warning(f"Task {task_id} timed out")
            return {
                "task_id": task_id,
                "accuracy": 0.0,
                "nodes_visited": 0,
                "latency_ms": elapsed_time * 1000,
                "status": "timeout"
            }
        
        if execution_result["status"] == "error":
            logger.error(f"Task {task_id} failed: {execution_result['error']}")
            return {
                "task_id": task_id,
                "accuracy": 0.0,
                "nodes_visited": 0,
                "latency_ms": elapsed_time * 1000,
                "status": "error"
            }
        
        # Extract result data
        traversal_result = execution_result["data"]
        predicted_answer = traversal_result.get("answer", "")
        nodes_visited = traversal_result.get("nodes_visited", 0)
        
        # Calculate accuracy (simple string matching for now)
        # In a real scenario, this might use semantic similarity
        accuracy = 1.0 if predicted_answer.strip().lower() == expected_answer.strip().lower() else 0.0
        
        logger.info(f"Task {task_id} completed: accuracy={accuracy}, nodes_visited={nodes_visited}")
        
        return {
            "task_id": task_id,
            "accuracy": accuracy,
            "nodes_visited": nodes_visited,
            "latency_ms": elapsed_time * 1000,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in task {task_id}: {e}")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": 0.0,
            "status": "error",
            "error": str(e)
        }

def main():
    """
    Main entry point for baseline execution.
    Runs all tasks and saves results to data/processed/baseline_results.csv.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting baseline execution runner...")
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    # Load tasks
    tasks = load_tasks()
    
    if not tasks:
        logger.warning("No tasks to process")
        return
    
    # Evaluate tasks
    results = []
    for task in tasks:
        result = evaluate_task(task, timeout=300)
        results.append(result)
    
    # Save results to CSV
    output_path = "data/processed/baseline_results.csv"
    columns = ["task_id", "accuracy", "nodes_visited", "latency_ms"]
    
    # Filter results to only include successful ones for CSV
    successful_results = [r for r in results if r.get("status") == "success"]
    
    # Write to CSV using the runner's save function
    save_results_to_csv(successful_results, output_path, columns)
    
    # Also write a summary of all results (including failed)
    summary_path = "data/processed/baseline_execution_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_tasks": len(tasks),
            "successful": len(successful_results),
            "failed": len(tasks) - len(successful_results),
            "results": results
        }, f, indent=2)
    
    logger.info(f"Baseline execution completed. Results saved to {output_path}")
    logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    main()
