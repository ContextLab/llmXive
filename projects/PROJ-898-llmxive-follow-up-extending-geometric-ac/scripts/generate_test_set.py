#!/usr/bin/env python3
"""
Script to execute the Topology-Shift Test Set generation.

This script orchestrates the generation of a synthetic dataset containing
novel kinematic chains and deformable materials using PyBullet, as defined
in User Story 1 (US1).

It loads configuration, initializes the TopologyShiftGenerator, runs the
generation process, and saves the resulting metadata and data files.
"""

import argparse
import logging
import os
import sys

# Add project root to path to allow relative imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import load_config, create_default_config_file
from code.data_generation import TopologyShiftGenerator
from code.utils import setup_logging, set_deterministic_seed


def main():
    parser = argparse.ArgumentParser(
        description="Generate the Topology-Shift Test Set for US1."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/experiment_config.json",
        help="Path to the experiment configuration file."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the random seed from config."
    )
    parser.add_argument(
        "--num-topologies",
        type=int,
        default=None,
        help="Override the number of topologies to generate."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/generated",
        help="Directory to save generated data."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging("generate_test_set", log_level=log_level)
    logger.info("Starting Topology-Shift Test Set generation.")

    # Load or create config
    config_path = args.config
    if not os.path.exists(config_path):
        logger.info(f"Config file {config_path} not found. Creating default.")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        create_default_config_file(config_path)
    
    config = load_config(config_path)

    # Apply CLI overrides
    if args.seed is not None:
        config['random_seed'] = args.seed
    if args.num_topologies is not None:
        config['generation_params']['num_topologies'] = args.num_topologies
    
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Set deterministic seed
    set_deterministic_seed(config['random_seed'])
    logger.info(f"Random seed set to {config['random_seed']}")

    # Initialize Generator
    logger.info("Initializing TopologyShiftGenerator...")
    generator = TopologyShiftGenerator(
        num_topologies=config['generation_params']['num_topologies'],
        output_dir=output_dir,
        logger=logger
    )

    try:
        # Run generation
        logger.info("Starting generation process...")
        generator.generate_all()
        
        logger.info("Generation completed successfully.")
        logger.info(f"Output files saved to: {output_dir}")
        
        # Verify outputs exist (basic check)
        expected_files = [
            os.path.join(output_dir, "topology_shift_metadata.json"),
            os.path.join(output_dir, "topology_shift_data.npz")
        ]
        
        all_exist = True
        for f in expected_files:
            if os.path.exists(f):
                logger.debug(f"Verified: {f} exists.")
            else:
                logger.warning(f"Expected output not found: {f}")
                all_exist = False

        if all_exist:
            logger.info("All expected output files verified.")
            return 0
        else:
            logger.error("Some expected output files are missing.")
            return 1

    except Exception as e:
        logger.exception(f"Generation failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())