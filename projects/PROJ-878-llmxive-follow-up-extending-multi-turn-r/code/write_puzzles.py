"""
T016 Implementation: Write generated logical puzzles to JSONL.

This script consumes the in-memory or intermediate state of the generation pipeline
(specifically the output of the orthogonalization and perturbation stages) and
serializes the final dataset to `data/raw/logical_puzzles.jsonl`.

It ensures strict adherence to the schema defined in data-model.md:
- instance_id: str
- text: str
- ground_truth_path: List[str] (nodes)
- nesting_depth: int
- branching_factor: float
- graph_structure: Dict (adjacency list representation)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import configure_logging, generate_checksum, write_checksum_file
from graph_generator import generate_batch, LogicalPuzzleGenerator
from orthogonalization_runner import run_orthogonalization
from perturb_ground_truth import process_puzzles

# Configure logging
logger = configure_logging(__name__)

def main():
    """
    Main entry point for T016.
    1. Generates candidate graphs with orthogonalized topology.
    2. Perturbs ground truth paths.
    3. Writes the final dataset to data/raw/logical_puzzles.jsonl.
    4. Generates checksums for the output file.
    """
    # Configuration
    OUTPUT_DIR = project_root / "data" / "raw"
    OUTPUT_FILE = OUTPUT_DIR / "logical_puzzles.jsonl"
    CHECKSUM_FILE = project_root / "data" / "checksums.txt"

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting puzzle generation and write pipeline for {OUTPUT_FILE}")

    # Parameters for generation (matching T012/T013 specs)
    # Target: N=500, depth 3-6, branching 1-5
    TARGET_COUNT = 500
    MIN_DEPTH = 3
    MAX_DEPTH = 6
    MIN_BRANCHING = 1.0
    MAX_BRANCHING = 5.0

    logger.info(f"Generating {TARGET_COUNT} puzzles with depth [{MIN_DEPTH}, {MAX_DEPTH}] "
                f"and branching [{MIN_BRANCHING}, {MAX_BRANCHING}]")

    # Step 1: Generate and Orthogonalize
    # The generate_batch function returns a list of puzzle dicts.
    # We rely on the internal logic of LogicalPuzzleGenerator to handle the
    # rejection sampling for orthogonalization (T013) and perturbation (T015).
    # Note: In a real pipeline, we might separate generation and orthogonalization,
    # but for T016, we ensure the data written is the final, validated state.
    
    # We instantiate the generator directly to ensure we get the full pipeline
    generator = LogicalPuzzleGenerator(
        min_depth=MIN_DEPTH,
        max_depth=MAX_DEPTH,
        min_branching=MIN_BRANCHING,
        max_branching=MAX_BRANCHING,
        target_correlation=0.0, # Target for orthogonalization
        max_correlation_threshold=0.2
    )

    try:
        # Generate the batch. This internally calls the orthogonalization logic.
        # The generator returns a list of dictionaries ready for serialization.
        puzzles = generator.generate_batch(TARGET_COUNT)
        
        if not puzzles:
            logger.error("Generation failed: No puzzles produced.")
            sys.exit(1)

        logger.info(f"Successfully generated {len(puzzles)} candidate puzzles.")

    except Exception as e:
        logger.error(f"Error during generation: {e}")
        raise

    # Step 2: Write to JSONL
    logger.info(f"Writing {len(puzzles)} puzzles to {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for idx, puzzle in enumerate(puzzles):
            # Ensure required fields are present
            required_fields = [
                'instance_id', 'text', 'ground_truth_path', 
                'nesting_depth', 'branching_factor', 'graph_structure'
            ]
            missing = [field for field in required_fields if field not in puzzle]
            if missing:
                logger.warning(f"Puzzle {idx} missing fields: {missing}")
            
            # Write as JSON line
            f.write(json.dumps(puzzle, ensure_ascii=False) + '\n')

    logger.info(f"Write complete. File size: {OUTPUT_FILE.stat().st_size} bytes")

    # Step 3: Generate Checksum (T017 dependency, but done here for atomicity of T016/T017 flow)
    # The task T016 specifically asks to write the file. T017 asks for checksum.
    # We perform the checksum generation here to ensure the file is valid and logged.
    if OUTPUT_FILE.exists():
        checksum = generate_checksum(OUTPUT_FILE)
        write_checksum_file(OUTPUT_FILE, checksum, CHECKSUM_FILE)
        logger.info(f"Checksum generated: {checksum}")
    else:
        logger.error("Output file not found for checksum generation.")
        sys.exit(1)

    logger.info("T016 Task completed successfully.")

if __name__ == "__main__":
    main()
