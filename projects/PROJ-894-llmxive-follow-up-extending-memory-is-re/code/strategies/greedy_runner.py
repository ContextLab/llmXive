"""
Greedy Execution Runner for User Story 2.

This script implements the execution runner for the Greedy strategy.
It loads tasks, executes the Greedy traversal strategy using the provided graph,
and logs results to data/processed/greedy_results.csv.

It enforces a configurable timeout (default 1800s) via the runner's timeout handler.
It validates the configuration before starting.
"""

import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import TimeoutHandler, TaskResult, load_graph, load_tasks, run_batch
from strategies.greedy import run_greedy_strategy
from utils import get_seed, ensure_dir, get_config_path, get_state_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "greedy_results.csv"
DEFAULT_TIMEOUT = 1800  # Moderate duration as per spec

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def evaluate_task(
    task: Dict[str, Any],
    graph: Any,
    strategy_func,
    timeout_handler: TimeoutHandler
) -> TaskResult:
    """
    Execute a single task using the specified strategy.

    Args:
        task: Dictionary containing 'task_id', 'question', 'context', 'answer'.
        graph: The memory graph to traverse.
        strategy_func: The strategy function to execute (e.g., run_greedy_strategy).
        timeout_handler: The timeout handler instance.

    Returns:
        TaskResult object with execution metrics.
    """
    task_id = task.get('task_id', 'unknown')
    question = task.get('question', '')
    context = task.get('context', '')
    expected_answer = task.get('answer', '')

    start_time = time.time()
    status = "COMPLETED"
    accuracy = 0.0
    nodes_visited = 0
    token_count = 0
    evidence_threshold = 0.0

    try:
        with timeout_handler():
            # Execute the greedy strategy
            # The strategy function should return a dict with results
            result = strategy_func(
                graph=graph,
                question=question,
                context=context,
                task_id=task_id
            )

            if isinstance(result, dict):
                nodes_visited = result.get('nodes_visited', 0)
                token_count = result.get('token_count', 0)
                evidence_threshold = result.get('evidence_threshold', 0.0)
                
                # Determine accuracy based on result content
                # Assuming the strategy returns a boolean or score if it resolves
                if 'resolved' in result:
                    is_correct = result.get('resolved', False)
                    # For this runner, we assume the LLM or logic inside strategy 
                    # determines correctness. If it returns a score, use that.
                    if 'score' in result:
                        accuracy = float(result['score'])
                    else:
                        accuracy = 1.0 if is_correct else 0.0
                elif 'accuracy' in result:
                    accuracy = float(result['accuracy'])
                else:
                    # Fallback: if no explicit correctness, assume 0 or check specific keys
                    accuracy = 0.0

            else:
                logger.warning(f"Task {task_id}: Strategy returned unexpected type {type(result)}")
                status = "UNRESOLVED"

    except TimeoutHandler.TimeoutError:
        status = "TIMEOUT"
        logger.warning(f"Task {task_id}: Timed out after {timeout_handler.duration}s")
    except Exception as e:
        status = "DEGENERATE" if "degenerate" in str(e).lower() else "UNRESOLVED"
        logger.error(f"Task {task_id}: Execution failed with {type(e).__name__}: {e}")

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    return TaskResult(
        task_id=task_id,
        accuracy=accuracy,
        nodes_visited=nodes_visited,
        latency_ms=latency_ms,
        status=status,
        token_count=token_count,
        evidence_threshold=evidence_threshold
    )

def save_results_to_csv(results: List[TaskResult], output_path: Path):
    """
    Save a list of TaskResult objects to a CSV file.
    Ensures the output directory exists.
    """
    ensure_dir(output_path.parent)
    
    fieldnames = [
        'task_id', 'accuracy', 'nodes_visited', 'latency_ms', 
        'status', 'token_count', 'evidence_threshold'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                'task_id': r.task_id,
                'accuracy': r.accuracy,
                'nodes_visited': r.nodes_visited,
                'latency_ms': r.latency_ms,
                'status': r.status,
                'token_count': r.token_count,
                'evidence_threshold': r.evidence_threshold
            })
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Greedy Strategy Execution Runner")
    parser.add_argument('--input', type=str, required=True, help='Path to input graph JSON')
    parser.add_argument('--tasks', type=str, required=True, help='Path to tasks JSONL/JSON')
    parser.add_argument('--output', type=str, default=str(OUTPUT_FILE), help='Path to output CSV')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='Timeout in seconds')
    parser.add_argument('--topk', type=int, default=5, help='Top-k edges to select in greedy strategy')
    args = parser.parse_args()

    logger.info(f"Starting Greedy Runner with timeout={args.timeout}s, topk={args.topk}")

    # Validate configuration
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input graph file not found: {args.input}")
    if not os.path.exists(args.tasks):
        raise FileNotFoundError(f"Tasks file not found: {args.tasks}")
    
    # Ensure output directory exists
    ensure_dir(Path(args.output).parent)

    # Load Graph
    logger.info(f"Loading graph from {args.input}")
    graph = load_graph(args.input)
    if graph is None:
        raise ValueError(f"Failed to load graph from {args.input}")

    # Load Tasks
    logger.info(f"Loading tasks from {args.tasks}")
    tasks = load_tasks(args.tasks)
    if not tasks:
        raise ValueError(f"No tasks found in {args.tasks}")
    logger.info(f"Loaded {len(tasks)} tasks")

    # Initialize Timeout Handler
    timeout_handler = TimeoutHandler(duration=args.timeout)

    # Run Batch
    results = run_batch(
        tasks=tasks,
        graph=graph,
        strategy_func=run_greedy_strategy,
        evaluate_func=evaluate_task,
        timeout_handler=timeout_handler,
        strategy_kwargs={'topk': args.topk}
    )

    # Save Results
    save_results_to_csv(results, Path(args.output))

    logger.info("Greedy Runner completed successfully.")

if __name__ == "__main__":
    main()
