"""
Lazy Execution Runner for the LLMXive follow-up project.

This script implements the execution runner for the Lazy traversal strategy.
It loads tasks from the raw LoCoMo dataset, builds memory graphs, applies
the Lazy traversal strategy, and logs results to a CSV file.

Output: data/processed/lazy_results.csv
"""

import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.lazy import run_lazy_strategy
from data_loader import load_graphs, ensure_output_dirs
from runner import timeout_context, TaskResult, TimeoutError
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dirs(output_path: str) -> Path:
    """Ensure the directory for the output file exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison."""
    if not answer:
        return ""
    return answer.lower().strip().replace(".", "").replace(",", "").replace("!", "").replace("?", "")

def load_tasks(graph_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph file.
    
    Args:
        graph_path: Path to the JSON file containing graphs and tasks.
        
    Returns:
        List of task dictionaries with task_id, question, context, answer, and graph.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file not found: {graph_path}")
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tasks = []
    for task_id, graph_data in data.items():
        # Extract task info from graph_data
        # The graph_data should contain 'question', 'context', 'answer' and the graph structure
        task = {
            'task_id': task_id,
            'question': graph_data.get('question', ''),
            'context': graph_data.get('context', ''),
            'answer': graph_data.get('answer', ''),
            'graph': graph_data.get('graph', {})  # The graph structure
        }
        tasks.append(task)
    
    if not tasks:
        logger.warning(f"No tasks found in {graph_path}")
    
    return tasks

def evaluate_task(task: Dict[str, Any], strategy_params: Dict[str, Any], timeout_seconds: int = 30) -> TaskResult:
    """
    Evaluate a single task using the Lazy traversal strategy.
    
    Args:
        task: Task dictionary with question, context, answer, and graph.
        strategy_params: Parameters for the Lazy strategy (e.g., threshold).
        timeout_seconds: Maximum time allowed for task execution.
        
    Returns:
        TaskResult object with accuracy, nodes_visited, latency_ms, and status.
    """
    start_time = time.time()
    task_id = task['task_id']
    
    try:
        with timeout_context(timeout_seconds):
            # Run the Lazy strategy
            result = run_lazy_strategy(
                graph=task['graph'],
                question=task['question'],
                context=task['context'],
                **strategy_params
            )
            
            # Calculate accuracy
            predicted_answer = result.get('predicted_answer', '')
            actual_answer = task['answer']
            
            # Normalize answers for comparison
            pred_normalized = normalize_answer(predicted_answer)
            actual_normalized = normalize_answer(actual_answer)
            
            accuracy = 1.0 if pred_normalized == actual_normalized else 0.0
            
            # Extract metrics
            nodes_visited = result.get('nodes_visited', 0)
            status = "COMPLETED"
            
    except TimeoutError:
        accuracy = 0.0
        nodes_visited = 0
        status = "TIMEOUT"
        logger.warning(f"Task {task_id} timed out")
    except Exception as e:
        accuracy = 0.0
        nodes_visited = 0
        status = "ERROR"
        logger.error(f"Task {task_id} failed with error: {str(e)}")
        raise
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    return TaskResult(
        task_id=task_id,
        accuracy=accuracy,
        nodes_visited=nodes_visited,
        latency_ms=latency_ms,
        status=status
    )

def save_results_to_csv(results: List[TaskResult], output_path: str):
    """
    Save results to a CSV file.
    
    Args:
        results: List of TaskResult objects.
        output_path: Path to the output CSV file.
    """
    ensure_output_dirs(output_path)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status'])
        
        for result in results:
            writer.writerow([
                result.task_id,
                result.accuracy,
                result.nodes_visited,
                result.latency_ms,
                result.status
            ])

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """Save results to a CSV file."""
    if not results:
        logger.warning("No results to save.")
        return
    
    fieldnames = [
        'task_id', 'accuracy', 'nodes_visited', 'latency_ms', 
        'status', 'token_count', 'evidence_threshold'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for the Lazy execution runner."""
    parser = argparse.ArgumentParser(description='Lazy Execution Runner for LLMXive')
    parser.add_argument('--input', type=str, required=True, help='Path to the graph JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to the output CSV file')
    parser.add_argument('--threshold', type=float, default=0.7, help='Evidence threshold for Lazy strategy')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout per task in seconds')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    logger.info(f"Starting Lazy execution runner")
    logger.info(f"Input graph: {args.input}")
    logger.info(f"Output results: {args.output}")
    logger.info(f"Threshold: {args.threshold}")
    logger.info(f"Timeout: {args.timeout}s")
    
    # Load tasks
    try:
        tasks = load_tasks(args.input)
        logger.info(f"Loaded {len(tasks)} tasks")
    except Exception as e:
        logger.error(f"Failed to load tasks: {str(e)}")
        sys.exit(1)
    
    # Strategy parameters
    strategy_params = {
        'threshold': args.threshold
    }
    
    # Evaluate tasks
    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Evaluating task {i+1}/{len(tasks)}: {task['task_id']}")
        try:
            result = evaluate_task(task, strategy_params, args.timeout)
            results.append(result)
            logger.info(f"  Accuracy: {result.accuracy}, Nodes: {result.nodes_visited}, Status: {result.status}")
        except Exception as e:
            logger.error(f"Failed to evaluate task {task['task_id']}: {str(e)}")
            # Continue with next task
            continue
    
    # Save results
    save_results_to_csv(results, args.output)
    logger.info(f"Saved {len(results)} results to {args.output}")
    
    # Summary
    completed = sum(1 for r in results if r.status == "COMPLETED")
    timeout = sum(1 for r in results if r.status == "TIMEOUT")
    error = sum(1 for r in results if r.status == "ERROR")
    
    logger.info(f"Summary: {completed} completed, {timeout} timeout, {error} errors")
    
    if completed > 0:
        avg_accuracy = sum(r.accuracy for r in results if r.status == "COMPLETED") / completed
        avg_nodes = sum(r.nodes_visited for r in results if r.status == "COMPLETED") / completed
        logger.info(f"Average accuracy (completed): {avg_accuracy:.4f}")
        logger.info(f"Average nodes visited (completed): {avg_nodes:.2f}")

if __name__ == "__main__":
    main()