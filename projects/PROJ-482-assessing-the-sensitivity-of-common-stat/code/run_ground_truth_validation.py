"""
Ground-Truth Validation Gate Script (Task T017b).

This script executes the validation routine from T013 on a fresh batch of
generated data before the Monte Carlo loop begins. It acts as a blocking
gate: if validation fails, the script exits with code 1, preventing
downstream simulation tasks (T018+) from running.

Deliverable: A log entry confirming ground-truth parameters were verified
for the current configuration batch.
"""
import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics

# Configure logging to output to both console and a specific log file
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "ground_truth_validation.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_validation_batch(config: SimulationConfig) -> bool:
    """
    Runs the ground-truth validation on a representative batch of configurations.

    Args:
        config: The simulation configuration object.

    Returns:
        True if all validations pass, False otherwise.
    """
    logger.info("Starting Ground-Truth Validation Batch...")
    
    # Get a subset of the simulation grid for validation (e.g., first few sample sizes)
    # We validate across distributions and test types to ensure robustness
    # before the full Monte Carlo loop.
    validation_configs = get_simulation_grid(
        sample_sizes=[10, 50, 100], # Small representative set
        distributions=config.distributions,
        effect_sizes=[0.0, 0.5],
        test_types=['t_test'] # T-test is the primary baseline for validation
    )

    all_passed = True
    failed_cases = []

    for scenario in validation_configs:
        try:
            # Generate fresh data for this scenario
            # data_generator.generate_data handles the logic for Null/Alt hypotheses
            data = generate_data(
                n=scenario['sample_size'],
                distribution_type=scenario['distribution_type'],
                effect_size=scenario['effect_size'],
                seed=42 # Deterministic seed for validation reproducibility
            )

            # Execute the validation routine from T013
            # This function compares generated sample statistics to theoretical parameters
            # and raises an error if they don't match within tolerance.
            validation_result = validate_sample_statistics(
                data, 
                scenario['distribution_type'], 
                scenario['effect_size'],
                tolerance=1e-4 # Slightly looser for Monte Carlo generation variance, but strict enough
            )

            logger.info(
                f"PASS: n={scenario['sample_size']}, "
                f"dist={scenario['distribution_type']}, "
                f"effect={scenario['effect_size']}, "
                f"stats={validation_result}"
            )

        except Exception as e:
            logger.error(
                f"FAIL: n={scenario['sample_size']}, "
                f"dist={scenario['distribution_type']}, "
                f"effect={scenario['effect_size']} -> {str(e)}"
            )
            all_passed = False
            failed_cases.append({
                "scenario": scenario,
                "error": str(e)
            })

    if all_passed:
        logger.info("GROUND-TRUTH VALIDATION GATE: PASSED. All scenarios verified.")
        logger.info("Proceeding to Monte Carlo simulation (T018).")
    else:
        logger.error(f"GROUND-TRUTH VALIDATION GATE: FAILED. {len(failed_cases)} scenarios failed.")
        for fc in failed_cases:
            logger.error(f"  - {fc['scenario']}: {fc['error']}")
    
    return all_passed

def main():
    """Main entry point for the validation gate."""
    parser = argparse.ArgumentParser(description="Run Ground-Truth Validation Gate (T017b)")
    parser.add_argument("--config", type=str, default="default", help="Configuration profile name")
    args = parser.parse_args()

    # Initialize config
    # In a real pipeline, this might load from a file, but we use the standard config here
    config = SimulationConfig()
    
    # Run the validation
    success = run_validation_batch(config)

    # Exit with appropriate code
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()