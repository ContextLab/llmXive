import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics

# Configure logging for the validation gate
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ground_truth_validation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def run_validation_batch(config: SimulationConfig) -> bool:
    """
    Executes the validation routine from T013 on a fresh batch of generated data.
    
    This function acts as the Ground-Truth Validation Gate. It generates synthetic data
    for a representative subset of the simulation grid and validates that the
    generated statistics match the theoretical ground truth parameters within tolerance.
    
    Args:
        config: The simulation configuration object.
        
    Returns:
        bool: True if all validations pass (exit code 0), False otherwise.
        
    Raises:
        RuntimeError: If validation fails for any scenario in the batch.
    """
    logger.info("Starting Ground-Truth Validation Gate (T017b)...")
    logger.info(f"Configuration: Alpha={config.alpha}, Max Replicates={config.max_replicates}")
    
    # Define a representative batch of scenarios for validation
    # We test small, medium, and large sample sizes across distributions
    validation_scenarios = [
        {"n": 20, "dist": "normal", "effect": 0.0},
        {"n": 50, "dist": "normal", "effect": 0.5},
        {"n": 100, "dist": "uniform", "effect": 0.0},
        {"n": 200, "dist": "log_normal", "effect": 0.5},
        {"n": 500, "dist": "normal", "effect": 0.0},
    ]
    
    all_passed = True
    
    for scenario in validation_scenarios:
        n = scenario["n"]
        dist_type = scenario["dist"]
        effect_size = scenario["effect"]
        
        logger.info(f"Validating scenario: n={n}, dist={dist_type}, effect={effect_size}")
        
        try:
            # Generate fresh data
            group1, group2 = generate_data(
                sample_size=n,
                distribution_type=dist_type,
                effect_size=effect_size
            )
            
            # Run the validation routine from T013
            # This compares generated sample statistics to theoretical parameters
            # and raises an error on mismatch
            validation_result = validate_sample_statistics(
                group1, group2, dist_type, effect_size, n, config.alpha
            )
            
            if validation_result["passed"]:
                logger.info(f"  [PASS] Scenario n={n}, {dist_type}, effect={effect_size} verified.")
                logger.info(f"         Stats: {validation_result['details']}")
            else:
                logger.error(f"  [FAIL] Scenario n={n}, {dist_type}, effect={effect_size} failed.")
                logger.error(f"         Reason: {validation_result['reason']}")
                all_passed = False
                
        except Exception as e:
            logger.error(f"  [ERROR] Scenario n={n}, {dist_type}, effect={effect_size} raised exception: {str(e)}")
            all_passed = False
    
    if all_passed:
        logger.info("GROUND-TRUTH VALIDATION GATE PASSED: All batch scenarios verified.")
        logger.info("Proceeding to Monte Carlo simulation (T018) is authorized.")
        return True
    else:
        logger.error("GROUND-TRUTH VALIDATION GATE FAILED: One or more scenarios failed verification.")
        logger.error("Simulation pipeline halted. Fix data generation logic before proceeding.")
        return False

def main():
    """
    Main entry point for the ground truth validation script.
    """
    parser = argparse.ArgumentParser(description="Run Ground-Truth Validation Gate")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()
    
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Load configuration
    config = SimulationConfig()
    
    # Run validation
    success = run_validation_batch(config)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
