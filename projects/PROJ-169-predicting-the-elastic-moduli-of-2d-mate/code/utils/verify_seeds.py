"""
Seed Verification Script for Reproducibility (Constitution Principle I)

This script verifies that the global seed pinning mechanism in `config.py`
correctly enforces consistent random states across `torch`, `numpy`, and `random`
modules. It runs a dummy pipeline step to simulate real usage and asserts
that the seeds remain pinned as expected.
"""

import os
import sys
import random
import logging
from pathlib import Path

import numpy as np
import torch

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import Config
from utils.logger import get_logger

# Configure logger for this script
logger = get_logger(__name__)

def run_dummy_pipeline_step(seed_value: int) -> dict:
    """
    Simulates a dummy pipeline step that uses random number generation.
    This ensures that the seed pinning is tested in a realistic context.

    Args:
        seed_value: The seed value to use for reproducibility.

    Returns:
        A dictionary containing the generated random values for verification.
    """
    # Generate random values using all three libraries
    torch_val = torch.rand(1).item()
    np_val = np.random.rand(1).item()
    random_val = random.random()

    return {
        "torch_val": torch_val,
        "np_val": np_val,
        "random_val": random_val
    }

def verify_seed_pinning(seed_value: int = 42) -> bool:
    """
    Verifies that seed pinning works correctly by running the dummy pipeline
    step twice and ensuring identical outputs.

    Args:
        seed_value: The seed value to pin.

    Returns:
        True if verification passes, False otherwise.
    """
    logger.info(f"Starting seed verification with seed value: {seed_value}")

    # First run
    logger.info("Running first pipeline step...")
    Config.set_seed(seed_value)
    result1 = run_dummy_pipeline_step(seed_value)
    logger.debug(f"First run results: {result1}")

    # Second run (should be identical if seeds are pinned correctly)
    logger.info("Running second pipeline step...")
    Config.set_seed(seed_value)
    result2 = run_dummy_pipeline_step(seed_value)
    logger.debug(f"Second run results: {result2}")

    # Compare results
    torch_match = np.isclose(result1["torch_val"], result2["torch_val"])
    np_match = np.isclose(result1["np_val"], result2["np_val"])
    random_match = np.isclose(result1["random_val"], result2["random_val"])

    all_match = torch_match and np_match and random_match

    if all_match:
        logger.info("✅ Seed verification PASSED: All random states are reproducible.")
        logger.info(f"  - torch.rand: {result1['torch_val']:.8f}")
        logger.info(f"  - np.random.rand: {result1['np_val']:.8f}")
        logger.info(f"  - random.random: {result1['random_val']:.8f}")
    else:
        logger.error("❌ Seed verification FAILED: Random states are not reproducible.")
        if not torch_match:
            logger.error(f"  - torch.rand mismatch: {result1['torch_val']} != {result2['torch_val']}")
        if not np_match:
            logger.error(f"  - np.random.rand mismatch: {result1['np_val']} != {result2['np_val']}")
        if not random_match:
            logger.error(f"  - random.random mismatch: {result1['random_val']} != {result2['random_val']}")

    return all_match

def main():
    """
    Main entry point for the seed verification script.
    """
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Verify seed pinning for reproducibility")
    parser.add_argument("--seed", type=int, default=42, help="Seed value to verify")
    args = parser.parse_args()

    # Run verification
    success = verify_seed_pinning(args.seed)

    # Exit with appropriate code
    if success:
        logger.info("Seed verification completed successfully.")
        sys.exit(0)
    else:
        logger.error("Seed verification failed. Please check your seed configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()