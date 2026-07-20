#!/usr/bin/env python3
"""
Script to execute the synthetic test set generation for User Story 1.

This script orchestrates the generation of novel kinematic chains and 
deformable materials using PyBullet, ensuring zero overlap with the 
original GAM training data.

Usage:
    python scripts/generate_test_set.py [--seed SEED] [--config CONFIG_PATH]

Output:
    - data/generated/physics_states.json
    - data/generated/latent_trajectory.csv
    - data/results/errors.log (if any errors occur)
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import load_config, get_default_config_path
from data_generation import TopologyShiftGenerator, main as generation_main
from metadata_checksum import generate_test_set_metadata, verify_zero_overlap
from utils import setup_logging, set_deterministic_seed

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic test set for geometric action model evaluation."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility. Defaults to config value."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config YAML file. Defaults to code/config.yaml."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base output directory. Defaults to project root."
    )
    return parser.parse_args()

def main():
    """Main entry point for test set generation."""
    args = parse_args()
    
    # Setup logging
    log_path = project_root / "data" / "results" / "errors.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(
        name="test_set_generation",
        log_file=str(log_path),
        level=logging.INFO
    )
    
    logger.info("Starting synthetic test set generation (T013)")
    
    # Load configuration
    config_path = args.config or get_default_config_path()
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
        
    config = load_config(config_path)
    
    # Override seed if provided
    if args.seed is not None:
        config.experiment.seed = args.seed
        
    # Set deterministic seed
    set_deterministic_seed(config.experiment.seed)
    logger.info(f"Using seed: {config.experiment.seed}")
    
    # Validate baseline metadata exists
    baseline_metadata_path = project_root / "data" / "raw" / "gam_baseline_metadata.json"
    if not baseline_metadata_path.exists():
        logger.error(f"Baseline metadata not found: {baseline_metadata_path}")
        logger.error("Run T009a first to create baseline metadata.")
        sys.exit(1)
    
    # Initialize generator
    generator = TopologyShiftGenerator(
        config=config,
        baseline_metadata_path=str(baseline_metadata_path),
        logger=logger
    )
    
    # Generate test set
    logger.info(f"Generating {config.experiment.trial_count} trials...")
    generation_main(
        config=config,
        output_dir=args.output_dir or str(project_root),
        logger=logger
    )
    
    # Verify zero overlap
    logger.info("Verifying zero overlap with baseline...")
    try:
        overlap_result = verify_zero_overlap(
            baseline_path=str(baseline_metadata_path),
            generated_path=str(project_root / "data" / "generated" / "physics_states.json")
        )
        
        if overlap_result["overlap_detected"]:
            logger.error("ZERO OVERLAP VERIFICATION FAILED!")
            logger.error(f"Overlap details: {overlap_result}")
            sys.exit(1)
        else:
            logger.info("Zero overlap verification PASSED.")
            logger.info(f"Generated topology IDs: {overlap_result['generated_topology_ids'][:5]}...")
    except Exception as e:
        logger.error(f"Overlap verification failed with error: {e}")
        sys.exit(1)
    
    # Generate metadata for the generated set
    metadata_path = project_root / "data" / "generated" / "test_set_metadata.json"
    generate_test_set_metadata(
        physics_states_path=str(project_root / "data" / "generated" / "physics_states.json"),
        output_path=str(metadata_path),
        seed=config.experiment.seed
    )
    logger.info(f"Test set metadata saved to: {metadata_path}")
    
    logger.info("Test set generation completed successfully!")
    logger.info(f"Output files:")
    logger.info(f"  - physics_states.json: {project_root / 'data' / 'generated' / 'physics_states.json'}")
    logger.info(f"  - latent_trajectory.csv: {project_root / 'data' / 'generated' / 'latent_trajectory.csv'}")
    logger.info(f"  - test_set_metadata.json: {metadata_path}")

if __name__ == "__main__":
    main()
