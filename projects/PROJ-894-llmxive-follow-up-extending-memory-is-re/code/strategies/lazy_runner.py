"""
Runner for the Lazy Traversal strategy on the LoCoMo benchmark.
Executes tasks and logs results to data/processed/lazy_results.csv.
"""
import os
import sys
import time
import logging
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader import load_noisy_graphs, ensure_output_dirs
from strategies.lazy import LazyTraversal
from inference import LLMInferenceEngine
from config import get_model_path
from runner import run_batch, save_results_to_csv, TimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / "lazy_runner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_tasks(subset: int = 5) -> List[Dict[str, Any]]:
    """
    Load tasks from the LoCoMo dataset.
    Uses the data downloaded by data_loader.py.
    """
    # We rely on the data_loader having populated data/processed/tasks.json
    # or we fetch a small subset directly if the file doesn't exist yet.
    # For robustness in this runner, we attempt to load from the cached JSON.
    tasks_path = project_root / "data" / "processed" / "tasks.json"
    
    if tasks_path.exists():
        with open(tasks_path, 'r') as f:
            tasks = json.load(f)
        logger.info(f"Loaded {len(tasks)} tasks from {tasks_path}")
        return tasks[:subset]
    else:
        logger.warning("tasks.json not found. Attempting to fetch a small subset directly.")
        # Fallback: fetch directly if runner is run before data_loader completes fully
        # This ensures the runner can still function if data_loader was run partially
        from data_loader import fetch_locomo_dataset
        try:
            tasks = fetch_locomo_dataset(subset=subset)
            logger.info(f"Fetched {len(tasks)} tasks directly.")
            return tasks
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            raise RuntimeError("Cannot proceed without real task data.")

def evaluate_task(
    task: Dict[str, Any], 
    graph: Any, 
    strategy: LazyTraversal, 
    engine: LLMInferenceEngine
) -> Dict[str, Any]:
    """
    Evaluate a single task using the Lazy strategy.
    Returns a dictionary with metrics: task_id, accuracy, nodes_visited, latency_ms.
    """
    task_id = task.get('id', 'unknown')
    question = task.get('question', '')
    context = task.get('context', '')
    answer = task.get('answer', '')
    
    start_time = time.time()
    
    try:
        # Run the strategy
        # The strategy expects a graph and the task context
        result = strategy.run(task, graph)
        
        # Determine accuracy (simple string match for now, as per baseline)
        # In a real scenario, this might use an LLM to judge semantic equivalence
        prediction = result.get('prediction', '')
        accuracy = 1.0 if prediction.lower().strip() == answer.lower().strip() else 0.0
        
        nodes_visited = result.get('nodes_visited', 0)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'task_id': task_id,
            'accuracy': accuracy,
            'nodes_visited': nodes_visited,
            'latency_ms': latency_ms,
            'status': 'success'
        }
        
    except TimeoutError as e:
        logger.warning(f"Task {task_id} timed out: {e}")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': (time.time() - start_time) * 1000,
            'status': 'timeout'
        }
    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}", exc_info=True)
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': (time.time() - start_time) * 1000,
            'status': 'error',
            'error': str(e)
        }

def main():
    """
    Main entry point for the Lazy Runner.
    Loads tasks, initializes the strategy and LLM, runs the batch, and saves results.
    """
    logger.info("Starting Lazy Traversal Runner...")
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    # Initialize LLM Engine
    model_path = get_model_path()
    if not model_path:
        logger.warning("No model path configured. Using default from config.")
        # The config will handle the default or raise an error if not set
    
    engine = LLMInferenceEngine(model_path=model_path)
    
    # Initialize Strategy
    strategy = LazyTraversal(engine=engine)
    
    # Load tasks
    try:
        tasks = load_tasks(subset=5) # Default to a small subset for testing
    except Exception as e:
        logger.critical(f"Failed to load tasks: {e}")
        return 1
    
    if not tasks:
        logger.warning("No tasks loaded. Exiting.")
        return 0
    
    # Load graph (if noisy graphs are to be used, this would be different)
    # For T019 (clean), we assume the graph is built from the task context
    # The data_loader.py builds the graph. We need to load it or build it per task.
    # According to the spec, the graph is built from the context.
    # We will assume a single global graph or per-task graph building is handled by the strategy.
    # For this runner, we'll assume the graph is passed or built inside the strategy.
    # However, to match the "load_noisy_graphs" pattern, let's check if a global graph exists.
    # Since T011 generates a graph file, we might need to load it if we are doing noisy.
    # T019 is for CLEAN results. We build the graph per task or load a clean graph.
    # Let's assume the strategy handles graph construction from the task context.
    
    results = []
    
    logger.info(f"Running {len(tasks)} tasks with Lazy strategy...")
    
    # Run batch
    for task in tasks:
        # Build graph for this task
        # We need to import build_memory_graph from graph_utils
        from graph_utils import build_memory_graph
        try:
            graph = build_memory_graph(task.get('context', ''))
        except Exception as e:
            logger.error(f"Failed to build graph for task {task.get('id')}: {e}")
            continue
        
        result = evaluate_task(task, graph, strategy, engine)
        results.append(result)
        
        # Log progress
        logger.info(f"Completed task {result['task_id']}: acc={result['accuracy']}, nodes={result['nodes_visited']}")
    
    # Save results
    output_path = project_root / "data" / "processed" / "lazy_results.csv"
    if results:
        save_results_to_csv(results, output_path)
        logger.info(f"Results saved to {output_path}")
    else:
        logger.warning("No results to save.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
