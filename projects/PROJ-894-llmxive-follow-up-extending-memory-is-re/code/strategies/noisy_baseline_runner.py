"""
Noisy Baseline Execution Runner for T013b.

Executes the 'full' active reconstruction strategy on the synthetic noisy graphs
(data/processed/graphs/graph_noise_42.json) generated in T011c.

Logs results to: data/processed/noisy_baseline_results.csv
Columns: task_id, accuracy, nodes_visited, latency_ms, status
Status Values: COMPLETED, TIMEOUT, DEGENERATE, UNRESOLVED
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

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.full import run_full_strategy
from data_loader import load_noisy_graphs, stream_locomo_tasks
from graph_utils import validate_graph, get_graph_statistics
from runner import TimeoutHandler, TimeoutError, ensure_output_dirs
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the noisy graph dataset.
    Since we are running on noisy graphs, we need to pair the task data
    with the noisy graph structure.
    """
    # We use the streaming iterator to get tasks, but we need to load the noisy graphs
    # The runner expects tasks to have 'question', 'context', 'answer', and 'task_id'
    # The graph structure is loaded separately and passed to the strategy.
    
    tasks = []
    # Using the streaming iterator from T050 to avoid loading full dataset into memory
    # We assume the raw data was already processed into graphs, so we just need the task metadata.
    # However, T011a-1b produces graphs_raw.json. T011c produces graph_noise_42.json.
    # We need to map task_id -> noisy_graph.
    
    # Let's load the noisy graphs first
    noisy_graphs = load_noisy_graphs()
    
    if not noisy_graphs:
        logger.error("No noisy graphs found. Ensure T011c has run successfully.")
        return []

    # We need to iterate over the original tasks to get the questions/answers
    # The noisy graphs are keyed by task_id.
    # We will use the streaming iterator to fetch task metadata (question, answer)
    # and match it with the pre-loaded noisy graph.
    
    for task in stream_locomo_tasks(chunk_size=100):
        task_id = task.get('task_id')
        if not task_id:
            logger.warning(f"Task missing task_id, skipping: {task}")
            continue
        
        if task_id in noisy_graphs:
            task['graph'] = noisy_graphs[task_id]
            tasks.append(task)
        else:
            logger.warning(f"Noisy graph missing for task_id: {task_id}. Skipping.")
    
    return tasks

def evaluate_task(task: Dict[str, Any], strategy_name: str = "full") -> Dict[str, Any]:
    """
    Evaluate a single task using the specified strategy on its noisy graph.
    
    Returns a result dictionary with:
    - task_id
    - accuracy (0.0 or 1.0 based on answer match)
    - nodes_visited (count)
    - latency_ms (float)
    - status (COMPLETED, TIMEOUT, DEGENERATE, UNRESOLVED)
    """
    task_id = task.get('task_id', 'unknown')
    graph = task.get('graph')
    question = task.get('question', '')
    expected_answer = task.get('answer', '')
    
    result = {
        'task_id': task_id,
        'accuracy': None,
        'nodes_visited': 0,
        'latency_ms': 0.0,
        'status': 'UNRESOLVED'
    }

    if not graph:
        logger.error(f"Task {task_id} has no graph data.")
        return result

    # Validate graph
    is_valid, stats = validate_graph(graph)
    if not is_valid:
        logger.warning(f"Task {task_id} has invalid graph: {stats}")
        result['status'] = 'DEGENERATE'
        return result
    
    # Check for degenerate cases (single node, no edges)
    num_nodes = stats.get('num_nodes', 0)
    num_edges = stats.get('num_edges', 0)
    if num_nodes <= 1 or num_edges == 0:
        logger.info(f"Task {task_id} detected as degenerate (nodes={num_nodes}, edges={num_edges})")
        result['status'] = 'DEGENERATE'
        return result

    start_time = time.time()
    try:
        # Run the full traversal strategy
        # The strategy returns (success, nodes_visited, execution_time, reconstructed_answer)
        success, nodes_visited, execution_time, reconstructed_answer = run_full_strategy(
            graph, 
            question, 
            timeout=30  # Default timeout per task
        )
        
        result['nodes_visited'] = nodes_visited
        result['latency_ms'] = execution_time * 1000.0
        
        if success:
            # Check accuracy
            pred_norm = normalize_answer(reconstructed_answer)
            expected_norm = normalize_answer(expected_answer)
            
            if pred_norm == expected_norm:
                result['accuracy'] = 1.0
            else:
                result['accuracy'] = 0.0
            
            result['status'] = 'COMPLETED'
        else:
            # If strategy returned False but didn't timeout, it might be unresolved
            result['status'] = 'UNRESOLVED'
            
    except TimeoutError as e:
        logger.warning(f"Task {task_id} timed out.")
        result['status'] = 'TIMEOUT'
        result['latency_ms'] = 30000.0 # Record timeout duration
    except Exception as e:
        logger.error(f"Task {task_id} failed with exception: {e}", exc_info=True)
        result['status'] = 'UNRESOLVED'

    return result

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """Save results to CSV file."""
    ensure_output_dirs(output_path)
    
    fieldnames = ['task_id', 'accuracy', 'nodes_visited', 'latency_ms', 'status']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            # Ensure all fields are present
            row = {k: res.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run noisy baseline execution.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/graphs/graph_noise_42.json",
        help="Path to the noisy graph dataset (JSON)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/noisy_baseline_results.csv",
        help="Path to the output CSV file"
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=None,
        help="Optional: limit execution to first N tasks"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting Noisy Baseline Runner. Input: {args.input}, Output: {args.output}")
    
    # Load tasks and graphs
    tasks = load_tasks(args.input)
    
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(tasks)} tasks.")
    
    if args.subset:
        tasks = tasks[:args.subset]
        logger.info(f"Limiting to {args.subset} tasks.")
    
    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id')}")
        res = evaluate_task(task)
        results.append(res)
        
        # Log summary for each task
        logger.info(f"  -> Status: {res['status']}, Acc: {res['accuracy']}, Nodes: {res['nodes_visited']}")
    
    # Save results
    save_results_to_csv(results, args.output)
    
    # Summary
    completed = sum(1 for r in results if r['status'] == 'COMPLETED')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    degenerate = sum(1 for r in results if r['status'] == 'DEGENERATE')
    unresolved = sum(1 for r in results if r['status'] == 'UNRESOLVED')
    
    logger.info(f"Execution complete. Total: {len(results)}, Completed: {completed}, Timeout: {timeout}, Degenerate: {degenerate}, Unresolved: {unresolved}")

if __name__ == "__main__":
    main()