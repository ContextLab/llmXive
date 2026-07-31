"""
Baseline execution runner for User Story 1.
Executes the 'Full' active reconstruction strategy on LoCoMo tasks
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

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from runner import run_batch, TimeoutError, save_results_to_csv
from strategies.full import FullTraversal
from data_loader import load_noisy_graphs
from config import get_model_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = project_root / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "baseline_results.csv"

def ensure_output_dirs():
    """Create output directories if they don't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks(num_tasks: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load tasks from the raw LoCoMo dataset.
    If num_tasks is provided, only load that many tasks.
    """
    raw_data_path = project_root / "data" / "raw" / "locomo.csv"
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw LoCoMo data not found at {raw_data_path}. "
                                "Please run data_loader.py --download first.")

    tasks = []
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if num_tasks is not None and i >= num_tasks:
                break
            tasks.append({
                'task_id': row.get('task_id', f'task_{i}'),
                'question': row.get('question', ''),
                'context': row.get('context', ''),
                'answer': row.get('answer', '')
            })
    
    if not tasks:
        raise ValueError("No tasks loaded from LoCoMo dataset.")
    
    logger.info(f"Loaded {len(tasks)} tasks from {raw_data_path}")
    return tasks

def evaluate_task(task: Dict[str, Any], graph: Optional[Any] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Evaluate a single task using the FullTraversal strategy.
    
    Args:
        task: Dictionary containing task_id, question, context, answer
        graph: Optional memory graph (if None, builds from context)
        timeout: Timeout in seconds for the task execution
    
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms, status
    """
    task_id = task['task_id']
    question = task['question']
    context = task['context']
    ground_truth = task['answer']
    
    result = {
        'task_id': task_id,
        'accuracy': 0.0,
        'nodes_visited': 0,
        'latency_ms': 0.0,
        'status': 'unresolved'
    }
    
    try:
        # Initialize the FullTraversal strategy
        strategy = FullTraversal()
        
        # Start timing
        start_time = time.time()
        
        # Execute the strategy with timeout
        try:
            # Build or use provided graph
            if graph is None:
                # If no graph provided, the strategy might build one internally
                # or we need to handle this case
                logger.warning(f"No graph provided for task {task_id}. Attempting to build from context.")
                # For now, pass context as part of task info
                strategy_result = strategy.run(task, timeout=timeout)
            else:
                strategy_result = strategy.run(task, graph=graph, timeout=timeout)
            
            # End timing
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Extract results
            result['latency_ms'] = round(latency_ms, 2)
            result['nodes_visited'] = strategy_result.get('nodes_visited', 0)
            result['status'] = strategy_result.get('status', 'completed')
            
            # Calculate accuracy (exact string match)
            predicted_answer = strategy_result.get('answer', '')
            if ground_truth.strip().lower() == predicted_answer.strip().lower():
                result['accuracy'] = 1.0
            else:
                result['accuracy'] = 0.0
                
            logger.info(f"Task {task_id} completed: accuracy={result['accuracy']}, "
                        f"nodes={result['nodes_visited']}, latency={result['latency_ms']:.2f}ms")
            
        except TimeoutError:
            end_time = time.time()
            result['latency_ms'] = round((end_time - start_time) * 1000, 2)
            result['status'] = 'timeout'
            logger.warning(f"Task {task_id} timed out after {timeout}s")
            
        except Exception as e:
            end_time = time.time()
            result['latency_ms'] = round((end_time - start_time) * 1000, 2)
            result['status'] = 'degenerate' if 'degenerate' in str(e).lower() else 'unresolved'
            logger.error(f"Task {task_id} failed with error: {e}")
            
    except Exception as e:
        logger.error(f"Critical error evaluating task {task_id}: {e}")
        result['status'] = 'unresolved'
    
    return result

def main(num_tasks: Optional[int] = None, timeout: int = 30):
    """
    Main entry point for baseline execution.
    
    Args:
        num_tasks: Number of tasks to process (None for all)
        timeout: Timeout in seconds per task
    """
    ensure_output_dirs()
    
    # Load tasks
    tasks = load_tasks(num_tasks)
    
    # Load memory graph if available (for consistency with noisy baseline)
    # For clean baseline, we might build graphs from context or use a default
    graph = None
    graph_path = project_root / "data" / "processed" / "graphs" / "graph_noise_42.json"
    if graph_path.exists():
        logger.info(f"Loading memory graph from {graph_path}")
        try:
            graph = load_noisy_graphs(str(graph_path))
        except Exception as e:
            logger.warning(f"Failed to load graph: {e}. Proceeding without graph.")
            graph = None
    
    # Run batch evaluation
    results = run_batch(
        tasks=tasks,
        evaluate_func=evaluate_task,
        timeout=timeout,
        graph=graph
    )
    
    # Save results to CSV
    if results:
        save_results_to_csv(results, str(OUTPUT_FILE))
        logger.info(f"Saved {len(results)} results to {OUTPUT_FILE}")
    else:
        logger.warning("No results to save.")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run baseline evaluation on LoCoMo tasks")
    parser.add_argument("--num-tasks", type=int, default=None, help="Number of tasks to process")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds per task")
    args = parser.parse_args()
    
    main(num_tasks=args.num_tasks, timeout=args.timeout)
