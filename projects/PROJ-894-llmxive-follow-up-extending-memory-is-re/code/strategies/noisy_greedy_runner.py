import os
import sys
import time
import logging
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from strategies.greedy import GreedyTraversal
from data_loader import load_noisy_graphs
from runner import run_batch, save_results_to_csv, TimeoutError
from config import get_model_path
import networkx as nx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output paths per task specification
OUTPUT_DIR = Path("data/processed")
RESULTS_FILE = OUTPUT_DIR / "noisy_greedy_results.csv"
GRAPHS_FILE = Path("data/processed/graphs/graph_noise_42.json")

def ensure_output_dirs():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks(graph_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load tasks and their associated noisy memory graphs.
    
    This function loads the synthetic noisy graph dataset generated in T011
    (graph_noise_42.json) and pairs it with the LoCoMo benchmark tasks.
    
    Returns:
        List of task dictionaries with 'graph' key attached.
    """
    if graph_path is None:
        graph_path = GRAPHS_FILE
    
    if not graph_path.exists():
        raise FileNotFoundError(
            f"Noisy graph file not found at {graph_path}. "
            "Run T011 (data_loader.py --generate-graphs) first."
        )

    # Load the noisy graph
    logger.info(f"Loading noisy graph from {graph_path}")
    noisy_graph = load_noisy_graphs(graph_path)
    
    if not isinstance(noisy_graph, nx.DiGraph):
        if isinstance(noisy_graph, dict) and 'graph' in noisy_graph:
            noisy_graph = noisy_graph['graph']
        else:
            raise ValueError(f"Invalid noisy graph format loaded from {graph_path}")

    # Load the raw tasks
    raw_tasks_path = Path("data/processed/raw_tasks.json")
    tasks = []
    
    if raw_tasks_path.exists():
        logger.info(f"Loading tasks from {raw_tasks_path}")
        with open(raw_tasks_path, 'r') as f:
            tasks = json.load(f)
    else:
        logger.warning(f"Raw tasks file not found at {raw_tasks_path}. Fetching a small subset.")
        from data_loader import fetch_locomo_dataset
        tasks = fetch_locomo_dataset(subset=10)

    # Attach the noisy graph to each task
    for task in tasks:
        task['memory_graph'] = noisy_graph
    
    logger.info(f"Loaded {len(tasks)} tasks with noisy graph attached.")
    return tasks

def evaluate_task(task: Dict[str, Any], strategy: GreedyTraversal) -> Dict[str, Any]:
    """
    Evaluate a single task using the Greedy strategy on the noisy graph.
    
    Args:
        task: Dictionary containing task details and memory_graph.
        strategy: The GreedyTraversal instance to use.
        
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms.
    """
    task_id = task.get('task_id', f"task_{hash(str(task)) % 10000}")
    question = task.get('question', '')
    expected_answer = task.get('answer', '')
    memory_graph = task.get('memory_graph')
    
    if memory_graph is None:
        logger.error(f"Task {task_id} has no memory graph attached.")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': 0.0,
            'error': 'Missing memory graph'
        }

    start_time = time.time()
    
    try:
        result = None
        if hasattr(strategy, 'run'):
            result = strategy.run(memory_graph, question)
        elif hasattr(strategy, 'traverse'):
            result = strategy.traverse(memory_graph, question)
        else:
            raise AttributeError("Strategy has no 'run' or 'traverse' method.")
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        actual_answer = result.get('answer', '') if isinstance(result, dict) else str(result)
        accuracy = 0.0
        if expected_answer and actual_answer:
            if expected_answer.lower() in actual_answer.lower():
                accuracy = 1.0
            else:
                expected_words = set(expected_answer.lower().split())
                actual_words = set(actual_answer.lower().split())
                if expected_words & actual_words:
                    accuracy = 0.5
        
        nodes_visited = result.get('nodes_visited', 0) if isinstance(result, dict) else 0
        
        return {
            'task_id': task_id,
            'accuracy': accuracy,
            'nodes_visited': nodes_visited,
            'latency_ms': latency_ms
        }
        
    except TimeoutError as e:
        logger.warning(f"Task {task_id} timed out.")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': (time.time() - start_time) * 1000,
            'error': 'Timeout'
        }
    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}", exc_info=True)
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': (time.time() - start_time) * 1000,
            'error': str(e)
        }

def main():
    """
    Main entry point for the noisy greedy execution runner.
    Runs the Greedy strategy on the noisy graph dataset and saves results.
    """
    ensure_output_dirs()
    
    model_path = get_model_path()
    logger.info(f"Using model path: {model_path}")
    
    strategy = GreedyTraversal()
    
    tasks = load_tasks()
    
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        sys.exit(1)
    
    logger.info(f"Starting evaluation of {len(tasks)} tasks with Greedy strategy on noisy graph.")
    
    results = run_batch(
        tasks=tasks,
        evaluate_func=lambda t: evaluate_task(t, strategy),
        chunk_size=10,
        timeout_per_task=300
    )
    
    save_results_to_csv(results, RESULTS_FILE)
    logger.info(f"Results saved to {RESULTS_FILE}")
    
    total_tasks = len(results)
    successful = sum(1 for r in results if r.get('error') is None)
    avg_accuracy = sum(r['accuracy'] for r in results) / total_tasks if total_tasks > 0 else 0.0
    avg_latency = sum(r['latency_ms'] for r in results) / total_tasks if total_tasks > 0 else 0.0
    
    logger.info(f"Completed: {successful}/{total_tasks} tasks. Avg Accuracy: {avg_accuracy:.4f}, Avg Latency: {avg_latency:.2f}ms")

if __name__ == "__main__":
    main()