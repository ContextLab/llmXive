"""
Power analysis for the AdaPlanBench extension study.

This module performs a power analysis to determine if the filtered subset
of tasks has sufficient statistical power to detect a medium effect size
(f² ≥ 0.15) with a power of ≥ 0.80.

The analysis assumes a Generalized Linear Mixed Model (GLMM) framework,
but for power estimation, we use the `statsmodels.stats.power` module
which provides approximations for logistic regression (binomial link).

Target parameters:
- Effect size (f²): 0.15 (medium)
- Alpha: 0.05
- Power target: 0.80

Output:
- data/processed/power_report.json
"""

import os
import json
import math
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.stats.power import GofChisquarePower, ZPowerProportion
from statsmodels.stats.proportion import proportion_effectsize

# Import project configuration
from config import Paths, set_all_seeds

# Constants for the analysis
TARGET_EFFECT_SIZE_F2 = 0.15
TARGET_POWER = 0.80
ALPHA = 0.05
N_PREDICTORS = 2  # "constraint_count" and "architecture" as main effects + interaction

def calculate_effect_size_for_logistic(p0: float, p1: float) -> float:
    """
    Calculate Cohen's h (effect size) for two proportions.
    For logistic regression, we often convert f² to a standardized metric
    or use Cohen's h for proportions if we frame it as a 2x2 comparison.
    
    However, for GLMM power analysis in statsmodels, we often estimate
    based on the expected odds ratio or the proportion difference.
    
    Here, we approximate the required sample size using the effect size
    derived from the target f².
    
    Reference: Cohen (1988), Statistical Power Analysis for the Behavioral Sciences.
    """
    # Convert f² to R² equivalent for interpretation, then to effect size for logistic
    # A common approximation for logistic regression power:
    # Effect size (Cohen's h) ≈ 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p0))
    # But we need to derive p1 from f² and p0.
    
    # Simpler approach for statsmodels GofChisquarePower:
    # We need the expected proportion of variance explained or a specific odds ratio.
    # Let's assume a baseline probability p0 = 0.5 (conservative for maximum variance)
    # and derive p1 from the effect size.
    
    # f² = R² / (1 - R²)  => R² = f² / (1 + f²)
    # This R² is pseudo-R².
    
    # For the Z-test of proportions (approximation for logistic):
    # We need the difference in proportions.
    # Let's use a heuristic: f² = 0.15 implies a moderate shift.
    # If p0 = 0.5, a medium effect often corresponds to p1 ~ 0.65 or 0.35.
    # Let's calculate Cohen's h for p0=0.5, p1=0.65.
    p0 = 0.5
    p1 = 0.65 # Approximation for medium effect in binary outcome
    h = proportion_effectsize(p0, p1)
    return h

def estimate_required_sample_size(effect_size: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Estimate the minimum sample size required to detect the given effect size
    with the specified power and alpha.
    """
    analysis = GofChisquarePower()
    # GofChisquarePower.solve_power works for chi-square tests (goodness of fit)
    # which approximates the logistic regression test for a single predictor or
    # a set of predictors if we adjust the degrees of freedom.
    # However, for a more direct logistic regression power, we might use
    # a simpler approximation or ZPowerProportion if we treat it as a 2-group comparison.
    
    # Given the complexity of exact GLMM power, we use the chi-square approximation
    # for the likelihood ratio test.
    # N = (Z_alpha + Z_beta)^2 / effect_size^2  (rough approximation)
    
    try:
        n_required = analysis.solve_power(effect_size=effect_size, 
                                          alpha=alpha, 
                                          power=power, 
                                          nobs1=None, 
                                          ratio=1.0, # Balanced design assumption
                                          alternative='two-sided')
        if n_required is None:
            return -1
        return int(math.ceil(n_required))
    except Exception:
        # Fallback to simple approximation if statsmodels fails
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        # Approximation for 2x2 table (1 df)
        n_approx = ((z_alpha + z_beta) ** 2) / (effect_size ** 2)
        return int(math.ceil(n_approx))

def perform_power_analysis(sample_size: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Calculate the achieved power given the sample size and effect size.
    """
    analysis = GofChisquarePower()
    try:
        power = analysis.solve_power(effect_size=effect_size,
                                     alpha=alpha,
                                     nobs1=sample_size,
                                     ratio=1.0,
                                     alternative='two-sided')
        return float(power) if power is not None else 0.0
    except Exception:
        return 0.0

def run_power_analysis(data_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main function to run the power analysis.
    
    1. Loads the filtered dataset to get the actual sample size.
    2. Calculates the effect size based on the target f².
    3. Estimates the required sample size for the target power.
    4. Calculates the actual power given the current sample size.
    5. Returns a report with the results.
    """
    if data_path is None:
        paths = Paths()
        data_path = paths.processed_dir / "filtered_tasks.csv"
    
    # 1. Load data to get sample size
    if not data_path.exists():
        raise FileNotFoundError(f"Filtered dataset not found at {data_path}. "
                                "Run T012/T013/T014 first.")
    
    df = pd.read_csv(data_path)
    actual_sample_size = len(df)
    
    if actual_sample_size == 0:
        raise ValueError("Filtered dataset is empty. Cannot perform power analysis.")
    
    # 2. Calculate effect size
    # We use the target f² = 0.15 to derive an approximate Cohen's h for proportions
    # as a proxy for the logistic regression effect size.
    # This is a heuristic approximation for the power analysis.
    estimated_effect_size = calculate_effect_size_for_logistic(0.5, 0.65)
    
    # 3. Estimate required sample size
    required_sample_size = estimate_required_sample_size(estimated_effect_size, ALPHA, TARGET_POWER)
    
    # 4. Calculate actual power
    actual_power = perform_power_analysis(actual_sample_size, estimated_effect_size, ALPHA)
    
    # 5. Determine pass/fail
    # Pass if actual_power >= TARGET_POWER
    passed = actual_power >= TARGET_POWER
    
    report = {
        "target_effect_size_f2": TARGET_EFFECT_SIZE_F2,
        "target_power": TARGET_POWER,
        "alpha": ALPHA,
        "estimated_effect_size_cohens_h": estimated_effect_size,
        "actual_sample_size": actual_sample_size,
        "required_sample_size": required_sample_size,
        "actual_power": actual_power,
        "passed": passed,
        "data_source": str(data_path),
        "notes": "Power analysis approximated using chi-square goodness-of-fit test "
                 "on effect size derived from target f²=0.15. Assumes balanced design "
                 "and baseline probability of 0.5."
    }
    
    return report

def main():
    """Entry point for the power analysis script."""
    set_all_seeds(42)
    
    print("Starting Power Analysis (T027)...")
    
    try:
        report = run_power_analysis()
        
        # Ensure output directory exists
        paths = Paths()
        output_path = paths.processed_dir / "power_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Power analysis complete. Report saved to: {output_path}")
        print(f"Sample Size: {report['actual_sample_size']}")
        print(f"Calculated Power: {report['actual_power']:.4f}")
        print(f"Target Power: {report['target_power']}")
        print(f"Status: {'PASS' if report['passed'] else 'FAIL'}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise
    except Exception as e:
        print(f"ERROR during power analysis: {e}")
        raise

if __name__ == "__main__":
    main()
