"""
Noisy Baseline Execution Runner for T013b.

Executes the "Full" active reconstruction strategy on synthetic noisy graphs
(generated in T011) and logs results to data/processed/noisy_baseline_results.csv.

This script MUST fail loudly if the noisy graph file is missing or invalid.
It does NOT generate synthetic data; it consumes the pre-generated noisy graphs.
"""

import os
import sys
import time
import json
import logging
import csv
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategies.full import FullTraversal
from data_loader import load_noisy_graphs
from runner import run_batch, save_results_to_csv, TimeoutError
from config import get_model_path
import networkx as nx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Output paths
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "noisy_baseline_results.csv"
NOISY_GRAPHS_PATH = PROJECT_ROOT / "data" / "processed" / "graphs" / "graph_noise_42.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks(graph_data_path: Path) -> List[Dict[str, Any]]:
    """
    Loads tasks from the pre-generated noisy graph file.
    The graph file structure is expected to be:
    {
      "tasks": [
        {
          "task_id": "string",
          "question": "string",
          "context": "string",
          "answer": "string",
          "graph": { ... graph structure ... }
        },
        ...
      ]
    }
    """
    if not graph_data_path.exists():
        raise FileNotFoundError(
            f"Noisy graph file not found at {graph_data_path}. "
            "Please ensure T011 (data_loader.py) has successfully generated "
            "data/processed/graphs/graph_noise_42.json."
        )

    logger.info(f"Loading noisy graphs from {graph_data_path}")
    try:
        with open(graph_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from {graph_data_path}: {e}")

    if "tasks" not in data:
        raise ValueError(f"Expected 'tasks' key in {graph_data_path}, but got: {list(data.keys())}")

    tasks = data["tasks"]
    logger.info(f"Loaded {len(tasks)} tasks from noisy graph file.")
    return tasks

def evaluate_task(task: Dict[str, Any], model_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs the FullTraversal strategy on a single task with its associated noisy graph.
    Returns a dictionary of metrics.
    """
    task_id = task.get("task_id", "unknown")
    question = task.get("question", "")
    context = task.get("context", "")
    answer = task.get("answer", "")
    graph_data = task.get("graph")

    if graph_data is None:
        logger.warning(f"Task {task_id} has no graph data. Skipping.")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": 0.0,
            "status": "skipped_no_graph"
        }

    # Reconstruct NetworkX graph from JSON
    try:
        G = nx.DiGraph()
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # Add nodes
        for node in nodes:
            if isinstance(node, dict):
                G.add_node(node.get("id", str(len(G))), **node)
            else:
                G.add_node(node)
        
        # Add edges
        for edge in edges:
            if isinstance(edge, dict):
                G.add_edge(edge["source"], edge["target"], **edge)
            else:
                # Assume tuple or list
                G.add_edge(edge[0], edge[1])
    except Exception as e:
        logger.error(f"Failed to reconstruct graph for task {task_id}: {e}")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": 0.0,
            "status": "error_graph_reconstruction"
        }

    # Initialize strategy
    # Note: We pass the model path to the strategy if it needs to make inference calls
    # for the "Full" traversal, though often the graph traversal itself is the focus.
    # The FullTraversal class handles its own internal logic.
    strategy = FullTraversal(model_path=model_path)

    start_time = time.time()
    try:
        result = strategy.run(
            graph=G,
            question=question,
            context=context,
            target_answer=answer
        )
        
        # Calculate metrics
        nodes_visited = result.get("nodes_visited", 0)
        success = result.get("success", False)
        accuracy = 1.0 if success else 0.0
        
        # If the strategy returns a specific answer, we could compare it to the target
        # For now, we rely on the strategy's internal success flag.
        
        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "task_id": task_id,
            "accuracy": accuracy,
            "nodes_visited": nodes_visited,
            "latency_ms": round(elapsed_ms, 2),
            "status": "completed"
        }

    except TimeoutError as te:
        logger.warning(f"Task {task_id} timed out.")
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": -1.0, # Indicator for timeout
            "status": "timeout"
        }
    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}")
        logger.error(traceback.format_exc())
        return {
            "task_id": task_id,
            "accuracy": 0.0,
            "nodes_visited": 0,
            "latency_ms": -1.0,
            "status": "error"
        }

def main():
    """
    Main entry point for the noisy baseline runner.
    """
    logger.info("Starting Noisy Baseline Runner (T013b)...")
    
    # Check for required graph file
    if not NOISY_GRAPHS_PATH.exists():
        logger.error(f"CRITICAL: Noisy graph file missing at {NOISY_GRAPHS_PATH}")
        logger.error("This task depends on T011 completing successfully to generate the noisy graphs.")
        sys.exit(1)

    model_path = get_model_path()
    if model_path:
        logger.info(f"Using model path: {model_path}")
    else:
        logger.warning("No model path configured. Traversal strategies may run without LLM inference.")

    # Load tasks
    try:
        tasks = load_tasks(NOISY_GRAPHS_PATH)
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)

    if not tasks:
        logger.warning("No tasks found in the noisy graph file.")
        # Create empty output file to satisfy schema validation
        save_results_to_csv([], str(OUTPUT_FILE))
        return

    # Execute tasks
    logger.info(f"Executing {len(tasks)} tasks...")
    results = []
    
    # Process tasks (using run_batch for timeout handling if needed, 
    # but here we call evaluate_task directly to keep it simple and robust)
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id')}")
        result = evaluate_task(task, model_path)
        results.append(result)

    # Save results
    logger.info(f"Saving results to {OUTPUT_FILE}")
    save_results_to_csv(results, str(OUTPUT_FILE))
    
    # Summary
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    errors = sum(1 for r in results if r["status"].startswith("error") or r["status"] == "skipped_no_graph")
    timeouts = sum(1 for r in results if r["status"] == "timeout")
    
    logger.info(f"Execution complete. Total: {total}, Completed: {completed}, Errors: {errors}, Timeouts: {timeouts}")
    logger.info(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()