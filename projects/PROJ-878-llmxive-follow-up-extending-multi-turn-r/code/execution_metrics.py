import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

import networkx as nx

logger = logging.getLogger(__name__)

def load_execution_log(log_path: str) -> List[Dict[str, Any]]:
    """Load execution log from CSV file."""
    log_file = Path(log_path)
    if not log_file.exists():
        raise FileNotFoundError(f"Execution log not found: {log_path}")
    
    results = []
    with open(log_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_puzzles_metadata(metadata_path: str) -> Dict[str, Dict[str, Any]]:
    """Load puzzle metadata from JSONL file."""
    meta_file = Path(metadata_path)
    if not meta_file.exists():
        raise FileNotFoundError(f"Puzzle metadata not found: {metadata_path}")
    
    puzzles = {}
    with open(meta_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            puzzle = json.loads(line)
            instance_id = puzzle.get('instance_id')
            if instance_id:
                puzzles[instance_id] = puzzle
    return puzzles

def jaccard_distance(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard distance between two sets of nodes."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return 1.0 - (intersection / union)

def path_edit_distance(path_a: List[str], path_b: List[str]) -> float:
    """Calculate normalized edit distance between two paths."""
    if not path_a and not path_b:
        return 0.0
    if not path_a or not path_b:
        return 1.0
    
    # Simple edit distance calculation
    m, n = len(path_a), len(path_b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if path_a[i-1] == path_b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    max_len = max(m, n)
    if max_len == 0:
        return 0.0
    return dp[m][n] / max_len

def calculate_divergence_metrics(execution_log: List[Dict[str, Any]], 
                                 puzzles_metadata: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate divergence metrics between model paths and ground truth paths.
    
    Ensures FR-007 compliance by validating against the perturbed ground truth,
    NOT the longest path.
    
    Args:
        execution_log: List of execution results with 'instance_id' and 'model_path'
        puzzles_metadata: Dictionary mapping instance_id to puzzle metadata containing
                       'ground_truth_path' (which should be the perturbed path)
    
    Returns:
        List of execution results with added divergence metrics
    """
    results = []
    
    for entry in execution_log:
        instance_id = entry.get('instance_id')
        
        if instance_id not in puzzles_metadata:
            logger.warning(f"Instance {instance_id} not found in metadata, skipping divergence calculation")
            entry['divergence_from_ground_truth'] = None
            entry['jaccard_distance'] = None
            entry['path_edit_distance'] = None
            results.append(entry)
            continue
        
        puzzle = puzzles_metadata[instance_id]
        ground_truth_path = puzzle.get('ground_truth_path')
        model_path_str = entry.get('model_path')
        
        if not ground_truth_path or not model_path_str:
            logger.warning(f"Missing ground_truth_path or model_path for {instance_id}")
            entry['divergence_from_ground_truth'] = None
            entry['jaccard_distance'] = None
            entry['path_edit_distance'] = None
            results.append(entry)
            continue
        
        # Parse paths
        if isinstance(ground_truth_path, str):
            ground_truth_path = json.loads(ground_truth_path)
        if isinstance(model_path_str, str):
            try:
                model_path = json.loads(model_path_str)
            except json.JSONDecodeError:
                # Try parsing as comma-separated string
                model_path = [n.strip() for n in model_path_str.split(',') if n.strip()]
        else:
            model_path = model_path_str
        
        # Convert to sets for Jaccard distance
        ground_truth_set = set(ground_truth_path)
        model_set = set(model_path)
        
        # Calculate metrics
        jaccard_dist = jaccard_distance(ground_truth_set, model_set)
        edit_dist = path_edit_distance(ground_truth_path, model_path)
        
        # Composite divergence metric (weighted average)
        divergence = 0.5 * jaccard_dist + 0.5 * edit_dist
        
        entry['jaccard_distance'] = jaccard_dist
        entry['path_edit_distance'] = edit_dist
        entry['divergence_from_ground_truth'] = divergence
        
        results.append(entry)
    
    return results

def write_execution_log_with_metrics(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write execution results with divergence metrics to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        logger.warning("No results to write")
        return
    
    # Determine fieldnames
    fieldnames = list(results[0].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Wrote {len(results)} results to {output_path}")

def main():
    """Main entry point for calculating divergence metrics."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    puzzles_path = "data/raw/logical_puzzles.jsonl"
    execution_log_path = "data/processed/execution_log.csv"
    output_path = "data/processed/execution_log.csv"
    
    logger.info(f"Loading puzzle metadata from {puzzles_path}")
    try:
        puzzles_metadata = load_puzzles_metadata(puzzles_path)
        logger.info(f"Loaded metadata for {len(puzzles_metadata)} puzzles")
    except FileNotFoundError as e:
        logger.error(f"Failed to load puzzle metadata: {e}")
        return
    
    logger.info(f"Loading execution log from {execution_log_path}")
    try:
        execution_log = load_execution_log(execution_log_path)
        logger.info(f"Loaded {len(execution_log)} execution records")
    except FileNotFoundError as e:
        logger.error(f"Failed to load execution log: {e}")
        return
    
    logger.info("Calculating divergence metrics...")
    results = calculate_divergence_metrics(execution_log, puzzles_metadata)
    
    logger.info(f"Writing results to {output_path}")
    write_execution_log_with_metrics(results, output_path)
    
    # Summary statistics
    divergences = [r['divergence_from_ground_truth'] for r in results 
                  if r['divergence_from_ground_truth'] is not None]
    if divergences:
        avg_divergence = sum(divergences) / len(divergences)
        logger.info(f"Average divergence from ground truth: {avg_divergence:.4f}")
    else:
        logger.warning("No valid divergence metrics calculated")

if __name__ == "__main__":
    main()