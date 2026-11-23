"""
Greedy Execution Runner for T019b.

Implements the execution runner for the Greedy strategy, logging results to
data/processed/greedy_results.csv.

This runner:
1. Loads the graph from the specified input path.
2. Validates the graph structure.
3. Invokes the GreedyTraversal strategy (T018) with a configurable top_k.
4. Enforces a timeout handler (T006) with a moderate default duration.
5. Logs task_id, accuracy, nodes_visited, latency_ms, status, token_count, and top_k.
6. Conforms to the schema defined in contracts/results.schema.yaml.
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

# Project imports based on API surface
from runner import (
    TaskResult,
    TimeoutError,
    TimeoutHandler,
    timeout_context,
    ensure_output_dirs,
    load_tasks,
    load_graph,
    run_task,
    run_batch,
    process_in_chunks_streaming,
)
from strategies.greedy import run_greedy_strategy, GreedyTraversal
from graph_utils import validate_graph, get_graph_statistics
from inference import LLMInferenceEngine
from config import get_model_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("greedy_runner")

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    return answer.strip().lower()

def load_tasks_from_graph(graph_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph JSON file.
    Expects the graph file to contain a list of tasks or a dict mapping task_id to graph data.
    For T019b, we assume the input graph file (from T011a-1b-serialize) contains
    a structure like: {"task_id": {"nodes": [...], "edges": [...], "question": "...", "answer": "..."}}
    or a list of such objects.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Input graph file not found: {graph_path}")

    with open(graph_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tasks = []
    if isinstance(data, dict):
        # Assume dict of task_id -> task_data
        for task_id, task_data in data.items():
            if isinstance(task_data, dict):
                tasks.append({
                    "task_id": task_id,
                    "context": task_data.get("context", ""),
                    "question": task_data.get("question", task_data.get("query", "")),
                    "answer": task_data.get("answer", ""),
                    "graph_data": task_data
                })
    elif isinstance(data, list):
        # Assume list of task objects
        for item in data:
            if isinstance(item, dict):
                tasks.append({
                    "task_id": item.get("task_id", str(len(tasks))),
                    "context": item.get("context", ""),
                    "question": item.get("question", item.get("query", "")),
                    "answer": item.get("answer", ""),
                    "graph_data": item
                })

    if not tasks:
        logger.warning("No tasks found in the input graph file.")

    return tasks

def evaluate_task(
    task: Dict[str, Any],
    graph: Any,
    inference_engine: LLMInferenceEngine,
    top_k: int,
    timeout_seconds: int
) -> TaskResult:
    """
    Evaluate a single task using the Greedy strategy.

    Returns a TaskResult object containing accuracy, nodes_visited, latency_ms, status, etc.
    """
    task_id = task.get("task_id", "unknown")
    question = task.get("question", "")
    ground_truth = task.get("answer", "")
    graph_data = task.get("graph_data", {})

    # Build the graph for this task if not already done
    # Assuming graph_data contains nodes and edges
    try:
        # Reconstruct graph if needed, or use the passed graph if it's a single graph for all tasks
        # For now, assume the passed 'graph' is the full graph or we extract subgraph
        # If the graph is a dict of task_id -> subgraph, we extract it here.
        # Given the runner logic, we assume 'graph' is the relevant subgraph for this task.
        current_graph = graph
        if isinstance(graph, dict) and task_id in graph:
            current_graph = graph[task_id]

        if current_graph is None:
            logger.warning(f"No graph data for task {task_id}. Marking as UNRESOLVED.")
            return TaskResult(
                task_id=task_id,
                accuracy=0.0,
                nodes_visited=0,
                latency_ms=0.0,
                status="UNRESOLVED",
                token_count=0,
                top_k=top_k,
                evidence_threshold=None
            )

        # Validate graph
        if not validate_graph(current_graph):
            logger.warning(f"Invalid graph for task {task_id}. Marking as DEGENERATE.")
            return TaskResult(
                task_id=task_id,
                accuracy=0.0,
                nodes_visited=0,
                latency_ms=0.0,
                status="DEGENERATE",
                token_count=0,
                top_k=top_k,
                evidence_threshold=None
            )

        start_time = time.time()
        
        # Run the greedy strategy with timeout
        with timeout_context(seconds=timeout_seconds):
            # Run the greedy traversal
            result = run_greedy_strategy(
                graph=current_graph,
                question=question,
                inference_engine=inference_engine,
                top_k=top_k
            )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract metrics from result
        # Expected result from run_greedy_strategy: {'accuracy': float, 'nodes_visited': int, 'latency_ms': float, 'top_k': int}
        accuracy = result.get("accuracy", 0.0)
        nodes_visited = result.get("nodes_visited", 0)
        
        # Determine status
        if accuracy is None or nodes_visited is None:
            status = "UNRESOLVED"
        else:
            status = "COMPLETED"

        # Estimate token count (approximate)
        # This is a placeholder; real implementation would track tokens in inference engine
        token_count = len(question.split()) + len(ground_truth.split())

        return TaskResult(
            task_id=task_id,
            accuracy=accuracy,
            nodes_visited=nodes_visited,
            latency_ms=latency_ms,
            status=status,
            token_count=token_count,
            top_k=top_k,
            evidence_threshold=None  # Greedy doesn't use evidence threshold
        )

    except TimeoutError:
        logger.warning(f"Task {task_id} timed out.")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=timeout_seconds * 1000.0,
            status="TIMEOUT",
            token_count=0,
            top_k=top_k,
            evidence_threshold=None
        )
    except Exception as e:
        logger.error(f"Error evaluating task {task_id}: {e}")
        return TaskResult(
            task_id=task_id,
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            status="ERROR",
            token_count=0,
            top_k=top_k,
            evidence_threshold=None
        )

def save_results_to_csv(results: List[TaskResult], output_path: str):
    """Save results to a CSV file conforming to the schema."""
    ensure_output_dirs(output_path)
    
    fieldnames = [
        "task_id", "accuracy", "nodes_visited", "latency_ms", 
        "status", "token_count", "top_k"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                "task_id": r.task_id,
                "accuracy": r.accuracy,
                "nodes_visited": r.nodes_visited,
                "latency_ms": r.latency_ms,
                "status": r.status,
                "token_count": r.token_count,
                "top_k": r.top_k
            })

    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Greedy Execution Runner (T019b)")
    parser.add_argument("--input", type=str, required=True, help="Path to input graph JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--topk", type=int, default=5, help="Number of top edges to consider")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (moderate default)")
    parser.add_argument("--model", type=str, default=None, help="Path to quantized model")
    
    args = parser.parse_args()

    # Validate timeout configuration
    if args.timeout <= 0:
        logger.warning("Invalid timeout value. Using default 300s.")
        args.timeout = 300

    logger.info(f"Starting Greedy Runner with top_k={args.topk}, timeout={args.timeout}s")

    # Load tasks from graph
    tasks = load_tasks_from_graph(args.input)
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        sys.exit(1)

    logger.info(f"Loaded {len(tasks)} tasks.")

    # Initialize LLM Inference Engine
    model_path = args.model or get_model_path()
    if not model_path or not os.path.exists(model_path):
        logger.warning("Model path not found. Using mock inference for demonstration.")
        # In a real scenario, this would fail loudly. For now, we proceed with a mock.
        # However, per T019b requirements, we must run real logic. 
        # If the model is missing, we should fail or use a fallback if allowed.
        # Since T012a is completed, we assume the engine can be initialized or a mock is used for testing.
        # We will attempt to initialize; if it fails, we log and proceed with mock if allowed by T012a.
        try:
            inference_engine = LLMInferenceEngine(model_path=model_path)
        except Exception as e:
            logger.error(f"Failed to initialize LLM engine: {e}")
            logger.error("Cannot proceed without a valid model. Exiting.")
            sys.exit(1)
    else:
        inference_engine = LLMInferenceEngine(model_path=model_path)

    # Load graph
    try:
        # The load_graph function from runner.py expects a path and returns a graph object.
        # We assume it handles the JSON structure appropriately.
        graph = load_graph(args.input)
        if graph is None:
            logger.error("Failed to load graph.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading graph: {e}")
        sys.exit(1)

    # Run batch evaluation
    results = []
    for task in tasks:
        result = evaluate_task(
            task=task,
            graph=graph,
            inference_engine=inference_engine,
            top_k=args.topk,
            timeout_seconds=args.timeout
        )
        results.append(result)
        logger.info(f"Processed task {task['task_id']}: {result.status}")

    # Save results
    save_results_to_csv(results, args.output)

    logger.info("Greedy Runner completed.")

if __name__ == "__main__":
    main()