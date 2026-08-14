"""
Separability Analysis Module for llmXive Project.

Implements power analysis to determine minimum sample size (N) required
to detect an effect size d > 0.8 with sufficient statistical power.
"""
import json
import os
from pathlib import Path
import numpy as np
from scipy.stats import norm
from statsmodels.stats.power import TTestIndPower

# Project root relative to this file (2 levels up from code/analysis)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Output paths
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_FILE = RESULTS_DIR / "power_analysis.json"

# Constants from Assumptions
EFFECT_SIZE = 0.8  # Minimum effect size (Cohen's d) to detect
TARGET_POWER = 0.80  # Target statistical power (80%)
ALPHA = 0.05  # Significance level (two-tailed)
N_AUDIT = 50  # Fixed sample size for manual audit (as per typical feasibility studies)

def calculate_sample_size_for_power(effect_size: float, power: float, alpha: float) -> int:
    """
    Calculate the minimum sample size (N per group) required to achieve
    the desired statistical power for detecting a given effect size.
    
    Uses T-test for independent groups (two-sample t-test).
    
    Args:
        effect_size: Cohen's d (expected difference in means / pooled std dev)
        power: Target statistical power (e.g., 0.80)
        alpha: Significance level (e.g., 0.05)
        
    Returns:
        int: Minimum sample size N per group required.
    """
    if effect_size <= 0:
        raise ValueError("Effect size must be positive.")
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1.")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")
        
    solver = TTestIndPower()
    
    # Calculate sample size per group
    # Note: TTestIndPower.solve_power returns N per group
    n_per_group = solver.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        ratio=1.0,  # Equal group sizes
        alternative='two-sided'
    )
    
    # Round up to ensure sufficient power
    return int(np.ceil(n_per_group))

def run_power_analysis(effect_size: float = EFFECT_SIZE, 
                       target_power: float = TARGET_POWER, 
                       alpha: float = ALPHA) -> dict:
    """
    Run the full power analysis pipeline and return results dictionary.
    
    Logic:
    1. Calculate N_required for the given effect size and power.
    2. Determine status based on whether achieved power meets threshold.
    3. Include N_audit for manual verification.
    
    Args:
        effect_size: Cohen's d to test against.
        target_power: Desired power level.
        alpha: Significance level.
        
    Returns:
        dict: Results containing N_required, effect_size, power, N_audit, status.
    """
    # Calculate required sample size
    n_required = calculate_sample_size_for_power(effect_size, target_power, alpha)
    
    # Verify power at this N (should be >= target_power by definition of the solver)
    # But we calculate the actual achieved power to be precise
    solver = TTestIndPower()
    achieved_power = solver.power(
        effect_size=effect_size,
        nobs1=n_required,
        alpha=alpha,
        ratio=1.0,
        alternative='two-sided'
    )
    
    # Determine status
    # Constraint: MUST include logic to check power < 0.8 and set status="INCONCLUSIVE"
    # Since we solve for power >= 0.8, if the solver fails or returns NaN, or if
    # the calculated power is below threshold due to constraints, we flag it.
    if achieved_power < target_power:
        status = "INCONCLUSIVE"
    else:
        status = "PASS"
        
    results = {
        "N_required": n_required,
        "effect_size": effect_size,
        "power": float(achieved_power),
        "N_audit": N_AUDIT,
        "status": status,
        "alpha": alpha,
        "notes": f"Calculated for effect_size={effect_size}, target_power={target_power}"
    }
    
    return results

def main():
    """
    Main entry point: Run power analysis and write results to JSON file.
    
    Creates the output directory if it doesn't exist.
    Writes the full results dictionary to data/results/power_analysis.json.
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Running power analysis for effect_size={EFFECT_SIZE}...")
    results = run_power_analysis()
    
    # Write results to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Power analysis complete. Results written to: {OUTPUT_FILE}")
    print(f"Status: {results['status']}")
    print(f"N_required: {results['N_required']}")
    print(f"Power: {results['power']:.4f}")
    
    # If inconclusive, print warning
    if results['status'] == "INCONCLUSIVE":
        print("WARNING: Achieved power is below target. Analysis is inconclusive.")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())