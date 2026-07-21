"""
Power Analysis Module for llmXive.

Performs power analysis on the filtered dataset to determine if the sample size
is sufficient to detect the target effect size (Cohen's f² >= 0.15) with power >= 0.80
for the planned GLMM.

Methodology:
- Uses statsmodels.stats.power for G*Power-like calculations.
- For GLMMs with binary outcomes, we approximate using the F-test for logistic regression
  or the chi-square test for proportions, as direct GLMM power analysis is computationally
  intensive and often approximated by the fixed effects component.
- We calculate the detectable effect size given the sample size and target power,
  or conversely, the power given the target effect size and sample size.
"""
import os
import json
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import config for paths
from config import Paths, get_analysis_config, get_dataset_config

# Import statsmodels for power analysis
# We use GofChisquarePower or FTestAnovaPower as proxies for GLMM fixed effects
# Specifically, for a binary outcome (violation) and interaction term (architecture * constraint_count),
# we can approximate the power using the F-test for the interaction effect in a linear model
# or the Chi-square for the proportion difference if we bin the data.
# Given the task requirement for Cohen's f², FTestAnovaPower is the most appropriate proxy
# for the "effect of the interaction" in a mixed model context.
try:
    from statsmodels.stats.power import FTestAnovaPower, GofChisquarePower
    from statsmodels.stats.proportion import proportion_effectsize
except ImportError:
    raise ImportError(
        "statsmodels is required for power analysis. "
        "Install it via: pip install statsmodels"
    )

def calculate_effect_size_for_logistic(
    p1: float,
    p2: float
) -> float:
    """
    Calculate Cohen's h (effect size for proportions) and convert to approximate f².
    
    Cohen's h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
    For approximation to f² in logistic regression context:
    f² ≈ h² / (4 * pi²) * (some scaling factor depending on model complexity)
    However, for the purpose of this task, we will use the F-test approximation
    where effect size f = sqrt( (p1-p0)^2 / (1-p0) ) is often used, but here we
    strictly follow the task: Calculate detectable effect size using Cohen's f².
    
    We will use the standard Cohen's f² definition for regression:
    f² = R² / (1 - R²)
    But since we are doing power analysis *a priori* or *post-hoc* on sample size,
    we need the input effect size.
    
    The task asks to calculate the detectable effect size using Cohen's f² (target >= 0.15).
    We will use statsmodels to find the power for a given f², or the f² for a given power.
    
    Here we calculate the effect size from observed proportions if available,
    or use the target f² directly.
    """
    # If we have observed proportions, we can estimate the effect size.
    # But for the power report, we are checking if the current N is enough for f²=0.15.
    return 0.0  # Placeholder, actual logic in perform_power_analysis

def estimate_required_sample_size(
    effect_size: float,
    power: float,
    alpha: float = 0.05,
    k_predictors: int = 2  # Architecture + Constraint Count + Interaction
) -> int:
    """
    Estimate the required sample size to detect a given effect size with specified power.
    
    Uses FTestAnovaPower as an approximation for the fixed effects in GLMM.
    """
    power_analysis = FTestAnovaPower()
    # f = effect_size (Cohen's f)
    # Note: Cohen's f² = f^2. So if target f² is 0.15, f = sqrt(0.15)
    f = math.sqrt(effect_size)
    
    try:
        n = power_analysis.solve_power(
            effect_size=f,
            power=power,
            alpha=alpha,
            n_groups=k_predictors, # Approximation: number of groups or predictors
            ratio=1.0
        )
        return int(math.ceil(n))
    except Exception:
        # Fallback if solver fails
        return -1

def perform_power_analysis(
    n_obs: int,
    effect_size_f2: float,
    alpha: float = 0.05,
    k_predictors: int = 2
) -> Tuple[float, bool]:
    """
    Perform power analysis given sample size and effect size.
    
    Returns:
        Tuple of (calculated_power, pass_boolean)
    """
    power_analysis = FTestAnovaPower()
    f = math.sqrt(effect_size_f2)
    
    try:
        calculated_power = power_analysis.solve_power(
            effect_size=f,
            nobs=n_obs,
            alpha=alpha,
            n_groups=k_predictors,
            ratio=1.0
        )
        # Clamp to [0, 1]
        calculated_power = max(0.0, min(1.0, calculated_power))
        passed = calculated_power >= 0.80
        return calculated_power, passed
    except Exception as e:
        # If calculation fails, log error and return 0 power
        print(f"Warning: Power calculation failed: {e}")
        return 0.0, False

def run_power_analysis(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to run power analysis on the filtered dataset.
    
    1. Load the filtered dataset (data/processed/filtered_tasks.csv).
    2. Determine the sample size (N).
    3. Use the target effect size (Cohen's f² = 0.15) from config.
    4. Calculate the power to detect this effect with the given N.
    5. Generate the report.
    """
    config = get_analysis_config()
    dataset_config = get_dataset_config()
    paths = get_paths()
    
    # Determine input path
    if input_path is None:
        input_path = paths.data_processed / "filtered_tasks.csv"
    
    # Determine output path
    if output_path is None:
        output_path = paths.data_processed / "power_report.json"
    
    # Load data to get sample size
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    n_obs = len(df)
    
    if n_obs == 0:
        raise ValueError("Input dataset is empty. Cannot perform power analysis.")
    
    # Target effect size (Cohen's f²)
    target_f2 = config.target_effect_size
    target_power = config.target_power
    alpha = config.significance_level
    
    # Number of predictors for the interaction term (Architecture, ConstraintCount, Interaction)
    # For F-test approximation, we consider the interaction as the effect of interest.
    # We assume a model with 2 main effects + 1 interaction = 3 parameters?
    # Or simply the number of groups if we treat it as ANOVA.
    # Let's use k=2 (Architecture, ConstraintCount) as the base, testing the interaction adds 1.
    # The F-test for the interaction term usually has degrees of freedom related to the interaction.
    # We'll approximate with k_groups = 2 (Monolithic vs Dual-Track) and test the difference in slopes.
    # A safe approximation for the interaction effect in a 2xK design is n_groups = 2.
    k_predictors = 2 
    
    # Perform analysis
    calculated_power, passed = perform_power_analysis(
        n_obs=n_obs,
        effect_size_f2=target_f2,
        alpha=alpha,
        k_predictors=k_predictors
    )
    
    # Prepare report
    report = {
        "calculated_power": round(calculated_power, 4),
        "effect_size": target_f2,
        "target_power": target_power,
        "pass": passed,
        "sample_size": n_obs,
        "significance_level": alpha,
        "method": "FTestAnovaPower approximation for GLMM interaction effect",
        "notes": f"Calculated power for detecting Cohen's f²={target_f2} with N={n_obs}."
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Power analysis complete. Report written to: {output_path}")
    print(f"Calculated Power: {calculated_power:.4f}")
    print(f"Target Power: {target_power}")
    print(f"Pass: {passed}")
    
    return report

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Perform power analysis on filtered dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input filtered_tasks.csv. Defaults to data/processed/filtered_tasks.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output power_report.json. Defaults to data/processed/power_report.json"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    try:
        run_power_analysis(input_path, output_path)
    except Exception as e:
        print(f"Error during power analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
