import os
import sys
import csv
import logging
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.logging_utils import configure_logging
from rm_executor import ReflectiveMaskingExecutor

logger = logging.getLogger(__name__)

def load_failure_instances(input_path: str) -> List[Dict[str, Any]]:
    """
    Filter execution_log.csv for rows where convergence_status='timeout'.
    Returns the list of failure instances to be re-run.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    timeout_instances = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('convergence_status') == 'timeout':
                timeout_instances.append(row)
    
    logger.info(f"Loaded {len(timeout_instances)} timeout instances from {input_path}")
    return timeout_instances

def load_puzzle_metadata(puzzles_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the original puzzles JSONL to retrieve ground truth and graph structure.
    Returns a dict keyed by instance_id.
    """
    if not os.path.exists(puzzles_path):
        raise FileNotFoundError(f"Puzzles file not found: {puzzles_path}")
    
    puzzles = {}
    with open(puzzles_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                instance_id = data.get('instance_id')
                if instance_id:
                    puzzles[instance_id] = data
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON line: {e}")
    
    logger.info(f"Loaded {len(puzzles)} puzzles from {puzzles_path}")
    return puzzles

def re_run_extended_budget(
    timeout_instances: List[Dict[str, Any]],
    puzzle_metadata: Dict[str, Dict[str, Any]],
    model_path: str,
    extended_turns: int = 1000,
    batch_size: int = 4,
    device: str = "cpu"
) -> List[Dict[str, Any]]:
    """
    Re-run the Reflective Masking loop for timeout instances with an extended turn limit.
    """
    if not timeout_instances:
        logger.warning("No timeout instances to re-run.")
        return []

    executor = ReflectiveMaskingExecutor(
        model_path=model_path,
        max_turns=extended_turns,
        device=device
    )
    
    results = []
    start_time = time.time()
    
    logger.info(f"Starting extended budget run for {len(timeout_instances)} instances (limit={extended_turns})")
    
    # Process in batches to manage memory, though we are re-running one by one logically
    # We group by instance_id to ensure we have the text
    batch = []
    for idx, instance in enumerate(timeout_instances):
        instance_id = instance.get('instance_id')
        puzzle_data = puzzle_metadata.get(instance_id)
        
        if not puzzle_data:
            logger.error(f"Puzzle metadata missing for instance_id: {instance_id}")
            continue
        
        text = puzzle_data.get('text')
        if not text:
            logger.error(f"Missing 'text' in puzzle metadata for {instance_id}")
            continue

        batch.append((instance_id, text))
        
        # Process batch
        if len(batch) >= batch_size or idx == len(timeout_instances) - 1:
            for bid, btext in batch:
                try:
                    run_result = executor.execute(btext)
                    run_result['instance_id'] = bid
                    # Preserve original metadata if needed, but primarily we care about the new run
                    results.append(run_result)
                except Exception as e:
                    logger.error(f"Execution failed for {bid}: {e}")
                    # Record a failure for this instance in the extended log
                    results.append({
                        'instance_id': bid,
                        'turns_to_converge': extended_turns,
                        'convergence_status': 'timeout',
                        'path_coverage': 0.0,
                        'divergence_from_ground_truth': 1.0,
                        'error': str(e)
                    })
            batch = []
    
    elapsed = time.time() - start_time
    logger.info(f"Extended budget run completed in {elapsed:.2f} seconds. Processed {len(results)} instances.")
    return results

def write_extended_log(results: List[Dict[str, Any]], output_path: str):
    """
    Write the extended budget results to CSV.
    """
    if not results:
        logger.warning("No results to write.")
        # Write empty file with headers to ensure file exists
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'instance_id', 'turns_to_converge', 'convergence_status',
                'path_coverage', 'divergence_from_ground_truth'
            ])
            writer.writeheader()
        return

    fieldnames = [
        'instance_id', 'turns_to_converge', 'convergence_status',
        'path_coverage', 'divergence_from_ground_truth'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Ensure all fields are present, fill defaults if missing
            safe_row = {k: row.get(k, '') for k in fieldnames}
            # Ensure numeric fields are numeric
            if 'turns_to_converge' in safe_row:
                try:
                    safe_row['turns_to_converge'] = int(safe_row['turns_to_converge'])
                except (ValueError, TypeError):
                    safe_row['turns_to_converge'] = 0
            if 'path_coverage' in safe_row:
                try:
                    safe_row['path_coverage'] = float(safe_row['path_coverage'])
                except (ValueError, TypeError):
                    safe_row['path_coverage'] = 0.0
            if 'divergence_from_ground_truth' in safe_row:
                try:
                    safe_row['divergence_from_ground_truth'] = float(safe_row['divergence_from_ground_truth'])
                except (ValueError, TypeError):
                    safe_row['divergence_from_ground_truth'] = 0.0
            writer.writerow(safe_row)
    
    logger.info(f"Wrote {len(results)} results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Extended Budget Validation Run")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to execution_log.csv (contains timeouts)")
    parser.add_argument("--puzzles", type=str, required=True,
                        help="Path to logical_puzzles.jsonl (metadata)")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to output extended_budget_log.csv")
    parser.add_argument("--model-path", type=str, default=None,
                        help="Path to the Mask Diffusion Model (from .env if None)")
    parser.add_argument("--max-turns", type=int, default=1000,
                        help="Extended turn limit")
    parser.add_argument("--batch-size", type=int, default=4,
                        help="Batch size for processing")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device to run on (cpu/cuda)")
    
    args = parser.parse_args()
    configure_logging()

    # Load model path from env if not provided
    model_path = args.model_path
    if not model_path:
        from dotenv import load_dotenv
        load_dotenv()
        model_path = os.getenv("MODEL_PATH")
        if not model_path:
            logger.error("MODEL_PATH not set in .env and not provided via argument.")
            sys.exit(1)

    logger.info(f"Starting Extended Budget Run. Model: {model_path}, Limit: {args.max_turns}")

    # 1. Load timeout instances
    timeout_instances = load_failure_instances(args.input)
    if not timeout_instances:
        logger.warning("No timeout instances found. Creating empty output file.")
        write_extended_log([], args.output)
        return

    # 2. Load puzzle metadata
    puzzle_metadata = load_puzzle_metadata(args.puzzles)

    # 3. Re-run with extended budget
    results = re_run_extended_budget(
        timeout_instances,
        puzzle_metadata,
        model_path=model_path,
        extended_turns=args.max_turns,
        batch_size=args.batch_size,
        device=args.device
    )

    # 4. Write results
    write_extended_log(results, args.output)
    
    # Verification
    if len(results) == len(timeout_instances):
        logger.info("Verification: Row count matches filtered input count.")
    else:
        logger.warning(f"Verification Mismatch: Input {len(timeout_instances)}, Output {len(results)}")

if __name__ == "__main__":
    main()
