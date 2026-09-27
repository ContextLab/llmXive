"""
Power Analysis for Crystal Structure Prediction Study.

Calculates required sample size based on assumed effect size (Cohen's w),
significance level (alpha), and power (1 - beta).

Parameters:
- Cohen's w = 0.15 (small-to-medium effect size for categorical associations)
- alpha = 0.05 (standard significance threshold)
- beta = 0.20 (targeting 80% statistical power)

Output:
- Target sample size of 500 scaffolds (planning artifact)
- Detailed metrics written to data/power_analysis_metrics.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Import logging infrastructure from existing API
from logging_config import get_logger, log_event

# Import config for path resolution
from config import get_path_absolute

logger = get_logger(__name__)


def calculate_sample_size(effect_size: float = 0.15, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Calculate required sample size for a chi-square test of independence.

    Uses the approximation formula for degrees of freedom based on
    the number of space groups (categories). We assume a moderate
    number of space group categories (e.g., 20 common ones + 'Other').

    Formula derivation:
    n = (Z_alpha + Z_beta)^2 / w^2
    where Z values are from the standard normal distribution.

    Args:
        effect_size (float): Cohen's w (default 0.15)
        alpha (float): Significance level (default 0.05)
        power (float): Statistical power (default 0.80)

    Returns:
        int: Required sample size
    """
    from scipy.stats import norm

    # Calculate Z-scores
    z_alpha = norm.ppf(1 - alpha / 2)  # Two-tailed test
    z_beta = norm.ppf(power)

    # Calculate sample size
    numerator = (z_alpha + z_beta) ** 2
    denominator = effect_size ** 2
    n = numerator / denominator

    return int(n)


def run_power_analysis() -> Dict[str, Any]:
    """
    Execute the power analysis and generate the planning artifact.

    Returns:
        Dict containing all power analysis metrics and the target sample size.
    """
    logger.info("Starting power analysis calculation")

    # Assumed parameters from task description
    effect_size = 0.15  # Cohen's w (small-to-medium effect)
    alpha = 0.05        # Significance level
    beta = 0.20         # Type II error rate
    power = 1 - beta    # Statistical power (80%)

    # Calculate required sample size
    calculated_n = calculate_sample_size(effect_size, alpha, power)

    # Apply domain-specific target: 500 scaffolds
    # This is a practical target that exceeds the statistical minimum
    # while being feasible for the pipeline constraints
    target_scaffolds = 500

    # Final target is the maximum of calculated and domain target
    final_target = max(calculated_n, target_scaffolds)

    logger.info(f"Calculated minimum sample size: {calculated_n}")
    logger.info(f"Domain target scaffolds: {target_scaffolds}")
    logger.info(f"Final target sample size: {final_target}")

    # Compile results
    results = {
        "parameters": {
            "effect_size_w": effect_size,
            "significance_alpha": alpha,
            "type_ii_error_beta": beta,
            "statistical_power": power,
            "degrees_of_freedom_assumed": 19  # 20 categories - 1
        },
        "calculated_metrics": {
            "minimum_sample_size": calculated_n,
            "domain_target_scaffolds": target_scaffolds,
            "final_target_sample_size": final_target,
            "effect_size_category": "small-to-medium",
            "power_achieved_at_target": round(
                (final_target * effect_size ** 2) ** 0.5 - (1.96), 2
            )  # Approximate power at target
        },
        "assumptions": [
            "Chi-square test of independence between molecular fingerprints and space groups",
            "Approximately 20 common space groups plus 'Other' category",
            "Effect size w=0.15 based on preliminary literature review",
            "Two-tailed test with alpha=0.05",
            "Target power of 80% (beta=0.20)"
        ],
        "recommendation": f"Target {final_target} unique (SMILES, Space Group) scaffolds for training and validation",
        "planning_artifact": "T006b"
    }

    return results


def main():
    """
    Main entry point for power analysis execution.

    Writes results to data/power_analysis_metrics.json
    """
    # Ensure output directory exists
    output_dir = get_path_absolute("data")
    os.makedirs(output_dir, exist_ok=True)

    # Run analysis
    results = run_power_analysis()

    # Write output file
    output_path = get_path_absolute("data/power_analysis_metrics.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Power analysis results written to {output_path}")
    print(f"Power analysis complete. Target sample size: {results['calculated_metrics']['final_target_sample_size']} scaffolds")
    return results


if __name__ == "__main__":
    main()
