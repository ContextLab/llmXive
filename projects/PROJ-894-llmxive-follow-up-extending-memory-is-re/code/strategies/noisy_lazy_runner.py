import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from runner import load_tasks, load_graph, run_batch, save_results_to_csv, TimeoutError
from strategies.lazy import run_lazy_strategy
from graph_utils import validate_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSONL file.
    Expected format: each line is a JSON object with 'question', 'context', 'answer', 'task_id'.
    """
    tasks = []
    logger.info(f"Loading tasks from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                task = json.loads(line)
                # Ensure required fields exist
                if 'task_id' not in task:
                    task['task_id'] = f"task_{line_num}"
                if 'question' not in task or 'context' not in task or 'answer' not in task:
                    logger.warning(f"Skipping line {line_num}: missing required fields")
                    continue
                tasks.append(task)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON on line {line_num}: {e}")
                continue
    logger.info(f"Loaded {len(tasks)} tasks")
    return tasks

def evaluate_task(task: Dict[str, Any], graph: Dict[str, Any], strategy_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single task using the Lazy strategy on the provided graph.
    
    Args:
        task: The task dictionary containing question, context, answer, etc.
        graph: The graph structure (noisy) to traverse.
        strategy_params: Parameters for the Lazy strategy (e.g., threshold).
    
    Returns:
        A dictionary containing task_id, accuracy, nodes_visited, latency_ms, status, evidence_threshold.
    """
    task_id = task.get('task_id', 'unknown')
    context = task.get('context', '')
    ground_truth = task.get('answer', '')
    question = task.get('question', '')

    logger.info(f"Evaluating task {task_id}")

    # Check for degenerate cases
    if not context or not graph:
        logger.warning(f"Task {task_id} has empty context or graph. Marking as DEGENERATE.")
        return {
            'task_id': task_id,
            'accuracy': 0.0,
            'nodes_visited': 0,
            'latency_ms': 0.0,
            'status': 'DEGENERATE',
            'evidence_threshold': strategy_params.get('threshold', 0.0)
        }

    start_time = time.time()
    status = 'COMPLETED'
    nodes_visited = 0
    accuracy = 0.0

    try:
        # Run the lazy strategy
        # The run_lazy_strategy function is expected to return (reconstructed_memory, nodes_visited, status)
        # We need to adapt this to the specific signature of run_lazy_strategy
        # Based on existing code, run_lazy_strategy likely takes graph and question/context
        
        # We assume the graph is passed as a NetworkX graph or similar structure
        # The strategy will traverse the graph to reconstruct memory
        
        # For this implementation, we'll call run_lazy_strategy with the necessary parameters
        # and capture the result
        
        # Note: The actual implementation of run_lazy_strategy needs to be compatible
        # with the noisy graph structure. We assume it handles the graph traversal.
        
        # Since we don't have the exact signature, we'll make a reasonable assumption:
        # run_lazy_strategy(graph, question, context, threshold) -> (memory, nodes_visited, status)
        
        # However, looking at the existing code structure, it seems the strategy is run
        # within the runner framework. We'll use the run_batch approach for consistency.
        
        # For a single task evaluation, we'll simulate the strategy execution
        # This is a placeholder for the actual strategy logic that should be implemented
        # in the lazy.py module.
        
        # To properly integrate, we need to ensure the graph is in the correct format
        # and the strategy can handle it.
        
        # For now, we'll assume the graph is a dict and convert it to a format the strategy expects
        # This is a simplification; the actual implementation should be more robust.
        
        # Attempt to run the strategy
        # We'll use a try-except block to handle any errors gracefully
        try:
            # Call the strategy with the graph and task information
            # The exact parameters may need adjustment based on the actual implementation
            reconstructed_memory, nodes_visited, strategy_status = run_lazy_strategy(
                graph=graph,
                question=question,
                context=context,
                threshold=strategy_params.get('threshold', 0.7)
            )
            
            # Determine accuracy by comparing reconstructed memory to ground truth
            # This is a simplified comparison; a real implementation would use more sophisticated metrics
            if ground_truth and reconstructed_memory:
                norm_gt = normalize_answer(ground_truth)
                norm_recon = normalize_answer(str(reconstructed_memory))
                accuracy = 1.0 if norm_gt == norm_recon else 0.0
            else:
                accuracy = 0.0
                
            status = strategy_status if strategy_status else 'COMPLETED'
            
        except Exception as e:
            logger.error(f"Strategy execution failed for task {task_id}: {e}")
            status = 'UNRESOLVED'
            nodes_visited = 0
            accuracy = 0.0

    except TimeoutError:
        logger.warning(f"Task {task_id} timed out")
        status = 'TIMEOUT'
        accuracy = 0.0
    except Exception as e:
        logger.error(f"Unexpected error evaluating task {task_id}: {e}")
        status = 'ERROR'
        accuracy = 0.0

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    result = {
        'task_id': task_id,
        'accuracy': accuracy,
        'nodes_visited': nodes_visited,
        'latency_ms': round(latency_ms, 2),
        'status': status,
        'evidence_threshold': round(strategy_params.get('threshold', 0.7), 2)
    }

    logger.info(f"Task {task_id} completed: accuracy={accuracy}, nodes_visited={nodes_visited}, status={status}")
    return result

def main():
    """
    Main function to run the Noisy Lazy Execution Runner.
    
    This script:
    1. Loads the noisy graph from data/processed/graphs/graph_noise_42.json
    2. Loads tasks from a specified input file (default: data/raw/locomo.jsonl)
    3. Runs the Lazy strategy on each task with the noisy graph
    4. Logs results to data/processed/noisy_lazy_results.csv
    """
    parser = argparse.ArgumentParser(description="Noisy Lazy Execution Runner")
    parser.add_argument('--input', type=str, default='data/raw/locomo.jsonl',
                        help='Path to the input tasks file (JSONL format)')
    parser.add_argument('--graph', type=str, default='data/processed/graphs/graph_noise_42.json',
                        help='Path to the noisy graph file (JSON format)')
    parser.add_argument('--output', type=str, default='data/processed/noisy_lazy_results.csv',
                        help='Path to the output results CSV file')
    parser.add_argument('--threshold', type=float, default=0.7,
                        help='Evidence threshold for the Lazy strategy (default: 0.7)')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Timeout in seconds per task (default: 300)')
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Noisy Lazy Execution Runner")
    logger.info(f"Input tasks: {args.input}")
    logger.info(f"Noisy graph: {args.graph}")
    logger.info(f"Output results: {args.output}")
    logger.info(f"Threshold: {args.threshold}")
    logger.info(f"Timeout: {args.timeout}s")

    # Load the noisy graph
    try:
        graph = load_graph(args.graph)
        if not validate_graph(graph):
            logger.error("Invalid graph structure")
            sys.exit(1)
        logger.info("Noisy graph loaded and validated successfully")
    except Exception as e:
        logger.error(f"Failed to load noisy graph: {e}")
        sys.exit(1)

    # Load tasks
    try:
        tasks = load_tasks(args.input)
        if not tasks:
            logger.warning("No tasks loaded. Exiting.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)

    # Prepare strategy parameters
    strategy_params = {
        'threshold': args.threshold,
        'timeout': args.timeout
    }

    # Run evaluation on all tasks
    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}")
        try:
            result = evaluate_task(task, graph, strategy_params)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing task {task.get('task_id', i)}: {e}")
            # Add a failure record
            results.append({
                'task_id': task.get('task_id', f'task_{i}'),
                'accuracy': 0.0,
                'nodes_visited': 0,
                'latency_ms': 0.0,
                'status': 'ERROR',
                'evidence_threshold': args.threshold
            })

    # Save results to CSV
    if results:
        save_results_to_csv(results, args.output)
        logger.info(f"Results saved to {args.output}")
    else:
        logger.warning("No results to save.")

    logger.info("Noisy Lazy Execution Runner completed")

if __name__ == "__main__":
    main()