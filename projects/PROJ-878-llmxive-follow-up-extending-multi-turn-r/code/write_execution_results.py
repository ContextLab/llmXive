import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# Import existing utilities from the project API surface
from utils.logging_utils import configure_logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_execution_log(path: str) -> List[Dict[str, Any]]:
    """Load execution log from JSONL format."""
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results

def load_puzzle_metadata(path: str) -> Dict[str, Dict[str, Any]]:
    """Load puzzle metadata from JSONL format and index by instance_id."""
    puzzles = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                instance_id = data.get('instance_id')
                if instance_id:
                    puzzles[instance_id] = data
    return puzzles

def calculate_path_coverage(model_path: List[str], ground_truth_path: List[str]) -> float:
    """
    Calculate path coverage: fraction of ground truth nodes covered by model path.
    Returns a float between 0.0 and 1.0.
    """
    if not ground_truth_path:
        return 0.0 if not model_path else 1.0
    
    model_set = set(model_path)
    ground_truth_set = set(ground_truth_path)
    
    intersection = model_set.intersection(ground_truth_set)
    coverage = len(intersection) / len(ground_truth_set)
    return float(coverage)

def calculate_jaccard_distance(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate Jaccard distance between two sets.
    Jaccard Distance = 1 - (|A ∩ B| / |A ∪ B|)
    """
    if not set_a and not set_b:
        return 0.0
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
    
    return float(1.0 - (intersection / union))

def process_execution_results(
    execution_log_path: str,
    puzzle_metadata_path: str,
    output_path: str
) -> None:
    """
    Process execution results, calculate metrics, and write to CSV.
    
    Required CSV columns:
    - instance_id
    - turns_to_converge
    - convergence_status (values: 'success', 'timeout', or 'ilv_fail')
    - path_coverage
    - divergence_from_ground_truth (Jaccard distance)
    """
    # Load data
    logger.info(f"Loading execution log from {execution_log_path}")
    execution_results = load_execution_log(execution_log_path)
    
    logger.info(f"Loading puzzle metadata from {puzzle_metadata_path}")
    puzzle_metadata = load_puzzle_metadata(puzzle_metadata_path)
    
    if not execution_results:
        raise ValueError("Execution log is empty. Cannot process results.")
    
    if not puzzle_metadata:
        raise ValueError("Puzzle metadata is empty. Cannot process results.")
    
    # Prepare output rows
    output_rows = []
    
    for result in execution_results:
        instance_id = result.get('instance_id')
        
        if not instance_id:
            logger.warning(f"Skipping result without instance_id: {result}")
            continue
        
        if instance_id not in puzzle_metadata:
            logger.warning(f"Instance {instance_id} not found in puzzle metadata. Skipping.")
            continue
        
        puzzle = puzzle_metadata[instance_id]
        ground_truth_path = puzzle.get('ground_truth_path', [])
        
        # Extract execution metrics
        turns_to_converge = result.get('turns_to_converge')
        convergence_status = result.get('convergence_status', 'unknown')
        
        # Get model path if available
        model_path = result.get('model_path', [])
        
        # Calculate path coverage
        path_coverage = calculate_path_coverage(model_path, ground_truth_path)
        
        # Calculate Jaccard distance for divergence
        model_set = set(model_path)
        ground_truth_set = set(ground_truth_path)
        divergence_score = calculate_jaccard_distance(model_set, ground_truth_set)
        
        # Build output row
        row = {
            'instance_id': instance_id,
            'turns_to_converge': turns_to_converge,
            'convergence_status': convergence_status,
            'path_coverage': round(path_coverage, 6),
            'divergence_from_ground_truth': round(divergence_score, 6)
        }
        
        output_rows.append(row)
    
    # Validate critical fields
    critical_fields = ['instance_id', 'turns_to_converge', 'convergence_status']
    for i, row in enumerate(output_rows):
        for field in critical_fields:
            if row.get(field) is None:
                logger.error(f"Row {i} missing critical field: {field}")
                raise ValueError(f"Critical field '{field}' is null in row {i}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    fieldnames = [
        'instance_id',
        'turns_to_converge',
        'convergence_status',
        'path_coverage',
        'divergence_from_ground_truth'
    ]
    
    logger.info(f"Writing {len(output_rows)} rows to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    logger.info(f"Successfully wrote execution results to {output_path}")

def main():
    """Main entry point for writing execution results."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Write execution results to CSV with metrics")
    parser.add_argument(
        '--execution-log',
        required=True,
        help="Path to input execution log JSONL file"
    )
    parser.add_argument(
        '--puzzles',
        required=True,
        help="Path to input puzzle metadata JSONL file"
    )
    parser.add_argument(
        '--output',
        required=True,
        help="Path to output CSV file"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    try:
        process_execution_results(
            execution_log_path=args.execution_log,
            puzzle_metadata_path=args.puzzles,
            output_path=args.output
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing results: {e}")
        raise

if __name__ == '__main__':
    main()