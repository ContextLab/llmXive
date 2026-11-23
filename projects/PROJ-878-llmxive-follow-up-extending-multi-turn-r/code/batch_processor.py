"""
Batch processing logic for Reflective Masking Executor to stay within RAM constraints.

This module implements streaming and batched processing of logical puzzles
to ensure memory efficiency when running on large datasets.
"""
import json
import csv
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Generator, Any
from dataclasses import dataclass
import gc

from utils.logging_utils import configure_logging, log_experiment_metadata

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 10
    max_memory_mb: Optional[int] = None
    stream_input: bool = True
    output_path: str = "data/processed/execution_log.csv"
    checkpoint_interval: int = 50

def stream_puzzles(input_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Stream puzzles from a JSONL file one at a time to minimize memory usage.
    
    Args:
        input_path: Path to the JSONL file containing puzzles
        
    Yields:
        Individual puzzle dictionaries
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                puzzle = json.loads(line)
                yield puzzle
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse line {line_num}: {e}")
                continue

def process_batch(
    batch: List[Dict[str, Any]],
    executor: Any,
    config: BatchConfig
) -> List[Dict[str, Any]]:
    """
    Process a batch of puzzles using the provided executor.
    
    Args:
        batch: List of puzzle dictionaries to process
        executor: ReflectiveMaskingExecutor instance
        config: Batch processing configuration
        
    Returns:
        List of result dictionaries
    """
    results = []
    for i, puzzle in enumerate(batch):
        instance_id = puzzle.get('instance_id', f'unknown_{i}')
        try:
            logger.info(f"Processing {instance_id} in batch...")
            result = executor.execute(puzzle)
            result['instance_id'] = instance_id
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {instance_id}: {e}")
            results.append({
                'instance_id': instance_id,
                'turns_to_converge': None,
                'convergence_status': 'error',
                'path_coverage': None,
                'divergence_from_ground_truth': None,
                'error_message': str(e)
            })
    return results

def write_results(results: List[Dict[str, Any]], output_path: str, append: bool = False):
    """
    Write results to CSV file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
        append: Whether to append to existing file
    """
    mode = 'a' if append else 'w'
    write_header = not append
    
    with open(output_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        if write_header:
            writer.writeheader()
        writer.writerows(results)

def run_batched_execution(
    input_path: str,
    output_path: str,
    executor_factory: callable,
    config: Optional[BatchConfig] = None
) -> Dict[str, Any]:
    """
    Run batched execution of puzzles with memory constraints.
    
    This function:
    1. Streams puzzles from input file
    2. Processes them in batches
    3. Writes results incrementally to avoid memory buildup
    4. Performs garbage collection between batches
    
    Args:
        input_path: Path to input JSONL file
        output_path: Path to output CSV file
        executor_factory: Callable that returns a new executor instance
        config: Batch processing configuration
        
    Returns:
        Summary statistics of the execution
    """
    if config is None:
        config = BatchConfig()
    
    configure_logging()
    log_experiment_metadata("batched_execution", {
        "input_path": input_path,
        "output_path": output_path,
        "batch_size": config.batch_size,
        "stream_input": config.stream_input
    })
    
    logger.info(f"Starting batched execution: {input_path} -> {output_path}")
    logger.info(f"Batch size: {config.batch_size}, Stream input: {config.stream_input}")
    
    total_puzzles = 0
    processed_puzzles = 0
    start_time = time.time()
    current_batch = []
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Clear output file if not appending
    if not Path(output_path).exists():
        write_results([], output_path)
    
    puzzle_stream = stream_puzzles(input_path)
    
    for puzzle in puzzle_stream:
        current_batch.append(puzzle)
        total_puzzles += 1
        
        # Process when batch is full
        if len(current_batch) >= config.batch_size:
            logger.info(f"Processing batch of {len(current_batch)} puzzles...")
            
            executor = executor_factory()
            batch_results = process_batch(current_batch, executor, config)
            
            # Write results for this batch
            write_results(batch_results, output_path, append=True)
            
            processed_puzzles += len(batch_results)
            current_batch = []
            
            # Force garbage collection to free memory
            del executor
            gc.collect()
            
            # Log progress
            elapsed = time.time() - start_time
            rate = processed_puzzles / elapsed if elapsed > 0 else 0
            logger.info(f"Processed {processed_puzzles}/{total_puzzles} puzzles "
                      f"({rate:.2f} puzzles/sec)")
    
    # Process remaining puzzles in the last batch
    if current_batch:
        logger.info(f"Processing final batch of {len(current_batch)} puzzles...")
        
        executor = executor_factory()
        batch_results = process_batch(current_batch, executor, config)
        
        write_results(batch_results, output_path, append=True)
        
        processed_puzzles += len(batch_results)
        del executor
        gc.collect()
    
    total_time = time.time() - start_time
    summary = {
        "total_puzzles": total_puzzles,
        "processed_puzzles": processed_puzzles,
        "total_time_seconds": total_time,
        "puzzles_per_second": processed_puzzles / total_time if total_time > 0 else 0,
        "batch_size": config.batch_size
    }
    
    logger.info(f"Batched execution complete: {summary}")
    return summary

def main():
    """Main entry point for batch processing."""
    import sys
    
    # Default paths
    input_path = "data/raw/logical_puzzles.jsonl"
    output_path = "data/processed/execution_log.csv"
    batch_size = 10
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        batch_size = int(sys.argv[3])
    
    # Check if input file exists
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Import executor here to avoid circular imports
    from rm_executor import ReflectiveMaskingExecutor
    
    def executor_factory():
        return ReflectiveMaskingExecutor()
    
    config = BatchConfig(
        batch_size=batch_size,
        stream_input=True,
        output_path=output_path
    )
    
    try:
        summary = run_batched_execution(
            input_path=input_path,
            output_path=output_path,
            executor_factory=executor_factory,
            config=config
        )
        logger.info(f"Successfully processed {summary['processed_puzzles']} puzzles")
    except Exception as e:
        logger.error(f"Batched execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
