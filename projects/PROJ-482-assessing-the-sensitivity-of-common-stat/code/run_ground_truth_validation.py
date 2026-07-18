"""
Ground-Truth Validation Gate Script (Task T017b).

This script executes the validation routine from T013 (validate_sample_statistics)
on a fresh batch of generated data. It serves as a blocking gate before the
Monte Carlo simulation loop (T018) can begin.

Deliverable: A log entry confirming ground-truth parameters were verified for
the current configuration batch. The script exits with code 0 on success,
or non-zero if validation fails.
"""
import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics

# Configure logging to ensure the "log entry" requirement is met
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'ground_truth_validation.log'))
    ]
)
logger = logging.getLogger("GroundTruthValidation")

def run_validation_batch(config: SimulationConfig, sample_sizes: List[int], distributions: List[str]) -> bool:
    """
    Run validation on a batch of configurations.

    Returns True if all validations pass, False otherwise.
    """
    grid = get_simulation_grid(
        sample_sizes=sample_sizes,
        distributions=distributions,
        test_types=['t-test'], # Validation doesn't need test execution, just data gen
        effect_sizes=[0.0, 0.5],
        n_replicates=5 # Small batch for validation gate
    )

    logger.info(f"Starting Ground-Truth Validation Batch for {len(grid)} configurations.")
    all_passed = True

    for i, scenario in enumerate(grid):
        try:
            # Generate data for this scenario
            # Note: generate_data returns a dict with 'group1', 'group2' arrays and metadata
            data_result = generate_data(
                n=scenario['sample_size'],
                distribution=scenario['distribution'],
                effect_size=scenario['effect_size'],
                seed=i # Deterministic seed for reproducibility in validation
            )

            # Call the validation routine from T013
            # This function raises an error or returns success if stats match theoretical params
            validation_result = validate_sample_statistics(
                group1=data_result['group1'],
                group2=data_result['group2'],
                expected_effect=scenario['effect_size'],
                distribution=scenario['distribution']
            )

            if validation_result['passed']:
                logger.info(f"VALIDATION PASSED: n={scenario['sample_size']}, dist={scenario['distribution']}, effect={scenario['effect_size']}")
            else:
                logger.error(f"VALIDATION FAILED: n={scenario['sample_size']}, dist={scenario['distribution']}, effect={scenario['effect_size']}. Reason: {validation_result['reason']}")
                all_passed = False

        except Exception as e:
            logger.error(f"VALIDATION ERROR: n={scenario['sample_size']}, dist={scenario['distribution']}. Exception: {str(e)}")
            all_passed = False

    return all_passed

def main():
    parser = argparse.ArgumentParser(description="Run Ground-Truth Validation Gate (T017b)")
    parser.add_argument('--n-sizes', type=str, default="10,50,100", help="Comma-separated list of sample sizes to validate")
    parser.add_argument('--distributions', type=str, default="normal,uniform,log-normal", help="Comma-separated list of distributions to validate")
    args = parser.parse_args()

    # Parse arguments
    sample_sizes = [int(x.strip()) for x in args.n_sizes.split(',')]
    distributions = [x.strip() for x in args.distributions.split(',')]

    # Initialize config (uses defaults from config.py)
    config = SimulationConfig()

    logger.info(f"--- GROUND-TRUTH VALIDATION GATE STARTED ---")
    logger.info(f"Configuration: Sample Sizes={sample_sizes}, Distributions={distributions}")

    success = run_validation_batch(config, sample_sizes, distributions)

    if success:
        logger.info("--- GROUND-TRUTH VALIDATION GATE PASSED ---")
        logger.info("All generated data matches theoretical ground truth within tolerance.")
        sys.exit(0)
    else:
        logger.error("--- GROUND-TRUTH VALIDATION GATE FAILED ---")
        logger.error("One or more configurations failed validation. Aborting simulation pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    main()
