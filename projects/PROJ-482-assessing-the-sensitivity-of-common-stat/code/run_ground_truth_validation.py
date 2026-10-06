"""
Ground-Truth Validation Gate Script (T017b)

This script executes the validation routine from T013 on a fresh batch of generated data
before starting the Monte Carlo loop. It ensures that the data generator is producing
data that matches theoretical parameters within acceptable sample tolerances.

Usage:
    python code/run_ground_truth_validation.py [--config code/config.yaml]

Exit Codes:
    0: Validation passed
    1: Validation failed or error occurred
"""

import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics

def setup_logging(log_file: str = "logs/validation.log") -> logging.Logger:
    """Configure logging for the validation script."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("GroundTruthValidation")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def run_validation_batch(
    scenarios: List[Dict[str, Any]],
    logger: logging.Logger,
    n_replicates: int = 100
) -> bool:
    """
    Run validation on a batch of scenarios.

    Args:
        scenarios: List of scenario dictionaries (n, dist, effect)
        logger: Logger instance
        n_replicates: Number of replicates to generate for validation

    Returns:
        True if all validations passed, False otherwise
    """
    all_passed = True

    for scenario in scenarios:
        n = scenario['n']
        dist = scenario['dist']
        effect = scenario['effect']

        logger.info(f"Validating scenario: n={n}, dist={dist}, effect={effect}")

        try:
            # Generate a fresh batch of data for validation
            # We use multiple replicates to ensure sample statistics are stable
            validation_passed = True

            for rep in range(n_replicates):
                seed = 42 + rep  # Deterministic seed for reproducibility
                sample1, sample2 = generate_data(n, dist, effect, seed=seed)

                # Validate sample statistics against theoretical parameters
                try:
                    validate_sample_statistics(sample1, sample2, dist, effect, n)
                except ValueError as e:
                    logger.warning(f"  -> Replicate {rep} failed: {e}")
                    validation_passed = False
                    break

            if validation_passed:
                logger.info(f"  -> PASSED: Ground-truth verified for this configuration")
            else:
                logger.error(f"  -> FAILED: Sample statistics did not match theoretical parameters")
                all_passed = False

        except Exception as e:
            logger.error(f"  -> ERROR: {e}")
            all_passed = False

    return all_passed

def main():
    """Main entry point for the validation gate."""
    parser = argparse.ArgumentParser(description="Ground-Truth Validation Gate")
    parser.add_argument("--config", type=str, default="code/config.yaml",
                      help="Path to configuration file")
    parser.add_argument("--log", type=str, default="logs/validation.log",
                      help="Path to log file")
    parser.add_argument("--replicates", type=int, default=100,
                      help="Number of validation replicates per scenario")
    args = parser.parse_args()

    logger = setup_logging(args.log)

    logger.info("=" * 60)
    logger.info("Starting Ground-Truth Validation Gate (T017b)")
    logger.info("=" * 60)

    # Define a representative batch of scenarios to validate
    # These cover the range of sample sizes and distributions used in the simulation
    validation_scenarios = [
        {'n': 10, 'dist': 'normal', 'effect': 0.0},
        {'n': 10, 'dist': 'normal', 'effect': 0.5},
        {'n': 30, 'dist': 'normal', 'effect': 0.0},
        {'n': 30, 'dist': 'normal', 'effect': 0.5},
        {'n': 50, 'dist': 'normal', 'effect': 0.0},
        {'n': 50, 'dist': 'normal', 'effect': 0.5},
        {'n': 100, 'dist': 'normal', 'effect': 0.0},
        {'n': 100, 'dist': 'normal', 'effect': 0.5},
        {'n': 10, 'dist': 'uniform', 'effect': 0.0},
        {'n': 10, 'dist': 'uniform', 'effect': 0.5},
        {'n': 30, 'dist': 'lognormal', 'effect': 0.0},
        {'n': 30, 'dist': 'lognormal', 'effect': 0.5},
    ]

    # Run validation
    success = run_validation_batch(validation_scenarios, logger, args.replicates)

    if success:
        logger.info("=" * 60)
        logger.info("VALIDATION PASSED: All ground-truth parameters verified")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("VALIDATION FAILED: Some ground-truth parameters did not match")
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()