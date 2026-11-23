"""
Noisy Greedy Execution Runner

Implements the execution runner for the Greedy strategy on noisy graphs.
Loads the noisy graph dataset (graph_noise_42.json) and executes the Greedy
traversal strategy, logging results to a CSV file.

Dependencies:
- T011a-1b: Clean graph extraction
- T011c: Noisy graph generation (graph_noise_42.json)
- T018: Greedy strategy implementation
- T006: Signal-based timeout handler
"""

import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from strategies.greedy import run_greedy_strategy
from runner import load_graph, load_tasks, run_task, save_results_to_csv, TaskResult
from graph_utils import validate_graph
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    return answer.strip().lower().replace(" ", "")

def load_tasks_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSONL file.

    Args:
        jsonl_path: Path to the JSONL file containing tasks

    Returns:
        List of task dictionaries
    """
    tasks = []
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Task file not found: {jsonl_path}")

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                task = json.loads(line)
                # Ensure required fields exist
                required_fields = ['task_id', 'question', 'context', 'answer']
                for field in required_fields:
                    if field not in task:
                        logger.warning(f"Line {line_num}: Missing field '{field}', skipping")
                        continue
                tasks.append(task)
            except json.JSONDecodeError as e:
                logger.warning(f"Line {line_num}: Invalid JSON - {e}")
                continue

    logger.info(f"Loaded {len(tasks)} tasks from {jsonl_path}")
    return tasks

def evaluate_task(
    task: Dict[str, Any],
    graph: Dict[str, Any],
    strategy_name: str = "greedy",
    threshold: float = 0.5,
    topk: int = 5
) -> TaskResult:
    """
    Evaluate a single task using the Greedy strategy on a noisy graph.

    Args:
        task: Task dictionary containing question, context, answer
        graph: Graph dictionary (nodes, edges)
        strategy_name: Name of the strategy (for logging)
        threshold: Evidence threshold for greedy selection
        topk: Number of top edges to consider

    Returns:
        TaskResult object with execution metrics
    """
    task_id = task.get('task_id', 'unknown')
    question = task.get('question', '')
    context = task.get('context', '')
    ground_truth = task.get('answer', '')

    start_time = time.time()

    try:
        # Run greedy strategy on the graph
        # The graph is already noisy (from graph_noise_42.json)
        result = run_greedy_strategy(
            graph=graph,
            query=question,
            context=context,
            threshold=threshold,
            topk=topk
        )

        latency_ms = (time.time() - start_time) * 1000

        # Determine accuracy
        # For this benchmark, we compare extracted answer with ground truth
        # If the strategy returns an answer, we check if it matches
        predicted_answer = result.get('answer', '')
        accuracy = 1.0 if normalize_answer(predicted_answer) == normalize_answer(ground_truth) else 0.0

        return TaskResult(
            task_id=task_id,
            accuracy=accuracy,
            nodes_visited=result.get('nodes_visited', 0),
            latency_ms=latency_ms,
            status="COMPLETED",
            extra={
                'evidence_threshold': threshold,
                'topk': topk,
                'predicted_answer': predicted_answer,
                'ground_truth': ground_truth
            }
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Task {task_id} failed: {str(e)}")

        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=latency_ms,
            status="ERROR",
            extra={
                'error': str(e),
                'evidence_threshold': threshold,
                'topk': topk
            }
        )

def main():
    """Main entry point for the Noisy Greedy Runner."""
    parser = argparse.ArgumentParser(
        description="Run Greedy strategy on noisy graphs"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the tasks JSONL file"
    )
    parser.add_argument(
        "--graph",
        type=str,
        required=True,
        help="Path to the noisy graph JSON file (graph_noise_42.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output CSV file"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Evidence threshold for greedy selection (default: 0.5)"
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=5,
        help="Number of top edges to consider (default: 5)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per task in seconds (default: 300)"
    )

    args = parser.parse_args()

    logger.info(f"Starting Noisy Greedy Runner")
    logger.info(f"Input tasks: {args.input}")
    logger.info(f"Noisy graph: {args.graph}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Threshold: {args.threshold}, TopK: {args.topk}")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load tasks
    try:
        tasks = load_tasks_from_jsonl(args.input)
    except FileNotFoundError as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)

    # Load noisy graph
    try:
        graph = load_graph(args.graph)
        # Validate graph structure
        if not validate_graph(graph):
            logger.error("Graph validation failed")
            sys.exit(1)
        logger.info(f"Loaded noisy graph with {len(graph.get('nodes', []))} nodes and {len(graph.get('edges', []))} edges")
    except FileNotFoundError as e:
        logger.error(f"Failed to load noisy graph: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in graph file: {e}")
        sys.exit(1)

    # Run evaluation
    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id')}")

        # Run with timeout handling
        result = run_task(
            task=task,
            graph=graph,
            evaluator=evaluate_task,
            evaluator_kwargs={
                'strategy_name': 'greedy',
                'threshold': args.threshold,
                'topk': args.topk
            },
            timeout=args.timeout
        )

        results.append(result)
        logger.info(f"Task {task.get('task_id')} completed: status={result.status}, accuracy={result.accuracy}")

    # Save results
    save_results_to_csv(results, args.output)
    logger.info(f"Results saved to {args.output}")

    # Log summary
    total_tasks = len(results)
    completed_tasks = sum(1 for r in results if r.status == "COMPLETED")
    avg_accuracy = sum(r.accuracy for r in results) / total_tasks if total_tasks > 0 else 0.0
    avg_latency = sum(r.latency_ms for r in results) / total_tasks if total_tasks > 0 else 0.0

    logger.info(f"Summary: {completed_tasks}/{total_tasks} completed, avg_accuracy={avg_accuracy:.4f}, avg_latency={avg_latency:.2f}ms")

if __name__ == "__main__":
    main()