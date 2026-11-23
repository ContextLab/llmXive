"""
Script to generate test data for T008c.

This script invokes the polynomial test data generation function
and saves the output to data/results/test_data_polynomial.npy.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.benchmarks import generate_polynomial_test_data, save_data, DATA_RESULTS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for generating test data.
    
    This function:
    1. Generates polynomial test data with specified parameters
    2. Saves it to data/results/test_data_polynomial.npy
    3. Verifies the output file exists and is valid
    4. Returns 0 on success, 1 on failure
    """
    logger.info("Starting test data generation (T008c)")
    
    try:
        # Ensure output directory exists
        DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate test data with T008c specified parameters
        # SEED=42, N=1000, coeffs=[1, 0, -1] for x^2 - 1
        test_data = generate_polynomial_test_data(
            seed=42,
            n=1000,
            coeffs=[1, 0, -1],
            noise_std=0.1
        )
        
        # Save to file
        output_path = DATA_RESULTS_DIR / "test_data_polynomial.npy"
        save_data(test_data, str(output_path))
        
        # Verification: Check file exists
        if not output_path.exists():
            logger.error(f"VERIFICATION FAILED: Output file {output_path} does not exist")
            return 1
        
        # Verification: Check file is not empty
        if output_path.stat().st_size == 0:
            logger.error(f"VERIFICATION FAILED: Output file {output_path} is empty")
            return 1
        
        # Verification: Load and check shape
        import numpy as np
        loaded_data = np.load(output_path)
        if loaded_data.shape != (1000, 2):
            logger.error(f"VERIFICATION FAILED: Expected shape (1000, 2), got {loaded_data.shape}")
            return 1
        
        logger.info("T008c completed successfully")
        logger.info(f"Output: {output_path}")
        logger.info(f"Shape: {loaded_data.shape}")
        logger.info(f"X range: [{loaded_data[:, 0].min():.4f}, {loaded_data[:, 0].max():.4f}]")
        logger.info(f"Y range: [{loaded_data[:, 1].min():.4f}, {loaded_data[:, 1].max():.4f}]")
        
        return 0
        
    except Exception as e:
        logger.error(f"Test data generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
