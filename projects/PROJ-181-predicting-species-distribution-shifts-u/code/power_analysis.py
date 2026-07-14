"""
Power Analysis Module for Species Distribution Modeling.

Calculates the minimum sample size required to achieve a desired statistical power
for detecting an effect in species distribution models, post-spatial thinning.

Outputs:
    metrics/power_analysis_report.json: A JSON file containing the analysis results,
    including calculated sample sizes, power parameters, and recommendations.
"""
import json
import math
import logging
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import METRICS_DIR, RND_SEED
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Default parameters as per task specification
DEFAULT_POWER = 0.8
DEFAULT_ALPHA = 0.05  # P-value threshold (two-tailed)
DEFAULT_EFFECT_SIZE = 0.5  # Cohen's d equivalent for proportion difference

def calculate_minimum_sample_size(power=DEFAULT_POWER, alpha=DEFAULT_ALPHA, effect_size=DEFAULT_EFFECT_SIZE):
    """
    Calculate the minimum sample size (n per group) required to achieve the specified
    statistical power for detecting an effect of a given size at the specified alpha level.

    This uses the standard formula for comparing two proportions (or means with known variance)
    often used in A/B testing or model comparison scenarios.

    Formula approximation for two-sample proportion test (normal approximation):
    n = 2 * ( (Z_alpha/2 + Z_beta) / effect_size )^2

    Where:
        Z_alpha/2: Critical value for the desired significance level (two-tailed)
        Z_beta: Critical value for the desired power (1 - beta)
        effect_size: Cohen's h (difference in proportions) or standardized mean difference

    Args:
        power (float): Desired statistical power (1 - beta), typically 0.8 or 0.9.
        alpha (float): Significance level (probability of Type I error), typically 0.05.
        effect_size (float): Expected effect size (Cohen's h or d).

    Returns:
        int: The minimum sample size required per group.
    """
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1.")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1.")
    if effect_size <= 0:
        raise ValueError("Effect size must be positive.")

    # Calculate Z-scores using the inverse of the standard normal CDF (approximation)
    # Using a standard approximation for the inverse error function or pre-calculated values
    # Z for alpha=0.05 (two-tailed) is approx 1.96
    # Z for power=0.80 (beta=0.20) is approx 0.84

    # Approximation for Z_alpha/2
    z_alpha = 1.96 if alpha == 0.05 else _inverse_normal_cdf(1 - alpha / 2)
    # Approximation for Z_beta (where beta = 1 - power)
    z_beta = _inverse_normal_cdf(power)

    # Calculate sample size per group
    # n = 2 * ((Z_alpha + Z_beta) / effect_size)^2
    numerator = z_alpha + z_beta
    n_per_group = 2 * (numerator / effect_size) ** 2

    return math.ceil(n_per_group)

def _inverse_normal_cdf(p):
    """
    Approximation of the inverse of the standard normal cumulative distribution function.
    Uses the Abramowitz and Stegun approximation (Formula 26.2.23).
    """
    if p <= 0 or p >= 1:
        raise ValueError("Probability must be between 0 and 1 (exclusive).")

    if p == 0.5:
        return 0.0

    # Coefficients for the approximation
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    if p > 0.5:
        t = math.sqrt(-2 * math.log(1 - p))
    else:
        t = math.sqrt(-2 * math.log(p))

    # Rational approximation
    z = t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)

    if p < 0.5:
        return -z
    else:
        return z

def main():
    """
    Main execution function for the power analysis.

    Calculates the minimum sample size using default parameters and saves the report
    to metrics/power_analysis_report.json.
    """
    logger.info("Starting power analysis calculation.")
    logger.info(f"Parameters: power={DEFAULT_POWER}, alpha={DEFAULT_ALPHA}, effect_size={DEFAULT_EFFECT_SIZE}")

    try:
        min_sample_size = calculate_minimum_sample_size(
            power=DEFAULT_POWER,
            alpha=DEFAULT_ALPHA,
            effect_size=DEFAULT_EFFECT_SIZE
        )

        report = {
            "analysis_type": "Minimum Sample Size for Statistical Power",
            "parameters": {
                "target_power": DEFAULT_POWER,
                "significance_level_alpha": DEFAULT_ALPHA,
                "effect_size": DEFAULT_EFFECT_SIZE,
                "random_seed": RND_SEED
            },
            "results": {
                "minimum_sample_size_per_group": min_sample_size,
                "total_minimum_sample_size": min_sample_size * 2,
                "interpretation": f"To detect an effect size of {DEFAULT_EFFECT_SIZE} with {DEFAULT_POWER*100}% power at a {DEFAULT_ALPHA*100}% significance level, a minimum of {min_sample_size} samples per group (presence/background or historical/recent) is required."
            },
            "recommendations": [
                "Ensure post-thinning occurrence records exceed this threshold for reliable model training.",
                "If sample sizes are below this threshold, consider aggregating species or relaxing effect size assumptions.",
                "Use spatial block cross-validation to ensure independence of samples."
            ]
        }

        # Ensure output directory exists
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = METRICS_DIR / "power_analysis_report.json"

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Power analysis report successfully written to {output_path}")
        logger.info(f"Calculated minimum sample size per group: {min_sample_size}")

    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
