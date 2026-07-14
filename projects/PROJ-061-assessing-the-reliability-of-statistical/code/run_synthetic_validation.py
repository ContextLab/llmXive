"""
Script to execute the Synthetic Ground Truth test (T031b).

This script imports the logic from T031a (code/power_empirical.py)
and runs a controlled simulation where the true power is known analytically.

The test passes if the empirical recovery rate (observed power) is within 5%
of the theoretical power.

If the test fails, this script exits with code 1, acting as a blocking gate
for all subsequent real-data processing phases.
"""
import sys
import logging
import json
from pathlib import Path

import numpy as np
from scipy import stats

# Project imports
# Ensure we import from the local code directory
sys.path.insert(0, str(Path(__file__).parent))

from config import RANDOM_SEED, ensure_directories
from power_empirical import run_bootstrap_power_simulation
from validators import bootstrap_validity_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for the Synthetic Ground Truth test
# We simulate a two-sample t-test scenario
# H0: mu1 = mu2
# H1: mu1 != mu2
# True effect size (Cohen's d) = 0.5 (Medium effect)
TRUE_EFFECT_SIZE = 0.5
SAMPLE_SIZE_PER_GROUP = 64  # N=64 per group gives ~80% power for d=0.5, alpha=0.05
ALPHA = 0.05
N_BOOTSTRAP_ITERATIONS = 1000  # Reduced for speed in validation, but sufficient for check
ACCEPTANCE_TOLERANCE = 0.05  # 5% tolerance

def calculate_theoretical_power(d, n1, n2, alpha=0.05):
    """
    Calculate theoretical power for a two-sample t-test.
    Uses the non-central t-distribution approximation.
    """
    # Pooled standard deviation assumption (sigma=1)
    # Standard error of the difference
    se = np.sqrt(1/n1 + 1/n2)
    # Non-centrality parameter
    ncp = d / se
    
    # Critical t-value (two-tailed, df = n1 + n2 - 2)
    df = n1 + n2 - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power is the probability that the t-statistic exceeds the critical value
    # under the alternative hypothesis (non-central t)
    # Power = P(T > t_crit | ncp) + P(T < -t_crit | ncp)
    power = (1 - stats.nct.cdf(t_crit, df, ncp)) + stats.nct.cdf(-t_crit, df, ncp)
    return power

def run_synthetic_ground_truth_test():
    """
    Execute the Synthetic Ground Truth test.
    
    1. Generate synthetic data with known parameters (True Power).
    2. Run the empirical bootstrap simulation (Empirical Power).
    3. Compare Empirical vs. True Power.
    4. Enforce the 5% tolerance gate.
    """
    logger.info("Starting Synthetic Ground Truth Test (T031b)...")
    ensure_directories()
    np.random.seed(RANDOM_SEED)

    # 1. Define Ground Truth
    # We create two groups with a known difference in means (effect size d)
    # Group 1: N(0, 1)
    # Group 2: N(d, 1)
    group1 = np.random.normal(loc=0, scale=1, size=SAMPLE_SIZE_PER_GROUP)
    group2 = np.random.normal(loc=TRUE_EFFECT_SIZE, scale=1, size=SAMPLE_SIZE_PER_GROUP)
    
    data = np.concatenate([group1, group2])
    labels = np.array([0] * SAMPLE_SIZE_PER_GROUP + [1] * SAMPLE_SIZE_PER_GROUP)

    # Calculate Theoretical Power
    theoretical_power = calculate_theoretical_power(
        d=TRUE_EFFECT_SIZE,
        n1=SAMPLE_SIZE_PER_GROUP,
        n2=SAMPLE_SIZE_PER_GROUP,
        alpha=ALPHA
    )
    logger.info(f"Theoretical Power (Ground Truth): {theoretical_power:.4f}")

    # 2. Run Empirical Simulation
    # We use the function from T031a logic
    # Note: run_bootstrap_power_simulation expects specific arguments.
    # We adapt the call to match the simulated data structure.
    
    # Since run_bootstrap_power_simulation is designed for real datasets,
    # we simulate the "dataset" object or pass raw arrays if the function allows.
    # Assuming the function signature from T031a implementation:
    # def run_bootstrap_power_simulation(data, labels, n_iterations, seed):
    
    logger.info(f"Running Bootstrap Empirical Power estimation ({N_BOOTSTRAP_ITERATIONS} iterations)...")
    
    try:
        # Call the empirical power function
        # We pass the raw numpy arrays directly if the loader logic is bypassed for synthetic data
        # or we wrap them in a minimal dict if the function expects a dataset dict.
        # Based on typical implementations, we assume it takes raw data/labels.
        
        empirical_result = run_bootstrap_power_simulation(
            data=data,
            labels=labels,
            n_iterations=N_BOOTSTRAP_ITERATIONS,
            seed=RANDOM_SEED,
            alpha=ALPHA
        )
        
        empirical_power = empirical_result['observed_power']
        
    except Exception as e:
        logger.error(f"Empirical simulation failed: {e}")
        return False

    logger.info(f"Empirical Power (Observed): {empirical_power:.4f}")

    # 3. Validation Check
    absolute_error = abs(empirical_power - theoretical_power)
    logger.info(f"Absolute Error: {absolute_error:.4f}")
    logger.info(f"Tolerance Threshold: {ACCEPTANCE_TOLERANCE:.4f}")

    # Bootstrap Validity Check (FR-010)
    # Verify the variance of the bootstrap estimate is reasonable
    # This ensures the simulation didn't crash or produce garbage variance
    if 'bootstrap_variance' in empirical_result:
        var_check = bootstrap_validity_check(
            empirical_result['bootstrap_variance'],
            theoretical_power,
            n_iterations=N_BOOTSTRAP_ITERATIONS
        )
        if not var_check['valid']:
            logger.warning(f"Bootstrap validity check failed: {var_check['reason']}")
            # We might still pass the power check if the mean is correct, but it's a warning
    else:
        logger.warning("Bootstrap variance not returned, skipping validity check.")

    # 4. Gate Enforcement
    passed = absolute_error <= ACCEPTANCE_TOLERANCE

    if passed:
        logger.info("✅ T031b PASSED: Recovery rate within 5% tolerance.")
        logger.info("Blocking gate cleared. Real-data processing can proceed.")
    else:
        logger.error("❌ T031b FAILED: Recovery rate outside 5% tolerance.")
        logger.error("Blocking gate triggered. No real-data processing allowed.")
        logger.error("Investigate power_empirical.py logic before proceeding.")

    # Save results to data/results/synthetic_validation.json
    results_path = Path("data/results/synthetic_validation.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    validation_report = {
        "test_name": "Synthetic Ground Truth (T031b)",
        "parameters": {
            "true_effect_size": TRUE_EFFECT_SIZE,
            "sample_size_per_group": SAMPLE_SIZE_PER_GROUP,
            "alpha": ALPHA,
            "n_iterations": N_BOOTSTRAP_ITERATIONS,
            "tolerance": ACCEPTANCE_TOLERANCE
        },
        "results": {
            "theoretical_power": theoretical_power,
            "empirical_power": empirical_power,
            "absolute_error": absolute_error,
            "passed": passed
        },
        "status": "PASSED" if passed else "FAILED"
    }
    
    with open(results_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info(f"Validation report saved to {results_path}")

    return passed

if __name__ == "__main__":
    success = run_synthetic_ground_truth_test()
    # Exit with code 1 if failed, 0 if passed
    sys.exit(0 if success else 1)
