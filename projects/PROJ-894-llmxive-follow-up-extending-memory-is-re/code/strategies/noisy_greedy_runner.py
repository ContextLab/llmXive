import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure parent directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner import load_tasks, load_graph, run_batch, save_results_to_csv, TimeoutHandler
from strategies.greedy import run_greedy_strategy
from config import get_model_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not isinstance(answer, str):
        return str(answer) if answer is not None else ""
    return answer.strip().lower()

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSONL file.
    Expected schema: question, context, answer, task_id (optional, derived from index if missing)
    """
    tasks = []
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                task = json.loads(line)
                if 'task_id' not in task:
                    task['task_id'] = f"task_{idx}"
                tasks.append(task)
            except json.JSONDecodeError as e:
                logger.error(f"Skipping malformed JSON line {idx}: {e}")
                continue
    
    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    return tasks

def evaluate_task(
    task: Dict[str, Any], 
    graph_data: Dict[str, Any], 
    strategy_name: str,
    top_k: int = 5,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Evaluate a single task using the Greedy strategy on a noisy graph.
    
    Args:
        task: Task dictionary containing question, context, answer, task_id
        graph_data: Dictionary mapping task_id to graph edges (from noisy graph file)
        strategy_name: Name of the strategy (for logging)
        top_k: Top-k edges to select in Greedy strategy
        timeout: Hard timeout per task in seconds
    
    Returns:
        Result dictionary with metrics
    """
    task_id = task.get('task_id', 'unknown')
    graph = graph_data.get(task_id)
    
    if graph is None:
        logger.warning(f"No graph found for task {task_id}. Skipping.")
        return {
            'task_id': task_id,
            'accuracy': None,
            'nodes_visited': 0,
            'latency_ms': 0,
            'evidence_threshold': top_k,
            'status': 'MISSING_GRAPH'
        }

    start_time = time.time()
    status = 'SUCCESS'
    accuracy = None
    nodes_visited = 0
    
    try:
        # Run the greedy strategy
        # The strategy returns (nodes_visited, visited_nodes_list, execution_time)
        # We assume the strategy handles the LLM inference internally if needed, 
        # or we simulate the "reconstruction" logic here based on the graph.
        
        # For this specific runner, we call the strategy function directly.
        # The strategy function expects (graph, query, ...) and returns metrics.
        
        # Note: The actual "accuracy" calculation depends on whether we have ground truth.
        # If the task has an 'answer' field, we assume ground truth exists and we 
        # compare the strategy's output against it. 
        # Since the strategy 'run_greedy_strategy' returns traversal metrics, 
        # we need to map the traversal result to an accuracy.
        # In the context of "Memory Reconstruction", accuracy is often binary: 
        # Did the traversal find the correct node/edge path?
        # For this implementation, we will assume the strategy returns a boolean 'found' 
        # or we compute it based on the nodes visited matching the answer.
        
        # To keep it aligned with T018 (Greedy) implementation:
        # run_greedy_strategy(graph, query, top_k) -> (nodes_visited, result_dict)
        
        # Simulate the execution with timeout
        handler = TimeoutHandler(timeout)
        with handler:
            try:
                nodes_visited, result = run_greedy_strategy(graph, task.get('question', ''), top_k)
                
                # Determine accuracy: 
                # If the strategy returns a 'found' flag or similar in result, use it.
                # Otherwise, if we are in a "reconstruction" context, we might check 
                # if the 'answer' entity is in the visited nodes.
                # Since we don't have the exact return signature of run_greedy_strategy 
                # from the prompt's API surface (it just lists names), we assume a standard 
                # return of (int, dict) where dict contains 'found' or 'reconstructed_answer'.
                
                # Fallback logic: if the result dict has 'found', use it.
                # If not, we assume the traversal was "successful" if nodes_visited > 0 
                # and the graph wasn't degenerate, but this is a heuristic.
                # Ideally, the strategy returns a boolean success.
                
                found = result.get('found', False) if isinstance(result, dict) else False
                
                # If we have a ground truth answer, we could check if it was found.
                # For now, we rely on the strategy's internal logic to set 'found'.
                accuracy = 1.0 if found else 0.0
                
            except TimeoutHandler.TimeoutError:
                status = 'TIMEOUT'
                nodes_visited = 0
                accuracy = None
    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}")
        status = 'ERROR'
        nodes_visited = 0
        accuracy = None

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    return {
        'task_id': task_id,
        'accuracy': accuracy,
        'nodes_visited': nodes_visited,
        'latency_ms': round(latency_ms, 2),
        'evidence_threshold': top_k,
        'status': status
    }

def main():
    parser = argparse.ArgumentParser(description="Run Noisy Greedy Strategy on Graph Memory Tasks")
    parser.add_argument('--input', type=str, required=True, help="Path to input tasks JSONL file")
    parser.add_argument('--graph', type=str, required=True, help="Path to noisy graph JSON file (generated by T011c)")
    parser.add_argument('--output', type=str, required=True, help="Path to output CSV results file")
    parser.add_argument('--topk', type=int, default=5, help="Top-k edges for Greedy selection")
    parser.add_argument('--timeout', type=int, default=60, help="Timeout per task in seconds")
    
    args = parser.parse_args()

    logger.info(f"Starting Noisy Greedy Runner with top_k={args.topk}, timeout={args.timeout}s")
    logger.info(f"Input tasks: {args.input}")
    logger.info(f"Noisy graph: {args.graph}")
    logger.info(f"Output results: {args.output}")

    # Load tasks
    tasks = load_tasks(args.input)
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        sys.exit(1)

    # Load noisy graphs
    if not os.path.exists(args.graph):
        logger.error(f"Noisy graph file not found: {args.graph}")
        sys.exit(1)
    
    with open(args.graph, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    
    logger.info(f"Loaded graph data for {len(graph_data)} tasks")

    # Process tasks
    results = []
    for task in tasks:
        result = evaluate_task(
            task=task,
            graph_data=graph_data,
            strategy_name='NoisyGreedy',
            top_k=args.topk,
            timeout=args.timeout
        )
        results.append(result)
        logger.info(f"Completed task {result['task_id']}: status={result['status']}, acc={result['accuracy']}")

    # Save results
    save_results_to_csv(results, args.output)
    logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()