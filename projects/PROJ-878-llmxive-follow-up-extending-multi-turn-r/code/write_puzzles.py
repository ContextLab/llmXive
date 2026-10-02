import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent to path for imports if running directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.graph_generator import generate_batch
from code.utils.logging_utils import configure_logging

def main():
    """
    Generates a batch of logical puzzles with controlled topology,
    perturbs the ground truth path, and writes them to data/raw/logical_puzzles.jsonl.
    """
    # Configure logging
    logger = configure_logging("write_puzzles", level=logging.INFO)
    logger.info("Starting puzzle generation for T016.")

    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "logical_puzzles.jsonl"

    # Configuration for generation
    # Based on T013/T015 context: Depth 3-6, Branching 1-5
    num_instances = 100
    min_depth = 3
    max_depth = 6
    min_branching = 1
    max_branching = 5
    target_correlation = 0.2

    logger.info(f"Generating {num_instances} instances with depth [{min_depth}, {max_depth}] and branching [{min_branching}, {max_branching}].")

    try:
        # Generate the batch
        # The generate_batch function handles the graph generation,
        # orthogonalization checks, and perturbation logic internally
        # as per T012, T013, T014, T015 implementation.
        puzzles = generate_batch(
            num_instances=num_instances,
            min_depth=min_depth,
            max_depth=max_depth,
            min_branching=min_branching,
            max_branching=max_branching,
            max_correlation=target_correlation,
            logger=logger
        )

        if not puzzles:
            logger.error("Generation produced no valid puzzles. Check orthogonalization constraints.")
            sys.exit(1)

        # Write to JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for idx, puzzle in enumerate(puzzles):
                # Ensure instance_id is set
                if "instance_id" not in puzzle:
                    puzzle["instance_id"] = f"puzzle_{idx:04d}"
                
                # Write as a single JSON line
                f.write(json.dumps(puzzle, ensure_ascii=False) + "\n")

        logger.info(f"Successfully wrote {len(puzzles)} puzzles to {output_file}")
        logger.info(f"Sample instance ID: {puzzles[0].get('instance_id')}")
        
        # Log basic stats
        depths = [p.get('nesting_depth', 0) for p in puzzles]
        branchings = [p.get('branching_factor', 0) for p in puzzles]
        logger.info(f"Depth range: {min(depths)}-{max(depths)} (Target: {min_depth}-{max_depth})")
        logger.info(f"Branching range: {min(branchings)}-{max(branchings)} (Target: {min_branching}-{max_branching})")

    except Exception as e:
        logger.error(f"Failed to generate or write puzzles: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
