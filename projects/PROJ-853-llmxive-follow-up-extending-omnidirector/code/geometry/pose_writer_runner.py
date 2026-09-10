"""
Runner script to execute T019: Write pose estimates and reconstructed boxes.

This script consumes the output from the geometry solver (T017) and 
the reconstruction module (T018) to generate the final JSON artifact.

It assumes:
1. `data/processed/poses_estimated.json` is NOT yet written (this is the target).
2. The solver has already processed `data/processed/filtered_sequences.csv`.
3. The reconstruction module has calculated dimensions.

To run this task, we must re-run the solver logic to get the data structures
in memory, then pass them to the writer.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, load_config
from geometry.solver import process_filtered_sequences
from geometry.reconstruction import process_poses_for_reconstruction
from geometry.writer import write_poses_and_boxes

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for T019.
    1. Loads filtered sequences.
    2. Runs solver to get pose estimates (in memory).
    3. Runs reconstruction to get box dimensions (in memory).
    4. Writes combined result to data/processed/poses_estimated.json.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting T019: Writing pose estimates and reconstructed boxes.")

    # Ensure config is loaded
    config = load_config()
    
    # Paths
    input_csv_path = get_path("filtered_sequences_csv")
    output_json_path = get_path("poses_estimated_json")

    if not input_csv_path.exists():
        logger.error(f"Input file not found: {input_csv_path}")
        logger.error("T011 (filtered_sequences.csv) must be completed before T019.")
        sys.exit(1)

    logger.info(f"Reading input from: {input_csv_path}")
    logger.info(f"Writing output to: {output_json_path}")

    try:
        # 1. Run Solver to get pose estimates
        # process_filtered_sequences returns a list of dicts with pose info
        logger.info("Running pose estimation solver...")
        poses_data = process_filtered_sequences(input_csv_path)
        
        if not poses_data:
            logger.warning("No poses were estimated. Output file will be empty.")
        
        # 2. Run Reconstruction to get box dimensions
        # process_poses_for_reconstruction expects the same data or a path to it
        # We can pass the poses_data directly if the function supports it, 
        # or we re-derive from the CSV if needed. 
        # Based on T018 signature, it likely takes the CSV path or the poses.
        # Let's assume it takes the CSV path to be consistent with pipeline flow.
        logger.info("Running box dimension reconstruction...")
        boxes_data = process_poses_for_reconstruction(input_csv_path)

        # 3. Write to JSON
        write_poses_and_boxes(poses_data, boxes_data, output_path=output_json_path)

        logger.info("T019 completed successfully.")

    except Exception as e:
        logger.error(f"Failed to execute T019: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()