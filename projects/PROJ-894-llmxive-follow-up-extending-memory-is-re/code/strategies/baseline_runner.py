"""
Baseline Execution Runner for User Story 1.

Executes the "Full" active reconstruction strategy on LoCoMo benchmark tasks.
Logs task_id, accuracy, nodes_visited, latency_ms, and status to a CSV file.
Handles degenerate/unresolved states as specified in T006/T037.
"""
import os
import sys
import time
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports based on API surface
from data_loader import load_raw_data, load_graphs
from strategies.full import run_full_strategy
from runner import TimeoutHandler, TimeoutError
from graph_utils import validate_graph, get_graph_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = "data/raw/locomo.csv"
GRAPHS_PATH = "data/intermediate/graphs_raw.json"
OUTPUT_PATH = "data/processed/baseline_results.csv"
TIMEOUT_SECONDS = 60  # Default timeout per task

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def load_tasks() -> List[Dict[str, Any]]:
    """Load raw LoCoMo tasks from CSV."""
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    return load_raw_data(RAW_DATA_PATH)

def evaluate_task(
    task: Dict[str, Any], 
    graph: Dict[str, List[Dict[str, Any]]], 
    timeout: int = TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Evaluate a single task using the Full Active Reconstruction Strategy.
    
    Args:
        task: Dictionary containing 'task_id', 'question', 'context', 'answer'
        graph: Dictionary mapping task_id to list of edges
        timeout: Maximum seconds allowed for execution
        
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms, status
    """
    task_id = task.get('task_id', task.get('id', 'unknown'))
    question = task.get('question', '')
    ground_truth = normalize_answer(task.get('answer', ''))
    
    result = {
        'task_id': task_id,
        'accuracy': None,
        'nodes_visited': 0,
        'latency_ms': 0.0,
        'status': 'UNRESOLVED'
    }

    # Check if graph exists for this task
    task_graph_edges = graph.get(task_id, [])
    
    # Degenerate Graph Handling (T037)
    if not task_graph_edges:
        logger.warning(f"Task {task_id}: No edges found in graph. Status: DEGENERATE")
        result['status'] = 'DEGENERATE'
        return result

    # Validate graph structure
    try:
        is_valid, stats = validate_graph(task_graph_edges)
        if not is_valid:
            logger.warning(f"Task {task_id}: Invalid graph structure. Status: DEGENERATE")
            result['status'] = 'DEGENERATE'
            return result
    except Exception as e:
        logger.error(f"Task {task_id}: Graph validation failed: {e}")
        result['status'] = 'ERROR'
        return result

    # Run the Full Strategy with timeout
    start_time = time.time()
    try:
        with TimeoutHandler(seconds=timeout):
            # Run the traversal strategy
            # Expected return from run_full_strategy: 
            # {'nodes_visited': int, 'visited_nodes': list, 'success': bool, 'answer': str, ...}
            strategy_result = run_full_strategy(
                question=question,
                edges=task_graph_edges,
                ground_truth=ground_truth
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000.0
            
            # Extract metrics
            nodes_visited = strategy_result.get('nodes_visited', 0)
            success = strategy_result.get('success', False)
            predicted_answer = strategy_result.get('answer', '')
            
            # Calculate accuracy (binary match for now, or partial if needed)
            # Assuming strict match for baseline
            is_correct = normalize_answer(predicted_answer) == ground_truth if ground_truth else False
            accuracy = 1.0 if is_correct else 0.0
            
            result['accuracy'] = accuracy
            result['nodes_visited'] = nodes_visited
            result['latency_ms'] = latency_ms
            result['status'] = 'COMPLETED' if success else 'UNRESOLVED'
            
    except TimeoutError:
        end_time = time.time()
        result['latency_ms'] = (end_time - start_time) * 1000.0
        result['status'] = 'TIMEOUT'
        logger.warning(f"Task {task_id}: Execution timed out.")
    except Exception as e:
        end_time = time.time()
        result['latency_ms'] = (end_time - start_time) * 1000.0
        result['status'] = 'ERROR'
        logger.error(f"Task {task_id}: Execution failed with error: {e}")

    return result

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """Save results to a CSV file."""
    if not results:
        logger.warning("No results to save.")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the baseline runner."""
    logger.info("Starting Baseline Execution Runner...")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Load tasks
    try:
        tasks = load_tasks()
        logger.info(f"Loaded {len(tasks)} tasks from {RAW_DATA_PATH}")
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)

    # Load graphs
    if not os.path.exists(GRAPHS_PATH):
        logger.error(f"Graph file not found: {GRAPHS_PATH}. Run T011a-1 first.")
        sys.exit(1)
    
    try:
        with open(GRAPHS_PATH, 'r', encoding='utf-8') as f:
            graphs = json.load(f)
        logger.info(f"Loaded graphs for {len(graphs)} tasks from {GRAPHS_PATH}")
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        sys.exit(1)

    # Process tasks
    results = []
    total = len(tasks)
    
    for i, task in enumerate(tasks):
        task_id = task.get('task_id', task.get('id', 'unknown'))
        logger.info(f"Processing task {i+1}/{total}: {task_id}")
        
        result = evaluate_task(task, graphs)
        results.append(result)
        
        # Log intermediate status
        logger.info(f"  -> Status: {result['status']}, Accuracy: {result['accuracy']}, Nodes: {result['nodes_visited']}")

    # Save results
    save_results_to_csv(results, OUTPUT_PATH)
    
    # Summary
    completed = sum(1 for r in results if r['status'] == 'COMPLETED')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    degenerate = sum(1 for r in results if r['status'] == 'DEGENERATE')
    unresolved = sum(1 for r in results if r['status'] == 'UNRESOLVED')
    
    logger.info(f"Baseline Execution Complete. Total: {total}, Completed: {completed}, "
                f"Timeout: {timeout}, Degenerate: {degenerate}, Unresolved: {unresolved}")
    
    return results

if __name__ == "__main__":
    main()