"""
Ground-Truth Validation Gate Runner.

Executes the validation routine from T013 (validate_sample_statistics) on a fresh
batch of generated data. This script MUST pass (exit code 0) before T018 can begin.
"""
import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Tuple

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics

logger = logging.getLogger(__name__)

def setup_logging(log_file: str = "logs/ground_truth_validation.log") -> None:
    """Configure logging to file and console."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_validation_batch(
    sample_sizes: List[int],
    distributions: List[str],
    effect_sizes: List[float]
) -> bool:
    """
    Run validation on a batch of configurations.
    
    Returns True if all validations pass, False otherwise.
    """
    all_passed = True
    config = SimulationConfig(
        sample_sizes=sample_sizes,
        distributions=distributions,
        effect_sizes=effect_sizes,
        alpha=0.05,
        max_replicates=10000,
        log_epsilon=1e-15
    )
    
    logger.info(f"Starting ground-truth validation batch with {config.sample_sizes} sample sizes, "
                f"{config.distributions} distributions, and {config.effect_sizes} effect sizes.")
    
    for n in config.sample_sizes:
        for dist in config.distributions:
            for eff in config.effect_sizes:
                # Use a deterministic seed for this validation batch
                seed = hash(f"{n}_{dist}_{eff}") % (2**32)
                
                try:
                    sample1, sample2 = generate_data(n, dist, eff, seed=seed)
                    
                    # Theoretical mean difference depends on distribution and effect size
                    if dist == "normal":
                        # Normal: mean2 = effect_size, mean1 = 0 -> diff = effect_size
                        expected_diff = eff
                    elif dist == "uniform":
                        # Uniform: mean1 = 0.5, mean2 = 0.5 + eff -> diff = effect_size
                        expected_diff = eff
                    elif dist == "log-normal":
                        # Log-normal: theoretical mean is exp(mu + sigma^2/2)
                        # mu1 = 0, mu2 = eff, sigma = 0.5
                        # mean1 = exp(0 + 0.125), mean2 = exp(eff + 0.125)
                        # diff = exp(0.125) * (exp(eff) - 1)
                        expected_diff = np.exp(0.125) * (np.exp(eff) - 1)
                    else:
                        raise ValueError(f"Unknown distribution: {dist}")
                    
                    # Run validation
                    validate_sample_statistics(
                        sample1, sample2, 
                        expected_diff, 
                        tolerance=1e-6, 
                        distribution=dist
                    )
                    
                    logger.info(f"Validation PASSED for n={n}, dist={dist}, eff={eff}")
                    
                except Exception as e:
                    logger.error(f"Validation FAILED for n={n}, dist={dist}, eff={eff}: {e}")
                    all_passed = False
    
    return all_passed

def main():
    """
    Entry point for the validation gate.
    Exits with 0 if validation passes, 1 if it fails.
    """
    parser = argparse.ArgumentParser(description="Run ground-truth validation gate")
    parser.add_argument("--sample-sizes", type=int, nargs="+", default=[10, 50, 100],
                        help="Sample sizes to validate")
    parser.add_argument("--distributions", type=str, nargs="+", 
                        default=["normal", "uniform", "log-normal"],
                        help="Distributions to validate")
    parser.add_argument("--effect-sizes", type=float, nargs="+", default=[0.0, 0.5],
                        help="Effect sizes to validate")
    parser.add_argument("--log-file", type=str, default="logs/ground_truth_validation.log",
                        help="Path to log file")
    
    args = parser.parse_args()
    
    setup_logging(args.log_file)
    
    logger.info("=" * 60)
    logger.info("GROUND-TRUTH VALIDATION GATE START")
    logger.info("=" * 60)
    
    success = run_validation_batch(
        args.sample_sizes,
        args.distributions,
        args.effect_sizes
    )
    
    logger.info("=" * 60)
    if success:
        logger.info("GROUND-TRUTH VALIDATION GATE: PASSED (exit code 0)")
        logger.info("All generated data verified against theoretical parameters.")
        logger.info("Pipeline can proceed to Monte Carlo simulation (T018).")
        sys.exit(0)
    else:
        logger.error("GROUND-TRUTH VALIDATION GATE: FAILED (exit code 1)")
        logger.error("Data generation does not match ground truth. Aborting pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    main()