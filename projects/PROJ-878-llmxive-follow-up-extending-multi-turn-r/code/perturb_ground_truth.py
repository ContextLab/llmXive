"""
Perturb Ground Truth Path (FR-007)

This script loads generated logical puzzles, selects a valid ground-truth path
different from the longest path (if possible), and calculates the cycle rate
(discarded/total attempts) for the perturbation process.

It writes the cycle rate and status to data/validation_metrics.json.
"""
import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.graph_utils import (
    graph_from_dict, 
    longest_path, 
    get_all_simple_paths_from_source_to_target,
    get_random_valid_path_different_from_reference
)
from utils.logging_utils import configure_logging

def load_puzzles(input_path: str) -> List[Dict[str, Any]]:
    """Load puzzles from a JSONL file."""
    puzzles = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                puzzles.append(json.loads(line))
    return puzzles

def process_puzzles(puzzles: List[Dict[str, Any]], max_attempts: int = 100) -> Dict[str, Any]:
    """
    Process puzzles to perturb ground truth paths.
    
    For each puzzle:
    1. Reconstruct the graph.
    2. Identify the longest path.
    3. Attempt to find a different valid path (ground truth).
    4. Track success/failure (cycle rate).
    
    Args:
        puzzles: List of puzzle dictionaries.
        max_attempts: Maximum attempts to find a different path.
        
    Returns:
        Dictionary containing processed puzzles and cycle rate metrics.
    """
    processed_puzzles = []
    total_attempts = 0
    successful_perturbations = 0
    failed_perturbations = 0

    for i, puzzle in enumerate(puzzles):
        graph_data = puzzle.get('graph_structure')
        if not graph_data:
            logging.warning(f"Puzzle {i} missing graph_structure, skipping.")
            continue

        G = graph_from_dict(graph_data)
        
        # Determine source and target (assuming standard DAG structure)
        # We look for nodes with in-degree 0 and out-degree 0
        sources = [n for n in G.nodes() if G.in_degree(n) == 0]
        targets = [n for n in G.nodes() if G.out_degree(n) == 0]
        
        if not sources or not targets:
            logging.warning(f"Puzzle {i} has no valid source or target, skipping.")
            continue
        
        source = sources[0]
        target = targets[0]

        # Get the longest path
        try:
            ref_path = longest_path(G, source, target)
        except Exception as e:
            logging.warning(f"Puzzle {i} failed to find longest path: {e}, skipping.")
            continue

        total_attempts += 1

        # Attempt to find a different valid path
        new_path = get_random_valid_path_different_from_reference(
            G, source, target, ref_path, max_attempts=max_attempts
        )

        if new_path is not None and new_path != ref_path:
            successful_perturbations += 1
            # Update the puzzle with the new ground truth path
            puzzle['ground_truth_path'] = new_path
            puzzle['original_longest_path'] = ref_path
            puzzle['path_perturbed'] = True
        else:
            failed_perturbations += 1
            # If no different path exists, we keep the longest path but mark it
            puzzle['ground_truth_path'] = ref_path
            puzzle['original_longest_path'] = ref_path
            puzzle['path_perturbed'] = False

        processed_puzzles.append(puzzle)

    cycle_rate = failed_perturbations / total_attempts if total_attempts > 0 else 0.0

    metrics = {
        "total_puzzles": len(puzzles),
        "total_attempts": total_attempts,
        "successful_perturbations": successful_perturbations,
        "failed_perturbations": failed_perturbations,
        "cycle_rate": cycle_rate,
        "status": "[deferred]" 
    }

    return {
        "processed_puzzles": processed_puzzles,
        "metrics": metrics
    }

def main():
    """Main entry point for the perturb ground truth script."""
    configure_logging()
    
    input_path = PROJECT_ROOT / "data" / "raw" / "logical_puzzles.jsonl"
    output_path = PROJECT_ROOT / "data" / "raw" / "logical_puzzles_perturbed.jsonl"
    metrics_path = PROJECT_ROOT / "data" / "validation_metrics.json"

    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logging.info(f"Loading puzzles from {input_path}")
    puzzles = load_puzzles(str(input_path))
    logging.info(f"Loaded {len(puzzles)} puzzles")

    logging.info("Processing puzzles to perturb ground truth paths...")
    result = process_puzzles(puzzles)

    # Write processed puzzles
    with open(output_path, 'w') as f:
        for puzzle in result['processed_puzzles']:
            f.write(json.dumps(puzzle) + '\n')
    logging.info(f"Wrote {len(result['processed_puzzles'])} processed puzzles to {output_path}")

    # Write metrics
    with open(metrics_path, 'w') as f:
        json.dump(result['metrics'], f, indent=2)
    logging.info(f"Wrote validation metrics to {metrics_path}")

    logging.info(f"Cycle rate (discarded/total attempts): {result['metrics']['cycle_rate']:.4f}")

if __name__ == "__main__":
    main()
