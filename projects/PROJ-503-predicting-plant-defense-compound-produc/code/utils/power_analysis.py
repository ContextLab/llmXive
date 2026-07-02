"""
Power analysis utility for determining sample size requirements.

Calculates the minimum sample size (n) required to detect a target correlation
coefficient (r) with a specified power and significance level (alpha).
Also allows calculating power given a sample size and target correlation.
"""
import argparse
import json
import logging
import math
import sys
from pathlib import Path
from typing import Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_z_score(p_value: float) -> float:
    """
    Approximate the z-score from a p-value (two-tailed).
    Uses the inverse of the standard normal cumulative distribution.
    """
    if p_value <= 0 or p_value >= 1:
        raise ValueError("P-value must be strictly between 0 and 1.")
    # Approximation of the inverse normal CDF (probit function)
    # Using the Beasley-Springer-Moro algorithm approximation for simplicity
    # or a standard library approach if available. Here we use a robust approximation.
    from math import sqrt, log, exp

    # Constants for approximation
    a0 = 2.515517
    a1 = 0.802853
    a2 = 0.010328
    b1 = 1.432788
    b2 = 0.189269
    b3 = 0.001308

    p = p_value / 2.0
    if p > 0.5:
        p = 1.0 - p
    t = sqrt(-2.0 * log(p))
    z = t - (a0 + a1*t + a2*t*t) / (1.0 + b1*t + b2*t*t + b3*t*t*t)
    return -z if p_value > 0.5 else z


def calculate_sample_size_for_correlation(
    power: float = 0.8,
    alpha: float = 0.05,
    target_r: float = 0.5
) -> int:
    """
    Calculate the minimum sample size (n) required to detect a target correlation.

    Args:
        power: Desired statistical power (1 - beta). Default 0.8.
        alpha: Significance level (Type I error rate). Default 0.05.
        target_r: Target Pearson correlation coefficient to detect. Default 0.5.

    Returns:
        Minimum sample size (n) as an integer.
    """
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1.")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")
    if not -1 < target_r < 1:
        raise ValueError("Target r must be between -1 and 1.")
    if target_r == 0:
        raise ValueError("Cannot calculate sample size for target_r = 0.")

    # Fisher's z-transformation
    z_r = 0.5 * math.log((1 + target_r) / (1 - target_r))

    # Z-scores for power and alpha
    # We need z_beta (for power) and z_alpha/2 (for two-tailed test)
    z_beta = calculate_z_score(1 - power)
    z_alpha = calculate_z_score(alpha / 2.0)

    # Formula: n = ((z_alpha + z_beta) / z_r)^2 + 3
    # Note: z_beta is negative for power > 0.5, so we use abs or adjust signs
    # Standard formula: n = ( (z_{1-alpha/2} + z_{1-beta}) / z_r )^2 + 3
    # Since our calculate_z_score returns negative for p > 0.5 (which 1-power usually is),
    # we take the absolute value of the sum of magnitudes or handle signs carefully.
    # Let's use magnitudes:
    z_power = abs(calculate_z_score(1 - power)) # z_{1-beta}
    z_alpha_val = abs(calculate_z_score(alpha / 2.0)) # z_{1-alpha/2}

    numerator = z_alpha_val + z_power
    n = (numerator / z_r) ** 2 + 3

    return math.ceil(n)


def calculate_power_for_correlation(
    n: int,
    alpha: float = 0.05,
    target_r: float = 0.5
) -> float:
    """
    Calculate the statistical power given sample size, alpha, and target correlation.

    Args:
        n: Sample size.
        alpha: Significance level.
        target_r: Target Pearson correlation coefficient.

    Returns:
        Statistical power (0 to 1).
    """
    if n <= 3:
        return 0.0
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")
    if not -1 < target_r < 1:
        raise ValueError("Target r must be between -1 and 1.")

    z_r = 0.5 * math.log((1 + target_r) / (1 - target_r))
    z_alpha_val = abs(calculate_z_score(alpha / 2.0))

    # Standard error of z_r
    se = 1.0 / math.sqrt(n - 3)

    # Calculate z_beta
    z_beta = (z_r / se) - z_alpha_val

    # Power is the probability that Z < z_beta (one-tailed in the direction of effect)
    # We need to convert z_beta back to a probability.
    # Since we don't have a perfect CDF in standard lib without scipy,
    # we approximate the CDF using the error function or a rational approximation.
    # Using a standard approximation for Normal CDF:
    def normal_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    power = normal_cdf(z_beta)
    return max(0.0, min(1.0, power))


def run_analysis(
    power: float = 0.8,
    alpha: float = 0.05,
    target_r: float = 0.5,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Run the power analysis and optionally save results to a file.

    Args:
        power: Desired power.
        alpha: Significance level.
        target_r: Target correlation.
        output_path: Optional path to write JSON results.

    Returns:
        Dictionary containing analysis results.
    """
    n_required = calculate_sample_size_for_correlation(power, alpha, target_r)
    actual_power = calculate_power_for_correlation(n_required, alpha, target_r)

    result = {
        "parameters": {
            "target_power": power,
            "alpha": alpha,
            "target_r": target_r
        },
        "results": {
            "minimum_sample_size": n_required,
            "actual_power_at_n": actual_power
        },
        "status": "success"
    }

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results written to {output_path}")

    return result


def main():
    """CLI entry point for power analysis."""
    parser = argparse.ArgumentParser(
        description="Calculate sample size or power for correlation analysis."
    )
    parser.add_argument(
        "--power", type=float, default=0.8,
        help="Desired statistical power (default: 0.8)"
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Significance level (default: 0.05)"
    )
    parser.add_argument(
        "--target-r", type=float, default=0.5,
        help="Target Pearson correlation coefficient (default: 0.5)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Path to output JSON file (optional)"
    )

    args = parser.parse_args()

    try:
        result = run_analysis(
            power=args.power,
            alpha=args.alpha,
            target_r=args.target_r,
            output_path=args.output
        )
        print(json.dumps(result, indent=2))
    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
