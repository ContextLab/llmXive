"""
Synthetic Ground Truth Execution Gate (T031b)

This script executes the Synthetic Ground Truth test defined in T031a (power_empirical.py).
It acts as a blocking gate: if the recovery rate is not within 5% of the true power,
the script exits with a failure code, preventing any real-data processing (Phase 3+) from beginning.

Output:
  - Prints the recovery rate and pass/fail status to stdout.
  - Writes the full result to `data/results/synthetic_gate_result.json`.
  - Exits with code 0 on pass, 1 on fail.
"""
import json
import sys
import logging
from pathlib import Path

import numpy as np
from scipy import stats

# Import the specific function from the implemented module
from power_empirical import run_synthetic_ground_truth_test

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Synthetic Ground Truth Gate (T031b)...")
    
    # Ensure output directory exists
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "synthetic_gate_result.json"

    try:
        # Execute the test logic defined in T031a
        # This function generates synthetic data with known parameters,
        # runs bootstrap, and compares recovered power to true power.
        result = run_synthetic_ground_truth_test()
        
        recovery_rate = result.get("recovery_rate", 0.0)
        true_power = result.get("true_power", 0.0)
        empirical_power = result.get("empirical_power", 0.0)
        absolute_error = result.get("absolute_error", 0.0)
        passed = result.get("passed", False)
        message = result.get("message", "")

        # Log results
        logger.info(f"True Power: {true_power:.4f}")
        logger.info(f"Empirical Power: {empirical_power:.4f}")
        logger.info(f"Absolute Error: {absolute_error:.4f}")
        logger.info(f"Recovery Rate (within 5%): {recovery_rate:.4f}")
        
        if passed:
            logger.info("✅ GATE PASSED: Recovery rate is within 5%. Proceeding to real-data processing.")
        else:
            logger.error("❌ GATE FAILED: Recovery rate is NOT within 5%. Blocking real-data processing.")

        # Write results to disk
        gate_result = {
            "task_id": "T031b",
            "status": "passed" if passed else "failed",
            "true_power": true_power,
            "empirical_power": empirical_power,
            "absolute_error": absolute_error,
            "recovery_rate": recovery_rate,
            "message": message,
            "timestamp": None  # Can be populated if needed
        }
        
        with open(output_path, "w") as f:
            json.dump(gate_result, f, indent=2)
        
        logger.info(f"Results written to {output_path}")

        # Exit with appropriate code for CI/CD gating
        sys.exit(0 if passed else 1)

    except Exception as e:
        logger.error(f"Gate execution failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
