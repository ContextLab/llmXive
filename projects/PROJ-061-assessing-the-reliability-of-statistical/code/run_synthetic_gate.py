"""
Execution script for the Synthetic Ground Truth test (T031b).

This script acts as a blocking gate. It executes the synthetic ground truth
test defined in T031a (via `power_empirical.run_synthetic_ground_truth_test`).

If the recovery rate is NOT within 5% of the true power, the script exits
with a non-zero status code and prints a failure message. No real-data
processing (Phase 3+) can begin until this passes.

Usage:
    python code/run_synthetic_gate.py
"""
import json
import sys
import logging
from pathlib import Path
import numpy as np
from scipy import stats

# Import from project modules
from power_empirical import run_synthetic_ground_truth_test
from config import RANDOM_SEED
from utils import setup_logging, ensure_file_directory

# Configure logging
logger = setup_logging("synthetic_gate", level=logging.INFO)

def main():
    """
    Execute the Synthetic Ground Truth test and enforce the 5% recovery rate gate.
    """
    logger.info("Starting Synthetic Ground Truth validation (T031b)...")
    logger.info(f"Random Seed: {RANDOM_SEED}")

    try:
        # Run the test logic defined in T031a
        # This function returns a dict with 'true_power', 'empirical_power', 'recovery_rate', 'passed'
        result = run_synthetic_ground_truth_test()
        
        if result is None:
            raise RuntimeError("run_synthetic_ground_truth_test returned None. Implementation missing or failed.")

        true_power = result.get('true_power')
        empirical_power = result.get('empirical_power')
        recovery_rate = result.get('recovery_rate')
        passed = result.get('passed')
        
        logger.info(f"True Power: {true_power:.4f}")
        logger.info(f"Empirical Power (Bootstrap): {empirical_power:.4f}")
        logger.info(f"Recovery Rate (|True - Empirical| / True): {recovery_rate:.4f}")
        
        # Define output directory and file
        output_dir = Path("data/results")
        ensure_file_directory(output_dir)
        output_file = output_dir / "synthetic_ground_truth_result.json"
        
        # Write the result to disk for audit trail
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_file}")
        
        # Gate Logic
        if passed:
            logger.info("✅ VALIDATION PASSED: Recovery rate is within 5%.")
            logger.info("Proceeding to Phase 3 (Real Data Processing) is UNBLOCKED.")
            return 0
        else:
            logger.error("❌ VALIDATION FAILED: Recovery rate exceeds 5% threshold.")
            logger.error(f"Threshold: 0.05, Actual: {recovery_rate:.4f}")
            logger.error("BLOCKING: No real-data processing can begin.")
            logger.error("Please review T031a implementation and bootstrap parameters.")
            return 1

    except Exception as e:
        logger.error(f"❌ VALIDATION CRASHED: {str(e)}")
        logger.error("BLOCKING: Execution failed. Cannot proceed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
