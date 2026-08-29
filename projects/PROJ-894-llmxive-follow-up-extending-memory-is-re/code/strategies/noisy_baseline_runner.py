"""
Noisy Baseline Execution Runner for T013b.
Executes the "Full" active reconstruction strategy on synthetic noisy graphs
and logs results to data/processed/noisy_baseline_results.csv.
"""
import os
import sys
import time
import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional

import networkx as nx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import TaskResult, TimeoutHandler, timeout_context, run_task
from strategies.full import run_full_strategy
from data_loader import load_noisy_graphs
from inference import LLMInferenceEngine
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROCESSED_DIR
RESULTS_FILE = RESULTS_DIR / "noisy_baseline_results.csv"

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    return answer.strip().lower()

def load_tasks(graph_data: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Load tasks from graph data.
    
    Args:
        graph_data: Dictionary mapping task_id to edges
        
    Returns:
        List of task records with graph
    """
    tasks = []
    
    # Load raw data for questions/answers
    raw_path = PROJECT_ROOT / "data" / "raw" / "locomo.jsonl"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data not found: {raw_path}")
    
    task_lookup = {}
    with open(raw_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            task_id = record.get("task_id", str(hash(record["question"]) % 10000))
            task_lookup[task_id] = record
    
    # Combine with graph data
    for task_id, edges in graph_data.items():
        if task_id in task_lookup:
            record = task_lookup[task_id]
            tasks.append({
                "task_id": task_id,
                "question": record["question"],
                "answer": record["answer"],
                "context": record["context"],
                "graph": edges
            })
        else:
            # Create synthetic task_id if not found
            tasks.append({
                "task_id": task_id,
                "question": f"Question for {task_id}",
                "answer": "Unknown",
                "context": "",
                "graph": edges
            })
    
    return tasks

def evaluate_task(task: Dict, strategy: str = "Full") -> TaskResult:
    """
    Evaluate a single task using the specified strategy.
    
    Args:
        task: Task record with graph
        strategy: Traversal strategy to use
        
    Returns:
        TaskResult with accuracy, nodes_visited, latency, status
    """
    task_id = task["task_id"]
    graph_edges = task["graph"]
    question = task["question"]
    ground_truth = task["answer"]
    
    # Convert edges to graph
    G = nx.DiGraph()
    for edge in graph_edges:
        G.add_edge(edge["source"], edge["target"], relation=edge["relation_string"])
    
    # Check for degenerate graphs
    if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
        logger.warning(f"Task {task_id}: Degenerate graph detected")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status="DEGENERATE"
        )
    
    # Initialize LLM engine
    try:
        model_path = get_model_path()
        if model_path and os.path.exists(model_path):
            llm = LLMInferenceEngine(model_path=model_path)
        else:
            # Fallback to a small model or skip inference for testing
            logger.warning(f"Model not found at {model_path}. Skipping inference.")
            # Return a placeholder result for testing without model
            return TaskResult(
                task_id=task_id,
                accuracy=0.0,
                nodes_visited=G.number_of_nodes(),
                latency_ms=0.0,
                status="UNRESOLVED"
            )
    except Exception as e:
        logger.error(f"Failed to initialize LLM engine: {str(e)}")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status="UNRESOLVED"
        )
    
    # Run strategy with timeout
    start_time = time.time()
    try:
        with timeout_context(timeout=300):  # 5 minute timeout per task
            result = run_full_strategy(G, question, llm)
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Calculate accuracy
            predicted = result.get("predicted_answer", "")
            predicted_normalized = normalize_answer(predicted)
            ground_truth_normalized = normalize_answer(ground_truth)
            accuracy = 1.0 if predicted_normalized == ground_truth_normalized else 0.0
            
            return TaskResult(
                task_id=task_id,
                accuracy=accuracy,
                nodes_visited=result.get("nodes_visited", 0),
                latency_ms=elapsed_time,
                status="COMPLETED"
            )
            
    except TimeoutError:
        elapsed_time = (time.time() - start_time) * 1000
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=elapsed_time,
            status="TIMEOUT"
        )
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        logger.error(f"Task {task_id} failed: {str(e)}")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=elapsed_time,
            status="UNRESOLVED"
        )

def save_results_to_csv(results: List[TaskResult], output_path: Path):
    """Save results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "accuracy", "nodes_visited", "latency_ms", "status"])
        
        for result in results:
            writer.writerow([
                result.task_id,
                result.accuracy,
                result.nodes_visited,
                result.latency_ms,
                result.status
            ])
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for noisy baseline execution."""
    logger.info("Starting Noisy Baseline Execution Runner (T013b)")
    
    # Load noisy graphs
    try:
        noisy_graphs = load_noisy_graphs("graph_noise_42.json")
        logger.info(f"Loaded {len(noisy_graphs)} noisy graphs")
    except FileNotFoundError as e:
        logger.error(f"Noisy graphs not found: {str(e)}")
        logger.error("Please run data_loader.py --noisy first to generate noisy graphs.")
        sys.exit(1)
    
    # Load tasks
    tasks = load_tasks(noisy_graphs)
    logger.info(f"Loaded {len(tasks)} tasks")
    
    if not tasks:
        logger.error("No tasks found to process")
        sys.exit(1)
    
    # Process tasks
    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task['task_id']}")
        result = evaluate_task(task)
        results.append(result)
        logger.info(f"  Status: {result.status}, Accuracy: {result.accuracy}")
    
    # Save results
    save_results_to_csv(results, RESULTS_FILE)
    
    # Summary
    completed = sum(1 for r in results if r.status == "COMPLETED")
    timeout = sum(1 for r in results if r.status == "TIMEOUT")
    degenerate = sum(1 for r in results if r.status == "DEGENERATE")
    unresolved = sum(1 for r in results if r.status == "UNRESOLVED")
    
    logger.info(f"Execution complete. Results saved to {RESULTS_FILE}")
    logger.info(f"Summary: COMPLETED={completed}, TIMEOUT={timeout}, DEGENERATE={degenerate}, UNRESOLVED={unresolved}")
    
    if completed > 0:
        avg_accuracy = sum(r.accuracy for r in results if r.status == "COMPLETED") / completed
        logger.info(f"Average accuracy (completed tasks): {avg_accuracy:.4f}")

if __name__ == "__main__":
    main()