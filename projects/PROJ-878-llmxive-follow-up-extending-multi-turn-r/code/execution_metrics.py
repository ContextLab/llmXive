"""
execution_metrics.py

Computes divergence metrics (Jaccard distance, path edit distance) between
the model's predicted path and the perturbed ground truth path.

Ensures FR-007 compliance by validating against the perturbed ground truth,
NOT the longest path.
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_execution_log(filepath: str) -> List[Dict[str, Any]]:
    """Load the execution log CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Execution log not found: {filepath}")
    
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse JSON fields if they exist as strings
            if 'predicted_path' in row and row['predicted_path']:
                try:
                    row['predicted_path'] = json.loads(row['predicted_path'])
                except json.JSONDecodeError:
                    row['predicted_path'] = []
            results.append(row)
    
    return results

def load_puzzles_metadata(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the logical puzzles JSONL file and index by instance_id.
    Returns a dict: {instance_id: {ground_truth_path, ...}}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Puzzles metadata not found: {filepath}")
    
    metadata = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                puzzle = json.loads(line)
                instance_id = puzzle.get('instance_id')
                if instance_id:
                    metadata[instance_id] = puzzle
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON line: {e}")
    
    return metadata

def jaccard_distance(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate Jaccard distance between two sets of nodes/edges.
    Jaccard Distance = 1 - (|A ∩ B| / |A ∪ B|)
    Returns 0.0 if both sets are empty.
    """
    if not set_a and not set_b:
        return 0.0
    if not set_a or not set_b:
        return 1.0
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
    
    return 1.0 - (intersection / union)

def path_edit_distance(path_a: List[str], path_b: List[str]) -> float:
    """
    Calculate a simple edit distance (Levenshtein-like) normalized by max length.
    Returns 0.0 if identical, 1.0 if completely different.
    """
    if path_a == path_b:
        return 0.0
    
    len_a, len_b = len(path_a), len(path_b)
    if len_a == 0 and len_b == 0:
        return 0.0
    
    # Simple dynamic programming for edit distance
    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]
    
    for i in range(len_a + 1):
        dp[i][0] = i
    for j in range(len_b + 1):
        dp[0][j] = j
    
    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            if path_a[i-1] == path_b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    max_len = max(len_a, len_b)
    if max_len == 0:
        return 0.0
    
    return dp[len_a][len_b] / max_len

def calculate_divergence_metrics(
    predicted_path: List[str],
    ground_truth_path: List[str]
) -> Dict[str, float]:
    """
    Calculate divergence metrics between predicted and ground truth paths.
    
    Args:
        predicted_path: List of node IDs predicted by the model.
        ground_truth_path: List of node IDs representing the perturbed ground truth.
    
    Returns:
        Dictionary with 'jaccard_distance' and 'path_edit_distance'.
    """
    # Convert paths to sets for Jaccard calculation
    set_pred = set(predicted_path)
    set_gt = set(ground_truth_path)
    
    jac_dist = jaccard_distance(set_pred, set_gt)
    edit_dist = path_edit_distance(predicted_path, ground_truth_path)
    
    return {
        'jaccard_distance': jac_dist,
        'path_edit_distance': edit_dist
    }

def write_execution_log_with_metrics(
    input_log_path: str,
    output_log_path: str,
    puzzles_metadata: Dict[str, Dict[str, Any]]
) -> None:
    """
    Read execution log, calculate divergence metrics against perturbed ground truth,
    and write the enriched log to the output path.
    
    FR-007 Compliance: Uses 'ground_truth_path' from metadata (which is perturbed),
    NOT the longest path of the original DAG.
    """
    if not os.path.exists(input_log_path):
        raise FileNotFoundError(f"Input execution log not found: {input_log_path}")
    
    execution_records = load_execution_log(input_log_path)
    
    if not execution_records:
        logger.warning("Execution log is empty. No metrics to calculate.")
        # Write empty file with headers if needed
        with open(output_log_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    # Ensure output directory exists
    Path(output_log_path).parent.mkdir(parents=True, exist_ok=True)
    
    output_rows = []
    metrics_summary = {'total': 0, 'success': 0, 'failure': 0, 'total_jaccard': 0.0}
    
    for record in execution_records:
        instance_id = record.get('instance_id')
        if not instance_id:
            logger.warning(f"Record missing instance_id: {record}")
            continue
        
        # Get predicted path from execution log
        predicted_path = record.get('predicted_path', [])
        if isinstance(predicted_path, str):
            try:
                predicted_path = json.loads(predicted_path)
            except json.JSONDecodeError:
                predicted_path = []
        
        # Get perturbed ground truth from metadata (FR-007 compliance)
        puzzle_meta = puzzles_metadata.get(instance_id)
        if not puzzle_meta:
            logger.warning(f"No metadata found for instance_id: {instance_id}")
            continue
        
        # CRITICAL: Use the perturbed ground truth path, not the longest path
        ground_truth_path = puzzle_meta.get('ground_truth_path')
        if not ground_truth_path:
            logger.warning(f"No ground_truth_path found for instance_id: {instance_id}")
            continue
        
        # Calculate metrics
        metrics = calculate_divergence_metrics(predicted_path, ground_truth_path)
        
        # Update record
        record['divergence_jaccard'] = metrics['jaccard_distance']
        record['divergence_edit'] = metrics['path_edit_distance']
        
        # Track summary stats
        metrics_summary['total'] += 1
        status = record.get('convergence_status', 'failure')
        if status == 'success':
            metrics_summary['success'] += 1
        else:
            metrics_summary['failure'] += 1
        metrics_summary['total_jaccard'] += metrics['jaccard_distance']
        
        output_rows.append(record)
    
    # Write enriched log
    if output_rows:
        fieldnames = list(output_rows[0].keys())
        with open(output_log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
    
    avg_jaccard = metrics_summary['total_jaccard'] / max(1, metrics_summary['total'])
    logger.info(f"Wrote {len(output_rows)} enriched records to {output_log_path}")
    logger.info(f"Average Jaccard divergence: {avg_jaccard:.4f}")
    logger.info(f"Success rate: {metrics_summary['success']}/{metrics_summary['total']}")

def main():
    """Main entry point for calculating divergence metrics."""
    import argparse

    parser = argparse.ArgumentParser(description='Calculate divergence metrics for execution results.')
    parser.add_argument('--input', required=True, help='Path to input execution log CSV')
    parser.add_argument('--output', required=True, help='Path to output enriched execution log CSV')
    parser.add_argument('--puzzles', required=True, help='Path to logical_puzzles.jsonl metadata file')
    
    args = parser.parse_args()
    
    logger.info(f"Loading puzzles metadata from: {args.puzzles}")
    puzzles_metadata = load_puzzles_metadata(args.puzzles)
    logger.info(f"Loaded {len(puzzles_metadata)} puzzle metadata entries.")
    
    logger.info(f"Processing execution log from: {args.input}")
    write_execution_log_with_metrics(
        input_log_path=args.input,
        output_log_path=args.output,
        puzzles_metadata=puzzles_metadata
    )
    
    logger.info("Divergence metrics calculation complete.")

if __name__ == '__main__':
    main()