import os
import time
import signal
import logging
import csv
import json
import argparse
import sys
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import strategies
from strategies.full import run_full_strategy
from strategies.lazy import run_lazy_strategy
from strategies.greedy import run_greedy_strategy

# Import data utilities
from data_loader import load_graphs, load_noisy_graphs, stream_locomo_tasks
from utils.time import get_current_time
from config import get_model_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

class TimeoutHandler:
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.old_handler = None

    def _handler(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        self.old_handler = signal.signal(signal.SIGALRM, self._handler)
        signal.alarm(self.timeout_seconds)
        return self

    def __exit__(self, type, value, traceback):
        signal.alarm(0)
        if self.old_handler:
            signal.signal(signal.SIGALRM, self.old_handler)

class TaskResult:
    def __init__(self, task_id: str, strategy: str, accuracy: float, 
                 nodes_visited: int, latency_ms: float, status: str, 
                 extra_fields: Optional[Dict[str, Any]] = None):
        self.task_id = task_id
        self.strategy = strategy
        self.accuracy = accuracy
        self.nodes_visited = nodes_visited
        self.latency_ms = latency_ms
        self.status = status
        self.extra_fields = extra_fields or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "strategy": self.strategy,
            "accuracy": self.accuracy,
            "nodes_visited": self.nodes_visited,
            "latency_ms": self.latency_ms,
            "status": self.status,
            **self.extra_fields
        }

def ensure_output_dirs(output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """Load tasks from JSONL or JSON file."""
    tasks = []
    if input_path.endswith('.jsonl'):
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
    elif input_path.endswith('.json'):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                tasks = data
            elif isinstance(data, dict):
                tasks = [data]
    else:
        raise ValueError(f"Unsupported input format: {input_path}")
    return tasks

def load_graph(graph_path: str, is_noisy: bool = False) -> Dict[str, Any]:
    """Load graph data based on whether it's noisy or clean."""
    if is_noisy:
        return load_noisy_graphs(graph_path)
    else:
        return load_graphs(graph_path)

def run_task(task: Dict[str, Any], graph_data: Dict[str, Any], 
             strategy: str, threshold: Optional[float] = None, 
             topk: Optional[int] = None, timeout: int = 300) -> TaskResult:
    """Execute a single task with the specified strategy."""
    task_id = task.get('task_id', 'unknown')
    context = task.get('context', '')
    question = task.get('question', '')
    ground_truth = task.get('answer', '')

    # Determine strategy function
    strategy_map = {
        'full': run_full_strategy,
        'lazy': run_lazy_strategy,
        'greedy': run_greedy_strategy
    }

    if strategy not in strategy_map:
        raise ValueError(f"Unknown strategy: {strategy}")

    strategy_func = strategy_map[strategy]

    # Prepare strategy kwargs
    strategy_kwargs = {
        'question': question,
        'context': context,
        'ground_truth': ground_truth,
        'graph_data': graph_data,
        'task_id': task_id
    }

    if strategy == 'lazy' and threshold is not None:
        strategy_kwargs['threshold'] = threshold
    elif strategy == 'greedy' and topk is not None:
        strategy_kwargs['topk'] = topk

    start_time = time.time()
    status = "COMPLETED"
    accuracy = 0.0
    nodes_visited = 0
    extra_fields = {}

    try:
        with TimeoutHandler(timeout):
            result = strategy_func(**strategy_kwargs)
            
            if isinstance(result, dict):
                accuracy = result.get('accuracy', 0.0)
                nodes_visited = result.get('nodes_visited', 0)
                status = result.get('status', 'COMPLETED')
                extra_fields = {k: v for k, v in result.items() 
                               if k not in ['accuracy', 'nodes_visited', 'status']}
            else:
                # Handle case where result might be a tuple or other format
                if hasattr(result, 'accuracy'):
                    accuracy = result.accuracy
                if hasattr(result, 'nodes_visited'):
                    nodes_visited = result.nodes_visited
                if hasattr(result, 'status'):
                    status = result.status

    except TimeoutError:
        status = "TIMEOUT"
        logger.warning(f"Task {task_id} timed out")
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {str(e)}")
        status = "ERROR"
        accuracy = 0.0
        nodes_visited = 0

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    return TaskResult(
        task_id=task_id,
        strategy=strategy,
        accuracy=accuracy,
        nodes_visited=nodes_visited,
        latency_ms=latency_ms,
        status=status,
        extra_fields=extra_fields
    )

def run_batch(tasks: List[Dict[str, Any]], graph_data: Dict[str, Any],
              strategy: str, output_path: str, threshold: Optional[float] = None,
              topk: Optional[int] = None, timeout: int = 300,
              streaming: bool = False, chunk_size: int = 10) -> None:
    """Run a batch of tasks and save results to CSV."""
    ensure_output_dirs(output_path)

    # Define CSV fieldnames
    fieldnames = ['task_id', 'strategy', 'accuracy', 'nodes_visited', 
                 'latency_ms', 'status']
    
    # Add strategy-specific fields
    if strategy == 'lazy':
        fieldnames.append('evidence_threshold')
    elif strategy == 'greedy':
        fieldnames.append('topk')

    results = []
    processed_count = 0

    for i, task in enumerate(tasks):
        if streaming and i > 0 and i % chunk_size == 0:
            gc.collect()
            logger.info(f"Processed {i} tasks, forcing garbage collection")

        result = run_task(task, graph_data, strategy, threshold, topk, timeout)
        results.append(result.to_dict())
        processed_count += 1

        logger.info(f"Completed task {i+1}/{len(tasks)}: {result.task_id} - {result.status}")

    # Write results to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = result.copy()
            
            # Format strategy-specific fields
            if strategy == 'lazy' and 'evidence_threshold' not in row:
                row['evidence_threshold'] = f"{threshold:.2f}" if threshold is not None else "0.00"
            elif strategy == 'greedy' and 'topk' not in row:
                row['topk'] = topk if topk is not None else 0
            
            writer.writerow(row)

    logger.info(f"Saved {len(results)} results to {output_path}")

def process_in_chunks_streaming(graph_data: Dict[str, Any], strategy: str,
                                output_path: str, threshold: Optional[float] = None,
                                topk: Optional[int] = None, timeout: int = 300,
                                chunk_size: int = 10) -> None:
    """Process tasks in streaming mode to handle large datasets."""
    ensure_output_dirs(output_path)
    
    # Define CSV fieldnames
    fieldnames = ['task_id', 'strategy', 'accuracy', 'nodes_visited', 
                 'latency_ms', 'status']
    
    if strategy == 'lazy':
        fieldnames.append('evidence_threshold')
    elif strategy == 'greedy':
        fieldnames.append('topk')

    # Open file for writing
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        task_count = 0
        for task_chunk in stream_locomo_tasks(chunk_size=chunk_size):
            for task in task_chunk:
                result = run_task(task, graph_data, strategy, threshold, topk, timeout)
                row = result.to_dict()
                
                # Format strategy-specific fields
                if strategy == 'lazy' and 'evidence_threshold' not in row:
                    row['evidence_threshold'] = f"{threshold:.2f}" if threshold is not None else "0.00"
                elif strategy == 'greedy' and 'topk' not in row:
                    row['topk'] = topk if topk is not None else 0
                
                writer.writerow(row)
                task_count += 1
                logger.info(f"Processed task {task_count}: {result.task_id}")

            # Force garbage collection after each chunk
            gc.collect()

    logger.info(f"Streamed and saved {task_count} results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Run memory reconstruction strategies')
    parser.add_argument('--strategy', type=str, required=True, 
                      choices=['full', 'lazy', 'greedy'],
                      help='Traversal strategy to use')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to input tasks (JSONL or JSON)')
    parser.add_argument('--graph', type=str, required=True,
                      help='Path to graph data (JSON)')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output CSV file')
    parser.add_argument('--threshold', type=float, default=0.7,
                      help='Evidence threshold for lazy strategy')
    parser.add_argument('--topk', type=int, default=5,
                      help='Top-k edges for greedy strategy')
    parser.add_argument('--timeout', type=int, default=300,
                      help='Timeout in seconds per task')
    parser.add_argument('--streaming', action='store_true',
                      help='Use streaming mode for large datasets')
    parser.add_argument('--chunk-size', type=int, default=10,
                      help='Chunk size for streaming')
    parser.add_argument('--noisy', action='store_true',
                      help='Use noisy graph data')

    args = parser.parse_args()

    logger.info(f"Starting {args.strategy} strategy run")
    logger.info(f"Input tasks: {args.input}")
    logger.info(f"Graph data: {args.graph}")
    logger.info(f"Output: {args.output}")

    # Load graph data
    try:
        graph_data = load_graph(args.graph, is_noisy=args.noisy)
        logger.info(f"Loaded graph with {len(graph_data)} tasks")
    except Exception as e:
        logger.error(f"Failed to load graph: {str(e)}")
        sys.exit(1)

    # Run batch or streaming
    if args.streaming:
        process_in_chunks_streaming(
            graph_data=graph_data,
            strategy=args.strategy,
            output_path=args.output,
            threshold=args.threshold,
            topk=args.topk,
            timeout=args.timeout,
            chunk_size=args.chunk_size
        )
    else:
        # Load tasks
        try:
            tasks = load_tasks(args.input)
            logger.info(f"Loaded {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"Failed to load tasks: {str(e)}")
            sys.exit(1)

        run_batch(
            tasks=tasks,
            graph_data=graph_data,
            strategy=args.strategy,
            output_path=args.output,
            threshold=args.threshold,
            topk=args.topk,
            timeout=args.timeout
        )

    logger.info("Run completed successfully")

if __name__ == '__main__':
    main()
