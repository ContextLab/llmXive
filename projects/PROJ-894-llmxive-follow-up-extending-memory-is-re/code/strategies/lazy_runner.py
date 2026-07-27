"""
Runner for the Lazy traversal strategy.
Executes tasks using the LazyTraversal algorithm and logs results.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.lazy import LazyTraversal
from data_loader import fetch_locomo_dataset, save_raw_data, ensure_output_dirs
from runner import run_task, save_results_to_csv, TimeoutError
from graph_utils import build_memory_graph, validate_graph
from inference import LLMInferenceEngine
from config import get_model_path

logger = logging.getLogger(__name__)

def load_tasks(dataset_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load tasks from the LoCoMo dataset.
    If dataset_path is provided, uses cached data; otherwise fetches from HF.
    """
    if dataset_path and os.path.exists(dataset_path):
        logger.info(f"Loading tasks from cached dataset: {dataset_path}")
        # Assuming cached data is saved as JSON or CSV by data_loader
        # For simplicity, we re-fetch or assume a standard location if not passed
        # In a real scenario, this would load the specific cached file
        pass
    
    # Fetch fresh data for execution to ensure real data usage
    # T011 ensures data is available, but we call fetch to be safe and get the list
    try:
        data_path = Path("data/raw/locomo_test.json")
        if not data_path.exists():
            fetch_locomo_dataset(split="test", output_path=str(data_path))
        
        with open(data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        tasks = []
        for item in raw_data:
            tasks.append({
                "task_id": item.get("id", f"task_{len(tasks)}"),
                "question": item.get("question", ""),
                "context": item.get("context", ""),
                "answer": item.get("answer", "")
            })
        return tasks
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        raise

def evaluate_task(task: Dict[str, Any], timeout: float = 300) -> Dict[str, Any]:
    """
    Evaluate a single task using the LazyTraversal strategy.
    
    Args:
        task: Dictionary containing task_id, question, context, answer.
        timeout: Maximum execution time in seconds.
        
    Returns:
        Dictionary with task_id, accuracy, nodes_visited, latency_ms, status.
    """
    task_id = task["task_id"]
    question = task["question"]
    context = task["context"]
    ground_truth = task["answer"]
    
    start_time = time.time()
    
    try:
        # 1. Build Memory Graph from context
        # T004 ensures build_memory_graph is available
        graph = build_memory_graph(context)
        
        if not validate_graph(graph):
            logger.warning(f"Task {task_id}: Graph validation failed or empty.")
            return {
                "task_id": task_id,
                "accuracy": 0.0,
                "nodes_visited": 0,
                "latency_ms": 0.0,
                "status": "invalid_graph"
            }
        
        # 2. Initialize Inference Engine
        model_path = get_model_path()
        engine = LLMInferenceEngine(model_path=model_path)
        
        # 3. Run Lazy Traversal
        # LazyTraversal handles the logic of traversing and querying
        strategy = LazyTraversal(engine=engine, evidence_threshold=0.8)
        
        # Execute strategy
        result = strategy.run(graph, question)
        
        # 4. Evaluate Accuracy
        # Simple string matching or semantic similarity (using LLM if needed, but keeping simple for now)
        # For robustness, we compare the generated answer to the ground truth
        generated_answer = result.get("answer", "")
        
        # Basic accuracy check (case-insensitive substring or exact match)
        # In a real research setting, this might use a metric like BLEU or an LLM judge
        is_correct = 0.0
        if generated_answer and ground_truth:
            if ground_truth.lower() in generated_answer.lower():
                is_correct = 1.0
            elif generated_answer.lower() in ground_truth.lower():
                is_correct = 1.0
            else:
                # Fallback to LLM judge for semantic equivalence if strict match fails
                # For this implementation, we assume strict match or partial match logic
                pass 
        
        latency = (time.time() - start_time) * 1000.0
        
        return {
            "task_id": task_id,
            "accuracy": is_correct,
            "nodes_visited": result.get("nodes_visited", 0),
            "latency_ms": latency,
            "status": "success"
        }
        
    except TimeoutError as e:
        logger.warning(f"Task {task_id} timed out.")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": (time.time() - start_time) * 1000.0,
            "status": "timeout"
        }
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": (time.time() - start_time) * 1000.0,
            "status": "error",
            "error_msg": str(e)
        }

def main():
    """
    Main entry point for running the Lazy strategy on the LoCoMo benchmark.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "lazy_results.csv"
    
    logger.info("Starting Lazy Traversal Execution...")
    
    # Load tasks
    tasks = load_tasks()
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(tasks)} tasks.")
    
    results = []
    columns = ["task_id", "accuracy", "nodes_visited", "latency_ms", "status"]
    
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task['task_id']}")
        result = evaluate_task(task, timeout=300)
        results.append(result)
        
        # Log progress
        if (i + 1) % 5 == 0:
            logger.info(f"Completed {i+1} tasks. Last status: {result['status']}")
    
    # Save results
    save_results_to_csv(results, str(output_file), columns)
    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
