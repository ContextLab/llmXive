"""
T024: Calculate divergence metrics between model execution paths and ground truth.

This module reads the execution log (produced by rm_executor) and the original
puzzle metadata (including the perturbed ground_truth_path) to calculate
a divergence metric (Jaccard distance) for each instance.

It ensures FR-007 compliance by validating against the perturbed ground truth
stored in the metadata, not the longest path.
"""
import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

from utils.logging_utils import configure_logging

# Configure logging
logger = logging.getLogger(__name__)

def load_execution_log(log_path: str) -> List[Dict[str, Any]]:
    """Load the execution log CSV."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Execution log not found at {log_path}")
    
    data = []
    with open(log_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse JSON fields if they are stored as strings
            if 'predicted_path' in row and row['predicted_path']:
                try:
                    row['predicted_path'] = json.loads(row['predicted_path'])
                except json.JSONDecodeError:
                    row['predicted_path'] = []
            data.append(row)
    return data

def load_puzzles_metadata(puzzle_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the logical puzzles JSONL and index by instance_id.
    We need the 'ground_truth_path' which is the perturbed one.
    """
    if not os.path.exists(puzzle_path):
        raise FileNotFoundError(f"Puzzle metadata not found at {puzzle_path}")
    
    puzzles = {}
    with open(puzzle_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            puzzle = json.loads(line)
            instance_id = puzzle.get('instance_id')
            if not instance_id:
                logger.warning(f"Skipping line without instance_id in {puzzle_path}")
                continue
            puzzles[instance_id] = puzzle
    return puzzles

def jaccard_distance(path_a: List[str], path_b: List[str]) -> float:
    """
    Calculate Jaccard distance between two paths.
    Jaccard Distance = 1 - (|Intersection| / |Union|)
    Treats paths as sets of nodes.
    """
    set_a = set(path_a)
    set_b = set(path_b)
    
    if not set_a and not set_b:
        return 0.0  # Both empty -> identical
    if not set_a or not set_b:
        return 1.0  # One empty, one not -> completely different
    
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    
    return 1.0 - (len(intersection) / len(union))

def calculate_divergence_metrics(
    execution_log_path: str,
    puzzle_metadata_path: str,
    output_path: str
) -> None:
    """
    Main function to calculate divergence metrics.
    
    Reads execution_log.csv and logical_puzzles.jsonl, calculates Jaccard distance
    between predicted_path and ground_truth_path, and writes the result to
    execution_log_with_metrics.csv.
    """
    logger.info(f"Loading execution log from {execution_log_path}")
    execution_data = load_execution_log(execution_log_path)
    
    logger.info(f"Loading puzzle metadata from {puzzle_metadata_path}")
    puzzles = load_puzzles_metadata(puzzle_metadata_path)
    
    output_rows = []
    total_instances = len(execution_data)
    processed = 0
    
    for row in execution_data:
        instance_id = row.get('instance_id')
        if not instance_id:
            logger.warning("Skipping row without instance_id")
            continue
        
        # Get ground truth path from metadata (perturbed)
        puzzle_data = puzzles.get(instance_id)
        if not puzzle_data:
            logger.warning(f"Instance {instance_id} not found in metadata")
            # Default to max distance if missing
            divergence = 1.0
            row['divergence_from_ground_truth'] = divergence
            output_rows.append(row)
            continue
        
        ground_truth_path = puzzle_data.get('ground_truth_path', [])
        predicted_path = row.get('predicted_path', [])
        
        # Ensure predicted_path is a list
        if isinstance(predicted_path, str):
            try:
                predicted_path = json.loads(predicted_path)
            except:
                predicted_path = []
        
        # Calculate divergence (Jaccard distance)
        divergence = jaccard_distance(predicted_path, ground_truth_path)
        
        row['divergence_from_ground_truth'] = divergence
        output_rows.append(row)
        processed += 1
        
        if processed % 100 == 0:
            logger.info(f"Processed {processed}/{total_instances} instances")
    
    # Write output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Writing results to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if output_rows:
            fieldnames = list(output_rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in output_rows:
                writer.writerow(row)
    
    logger.info(f"Successfully processed {processed} instances")
    logger.info(f"Output written to {output_path}")

def main():
    """Entry point for the script."""
    configure_logging()
    
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    execution_log_path = project_root / "data" / "processed" / "execution_log.csv"
    puzzle_metadata_path = project_root / "data" / "raw" / "logical_puzzles.jsonl"
    output_path = project_root / "data" / "processed" / "execution_log.csv"
    
    # Note: We overwrite the execution_log.csv with the new column.
    # In a real pipeline, we might write to a new file, but the task
    # specifies the output is in data/processed/execution_log.csv.
    
    if not os.path.exists(execution_log_path):
        logger.error(f"Execution log not found at {execution_log_path}. "
                     "Run T027 (rm_executor) first.")
        return 1
    
    if not os.path.exists(puzzle_metadata_path):
        logger.error(f"Puzzle metadata not found at {puzzle_metadata_path}. "
                     "Run T016 (graph_generator) first.")
        return 1
    
    try:
        calculate_divergence_metrics(
            str(execution_log_path),
            str(puzzle_metadata_path),
            str(output_path)
        )
        return 0
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
