"""
Verification script for seed reproducibility (Task T002c).

This script generates a random number using the pinned seeds from config.py
and logs the result. When run multiple times, the output must be identical.
"""
import logging
import sys
import random
import numpy as np
import torch

# Import the seed configuration from the project's config module
from config import set_global_seed, SEED

# Configure logging to output to stdout for verification
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for seed verification.
    Sets global seeds, generates deterministic values, and logs them.
    """
    logger.info(f"Starting seed verification for PROJ-318 (Task T002c).")
    logger.info(f"Using pinned seed value: {SEED}")

    # Apply the global seed to all relevant libraries
    set_global_seed()

    # Generate test values using each library to prove determinism
    # 1. Python random
    random_val = random.random()

    # 2. NumPy
    np_val = np.random.random()

    # 3. PyTorch
    torch_val = torch.rand(1).item()

    # Log the results
    logger.info(f"Python random result: {random_val}")
    logger.info(f"NumPy random result: {np_val}")
    logger.info(f"PyTorch random result: {torch_val}")

    logger.info("Seed verification completed successfully.")
    logger.info("If run twice, these values must be identical.")

    return 0

if __name__ == "__main__":
    sys.exit(main())