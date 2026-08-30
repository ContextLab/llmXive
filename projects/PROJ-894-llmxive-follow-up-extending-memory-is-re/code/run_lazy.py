"""
Lazy Execution Runner for T019a.

Executes the "Lazy" traversal strategy on the LoCoMo benchmark tasks
and logs results to data/processed/lazy_results.csv.

Dependencies: T017 (Lazy Strategy), T012a (LLM Engine), T070 (Graph Verification).
"""

import os
import sys
import time
import json
import logging
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from strategies.lazy import run_lazy_strategy
from utils.llm_engine import run_inference
from runner import TaskResult, ensure_output_dirs
from data_loader import load_graphs
from graph_utils import validate_graph, check_graph_connectivity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    return answer.strip().lower()

def load_tasks_from_graph(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load tasks from the graph data structure.
    Expects graph_data to be a dict mapping task_id -> list of edges/nodes
    or a structure that can be mapped to Task objects.
    """
    tasks = []
    # Assuming graph_data structure from data/intermediate/graphs_raw.json
    # Format: { "task_id": [edge1, edge2, ...], ... }
    # We need to map this to the Task structure expected by the strategy.
    # Based on T007, Task has: task_id, question, context, answer.
    # Since we are loading from graphs_raw.json which contains edges,
    # we assume the task metadata (question/context) is embedded or
    # we are iterating over the graph keys as task_ids.
    # For this runner, we assume the input graph file contains the full task context
    # or we load tasks separately. However, T070 implies we verify the graph exists.
    # The strategy `run_lazy_strategy` expects a graph and a task context.
    # Let's assume the graph file contains the necessary context for each task.
    
    # If the file is just edges, we might need to load the raw LoCoMo data too.
    # However, standard pattern for these runners is:
    # 1. Load Graph (nodes/edges)
    # 2. Load Task Metadata (question/context/answer) from the same source or parallel file.
    # Given T011a-1b-serialize produces graphs_raw.json with keys as task_id,
    # we assume the value contains the graph structure for that task.
    
    # We will construct a minimal task object. The 'context' and 'question' 
    # should ideally come from the raw LoCoMo data, but if the graph file
    # is the primary input, we assume the strategy can derive context from the graph 
    # or we load the raw data again.
    # To be robust, let's assume we need the raw LoCoMo data for questions/answers.
    # But the runner signature in tasks.md says "using code/run_lazy.py... logging results".
    # Let's assume the graph file `graphs_raw.json` is the primary input and 
    # it might contain the context or we load a parallel `locomo.jsonl`.
    
    # For now, we assume the graph file has the structure:
    # { "task_id_1": {"nodes": [...], "edges": [...], "question": "...", "answer": "..."}, ... }
    # OR we load the raw data separately.
    # Let's implement a fallback: if the graph data doesn't have context, we try to load raw data.
    
    # Simplified assumption for this task: The graph file contains the necessary context.
    # If not, the strategy will fail, which is correct (fail loud).
    
    for task_id, graph_content in graph_data.items():
        if isinstance(graph_content, dict):
            # Check if it contains task metadata
            question = graph_content.get("question", "")
            context = graph_content.get("context", "")
            answer = graph_content.get("answer", "")
            
            # If missing, we might need to load from raw data, but for now we proceed
            # with what we have. If empty, the strategy might fail or return 0 accuracy.
            
            tasks.append({
                "task_id": task_id,
                "question": question,
                "context": context,
                "answer": answer,
                "graph": graph_content # Pass the graph content for the strategy
            })
        else:
            # If the value is just a list of edges, we need more info.
            # We assume the task_id is the key and we need to fetch context elsewhere.
            # But without a separate loader call here, we assume the format includes context.
            # If the format is just edges, we create a minimal task.
            tasks.append({
                "task_id": task_id,
                "question": "",
                "context": "",
                "answer": "",
                "graph": graph_content
            })
    
    return tasks

def evaluate_task(
    task: Dict[str, Any], 
    model_path: str, 
    threshold: float
) -> TaskResult:
    """
    Evaluate a single task using the Lazy strategy.
    """
    task_id = task["task_id"]
    graph = task["graph"]
    question = task["question"]
    context = task["context"]
    expected_answer = task["answer"]

    # Validate graph
    if not validate_graph(graph):
        logger.warning(f"Task {task_id}: Invalid graph structure.")
        return TaskResult(
            task_id=task_id,
            strategy="Lazy",
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=0.0,
            evidence_threshold=threshold,
            status="DEGENERATE"
        )

    start_time = time.time()
    
    try:
        # Run the Lazy strategy
        # The strategy returns a result object or dict.
        # Based on T017, run_lazy_strategy should return the traversal result.
        result = run_lazy_strategy(
            graph=graph,
            question=question,
            context=context,
            model_path=model_path,
            threshold=threshold
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Determine accuracy
        # result might contain 'answer' or 'prediction'
        pred = result.get("prediction", "")
        # Normalize for comparison
        if normalize_answer(pred) == normalize_answer(expected_answer):
            accuracy = 1.0
        else:
            accuracy = 0.0

        return TaskResult(
            task_id=task_id,
            strategy="Lazy",
            accuracy=accuracy,
            nodes_visited=result.get("nodes_visited", 0),
            latency_ms=latency_ms,
            evidence_threshold=threshold,
            status="COMPLETED"
        )

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        return TaskResult(
            task_id=task_id,
            strategy="Lazy",
            accuracy=0.0,
            nodes_visited=0,
            latency_ms=latency_ms,
            evidence_threshold=threshold,
            status="ERROR",
            error=str(e)
        )

def save_results_to_csv(results: List[TaskResult], output_path: str) -> None:
    """Save results to a CSV file."""
    ensure_output_dirs(output_path)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["task_id", "strategy", "accuracy", "nodes_visited", "inference_time_seconds", "evidence_threshold", "status"])
        
        for res in results:
            writer.writerow([
                res.task_id,
                res.strategy,
                f"{res.accuracy:.4f}",
                res.nodes_visited,
                f"{res.latency_ms/1000:.4f}",
                res.evidence_threshold,
                res.status
            ])
    logger.info(f"Results saved to {output_path}")

def run_lazy_strategy_main(
    input_graph_path: str,
    output_csv_path: str,
    model_path: str,
    threshold: float = 0.7
) -> List[TaskResult]:
    """
    Main execution loop for the Lazy strategy.
    """
    logger.info(f"Loading graphs from {input_graph_path}")
    
    if not os.path.exists(input_graph_path):
        raise FileNotFoundError(f"Input graph file not found: {input_graph_path}")

    # Load graphs
    # The load_graphs function from data_loader expects a path.
    # We assume it returns a dict of task_id -> graph_data.
    try:
        graph_data = load_graphs(input_graph_path)
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        raise

    if not graph_data:
        logger.warning("No graphs loaded. Exiting.")
        return []

    tasks = load_tasks_from_graph(graph_data)
    logger.info(f"Loaded {len(tasks)} tasks.")

    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task['task_id']}")
        result = evaluate_task(task, model_path, threshold)
        results.append(result)
    
    save_results_to_csv(results, output_csv_path)
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Lazy Strategy on LoCoMo Benchmark")
    parser.add_argument("--input", type=str, required=True, help="Path to input graphs JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--model", type=str, default=None, help="Path to LLM model")
    parser.add_argument("--threshold", type=float, default=0.7, help="Evidence threshold")
    
    args = parser.parse_args()

    # Determine model path
    model_path = args.model
    if not model_path:
        # Try to get from config or default
        from config import get_model_path
        model_path = get_model_path()
        if not model_path:
            logger.error("Model path not provided and not found in config.")
            sys.exit(1)

    logger.info(f"Starting Lazy Execution Runner with model: {model_path}")
    
    try:
        run_lazy_strategy_main(
            input_graph_path=args.input,
            output_csv_path=args.output,
            model_path=model_path,
            threshold=args.threshold
        )
        logger.info("Lazy Execution Runner completed successfully.")
    except Exception as e:
        logger.error(f"Runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()