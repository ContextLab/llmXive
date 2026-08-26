"""
Lazy Strategy Execution Runner.

Executes the Lazy traversal strategy on provided tasks and graphs,
logging results including evidence_threshold to data/processed/lazy_results.csv.
"""
import os
import sys
import time
import logging
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project imports
from strategies.lazy import run_lazy_strategy, LazyTraversal
from runner import TimeoutHandler, TimeoutError, TaskResult, load_graph
from config import get_model_path, get_huggingface_cache_dir
from graph_utils import validate_graph, get_graph_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dirs(output_path: str) -> Path:
    """Ensure the directory for the output file exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def normalize_answer(answer: str) -> str:
    """Normalize answer string for comparison."""
    if not answer:
        return ""
    return answer.strip().lower()

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """Load tasks from a JSONL or JSON file."""
    tasks = []
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if path.suffix == '.jsonl':
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    elif path.suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                tasks = data
            elif isinstance(data, dict):
                tasks = [data]
    else:
        raise ValueError(f"Unsupported input format: {path.suffix}")
    
    if not tasks:
        raise ValueError(f"No tasks found in {input_path}")
    
    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    return tasks

def evaluate_task(
    task: Dict[str, Any], 
    graph: Any, 
    strategy: str = "lazy",
    threshold: float = 0.7,
    timeout: int = 1800
) -> Dict[str, Any]:
    """
    Evaluate a single task using the Lazy strategy.
    
    Returns a dictionary with results including evidence_threshold.
    """
    task_id = task.get('task_id', task.get('id', 'unknown'))
    question = task.get('question', '')
    context = task.get('context', '')
    answer = task.get('answer', '')
    
    start_time = time.time()
    status = "COMPLETED"
    accuracy = 0.0
    nodes_visited = 0
    token_count = 0
    evidence_threshold_used = threshold
    
    try:
        # Run the lazy strategy
        result = run_lazy_strategy(
            graph=graph,
            question=question,
            context=context,
            threshold=threshold
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        nodes_visited = result.get('nodes_visited', 0)
        token_count = result.get('token_count', 0)
        evidence_threshold_used = result.get('evidence_threshold', threshold)
        
        # Check answer
        predicted = result.get('predicted_answer', '')
        if normalize_answer(predicted) == normalize_answer(answer):
            accuracy = 1.0
        else:
            accuracy = 0.0
            
        status = result.get('status', 'COMPLETED')
        
    except TimeoutError as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        status = "TIMEOUT"
        logger.warning(f"Task {task_id} timed out after {timeout}s")
        
    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        status = "ERROR"
        logger.error(f"Task {task_id} failed with error: {str(e)}")
        accuracy = 0.0
        nodes_visited = 0
    
    return {
        'task_id': task_id,
        'accuracy': accuracy,
        'nodes_visited': nodes_visited,
        'latency_ms': latency_ms,
        'status': status,
        'token_count': token_count,
        'evidence_threshold': evidence_threshold_used
    }

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """Save results to a CSV file."""
    if not results:
        logger.warning("No results to save.")
        return
    
    fieldnames = [
        'task_id', 'accuracy', 'nodes_visited', 'latency_ms', 
        'status', 'token_count', 'evidence_threshold'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Lazy Strategy Evaluation")
    parser.add_argument('--input', required=True, help='Path to input tasks (JSON/JSONL)')
    parser.add_argument('--graph', required=True, help='Path to graph file (JSON)')
    parser.add_argument('--output', required=True, help='Path to output CSV')
    parser.add_argument('--threshold', type=float, default=0.7, help='Evidence threshold for lazy traversal')
    parser.add_argument('--timeout', type=int, default=1800, help='Timeout in seconds per task')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    try:
        # Ensure output directory exists
        output_path = ensure_output_dirs(args.output)
        
        # Load tasks
        tasks = load_tasks(args.input)
        
        # Load graph
        logger.info(f"Loading graph from {args.graph}")
        graph = load_graph(args.graph)
        
        if not validate_graph(graph):
            logger.error("Graph validation failed. Cannot proceed.")
            sys.exit(1)
        
        # Run evaluation
        results = []
        for i, task in enumerate(tasks):
            logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id', 'unknown')}")
            result = evaluate_task(
                task=task,
                graph=graph,
                strategy="lazy",
                threshold=args.threshold,
                timeout=args.timeout
            )
            results.append(result)
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Completed {i+1}/{len(tasks)} tasks")
        
        # Save results
        save_results_to_csv(results, str(output_path))
        
        # Summary
        completed = sum(1 for r in results if r['status'] == 'COMPLETED')
        avg_accuracy = sum(r['accuracy'] for r in results) / len(results) if results else 0.0
        avg_nodes = sum(r['nodes_visited'] for r in results) / len(results) if results else 0.0
        
        logger.info(f"Summary: {completed}/{len(results)} completed, Avg Accuracy: {avg_accuracy:.4f}, Avg Nodes: {avg_nodes:.2f}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()