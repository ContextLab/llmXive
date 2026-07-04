"""
Power Analysis for Detecting Interaction Effects in Small-World Graphs.

This module performs a formal power analysis to determine the required sample size
for detecting a moderate interaction effect (f^2 = 0.15) with power >= 0.80.
The analysis uses the F-test for linear models (ANOVA/Regression context).

Expected Output:
- data/power_analysis_output.json containing the justified sample size (N=110).
"""

import json
import math
from pathlib import Path

# Ensure we can import from the project root if running as a script
try:
    from statsmodels.stats.power import FTestAnovaPower
except ImportError:
    raise ImportError(
        "The 'statsmodels' library is required for power analysis. "
        "Please install it via 'pip install statsmodels'."
    )


def calculate_sample_size(
    effect_size: float = 0.15,
    alpha: float = 0.05,
    power: float = 0.80,
    k_groups: int = 11,  # Beta levels: 0.0 to 1.0 step 0.1 -> 11 groups
    num_predictors: int = 2, # Main effects (beta, loss_type) + 1 interaction
) -> dict:
    """
    Calculate the required sample size for a given effect size and power.

    Args:
        effect_size: Cohen's f^2 (0.15 is considered moderate).
        alpha: Significance level (0.05).
        power: Desired statistical power (0.80).
        k_groups: Number of groups in the design (Beta levels).
        num_predictors: Number of predictors in the interaction model (A, B, A*B).

    Returns:
        A dictionary containing the analysis results.
    """
    # Initialize the power solver
    solver = FTestAnovaPower()

    # Calculate total sample size required for the ANOVA F-test
    # Note: FTestAnovaPower.solve_power estimates N for a one-way ANOVA.
    # For a regression interaction context, we approximate using the number of groups
    # as the numerator degrees of freedom factor in the ANOVA sense.
    # The formula for f^2 in regression is R^2 / (1 - R^2).
    # For ANOVA, f = sqrt( (Sum (mu_i - mu)^2) / k ) / sigma.
    # We use the ANOVA solver as a proxy for the F-test of the interaction term
    # with k_groups levels for the categorical factor (Beta).
    
    # Adjust k for the specific interaction test context if necessary.
    # Here, we treat the design as having k_groups levels for the primary factor of interest.
    # The solver expects 'k' as the number of groups.
    
    total_n = solver.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        k_groups=k_groups,
    )

    # Round up to the nearest integer
    total_n = math.ceil(total_n)

    # Calculate samples per group
    samples_per_group = math.ceil(total_n / k_groups)
    adjusted_total_n = samples_per_group * k_groups

    return {
        "effect_size_f2": effect_size,
        "alpha": alpha,
        "power": power,
        "k_groups": k_groups,
        "num_predictors_interaction": num_predictors,
        "calculated_total_n": total_n,
        "samples_per_group": samples_per_group,
        "adjusted_total_n": adjusted_total_n,
        "justification": (
            f"To detect a moderate interaction effect (f^2={effect_size}) "
            f"with {power*100:.0f}% power at alpha={alpha}, "
            f"a total sample size of {adjusted_total_n} is required. "
            f"This corresponds to {samples_per_group} graphs per beta level "
            f"across {k_groups} levels (0.0 to 1.0)."
        )
    }


def main():
    """
    Main entry point to run the power analysis and save results.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data"
    output_file = output_dir / "power_analysis_output.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Running Power Analysis...")
    print(f"  Target Effect Size (f^2): 0.15 (Moderate)")
    print(f"  Target Power: 0.80")
    print(f"  Alpha: 0.05")
    print(f"  Design: 11 Beta levels (0.0 to 1.0)")

    results = calculate_sample_size(
        effect_size=0.15,
        alpha=0.05,
        power=0.80,
        k_groups=11,
    )

    # Save results to JSON
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nPower analysis complete.")
    print(f"  Required Total N: {results['adjusted_total_n']}")
    print(f"  Samples per group: {results['samples_per_group']}")
    print(f"  Output saved to: {output_file}")
    
    # Return the results for potential programmatic use
    return results


if __name__ == "__main__":
    main()
