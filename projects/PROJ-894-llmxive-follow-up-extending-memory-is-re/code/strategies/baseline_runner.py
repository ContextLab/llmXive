"""
Baseline execution runner for the Full traversal strategy.
Executes tasks from the LoCoMo dataset using the FullTraversal strategy
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

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from data_loader import fetch_locomo_dataset, build_memory_graph
from strategies.full import FullTraversal
from runner import run_batch, save_results_to_csv, TimeoutError
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output paths
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "baseline_results.csv"
LOG_FILE = OUTPUT_DIR / "baseline_execution.log"

def ensure_output_dirs():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks(subset_size: int = 50) -> List[Dict[str, Any]]:
    """
    Load tasks from the LoCoMo dataset.
    
    Args:
        subset_size: Number of tasks to load (for testing/scaling).
        
    Returns:
        List of task dictionaries.
    """
    logger.info(f"Loading LoCoMo dataset (subset size: {subset_size})...")
    try:
        tasks = fetch_locomo_dataset(subset=subset_size)
        logger.info(f"Successfully loaded {len(tasks)} tasks.")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def evaluate_task(task: Dict[str, Any], strategy: FullTraversal) -> Dict[str, Any]:
    """
    Evaluate a single task using the FullTraversal strategy.
    
    Args:
        task: Task dictionary containing 'question', 'context', 'answer'.
        strategy: The FullTraversal strategy instance.
        
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms.
    """
    task_id = task.get('id', f"task_{hash(task['question']) % 10000}")
    question = task.get('question', '')
    context = task.get('context', '')
    ground_truth = task.get('answer', '')
    
    # Build memory graph from context
    try:
        graph = build_memory_graph(context)
    except Exception as e:
        logger.warning(f"Failed to build graph for task {task_id}: {e}")
        # Handle degenerate case: return failure metrics
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': 0.0,
            'status': 'graph_build_failed',
            'error': str(e)
        }
    
    # Run the strategy
    start_time = time.time()
    try:
        result = strategy.execute(task_id, question, graph)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        # Calculate accuracy (simple string match or semantic similarity)
        # For now, using exact match as a baseline; can be extended
        predicted_answer = result.get('answer', '')
        accuracy = 1.0 if predicted_answer.lower() == ground_truth.lower() else 0.0
        
        # If the strategy returns a confidence score, we might use a threshold
        # but for baseline, we stick to the binary match or a more robust metric
        # if the LLM returns a structured response.
        # Assuming result contains 'answer' and potentially 'confidence'
        
        return {
            'task_id': task_id,
            'accuracy': accuracy,
            'nodes_visited': result.get('nodes_visited', 0),
            'latency_ms': latency_ms,
            'status': 'completed',
            'predicted_answer': predicted_answer,
            'ground_truth': ground_truth
        }
    except TimeoutError as te:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        logger.warning(f"Task {task_id} timed out after {latency_ms/1000:.2f}s")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': latency_ms,
            'status': 'timeout',
            'error': 'TimeoutError'
        }
    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        logger.error(f"Task {task_id} failed with error: {e}")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': latency_ms,
            'status': 'failed',
            'error': str(e)
        }

def main():
    """Main entry point for the baseline execution runner."""
    ensure_output_dirs()
    
    # Initialize strategy
    model_path = get_model_path()
    if not model_path:
        logger.warning("No model path configured. Using default or failing gracefully.")
        # In a real scenario, we might want to fail here if no model is available
        # For now, we proceed and let the strategy handle it or fail at inference
    
    strategy = FullTraversal(model_path=model_path)
    
    # Load tasks
    # Using a small subset for the initial run to ensure it completes in CI
    # The subset size can be adjusted based on available resources
    tasks = load_tasks(subset_size=10) 
    
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        return
    
    # Process tasks in batches (though here we do single batch for simplicity)
    # Using runner's run_batch for timeout handling and batching
    results = []
    
    logger.info(f"Starting baseline execution on {len(tasks)} tasks...")
    
    # We use run_batch to handle timeouts and parallelism if needed
    # For baseline, we might run sequentially to avoid LLM rate limits or resource contention
    # But run_batch can handle the timeout logic
    batch_size = 10
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} tasks)...")
        
        batch_results = run_batch(
            tasks=batch,
            evaluate_func=lambda t: evaluate_task(t, strategy),
            timeout_per_task=60.0, # 60 seconds per task
            max_workers=1 # Sequential to avoid LLM overload in CI
        )
        results.extend(batch_results)
    
    # Save results to CSV
    if results:
        save_results_to_csv(results, OUTPUT_FILE)
        logger.info(f"Results saved to {OUTPUT_FILE}")
    else:
        logger.warning("No results generated. CSV not created.")
        
    logger.info("Baseline execution completed.")

if __name__ == "__main__":
    main()