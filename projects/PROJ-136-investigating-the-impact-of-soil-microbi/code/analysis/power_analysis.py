"""
Power Analysis Utility for Soil Microbiome Study.

Implements a priori power analysis to determine minimum sample size requirements
and verify that the study design meets statistical power requirements per FR-015.

Requirements:
- Target power >= 0.8
- Target effect size >= 0.1
- Default alpha level = 0.05
- Default variance estimate = 0.15
"""

import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Tuple

# Import logging from the existing project infrastructure
from .logging_config import get_logger

# Constants for default parameters
DEFAULT_ALPHA = 0.05
DEFAULT_VARIANCE = 0.15
DEFAULT_EFFECT_SIZE = 0.1
TARGET_POWER = 0.8

# Output paths
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "power_analysis_report.json"

def calculate_sample_size_for_power(
    alpha: float = DEFAULT_ALPHA,
    power: float = TARGET_POWER,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    variance: float = DEFAULT_VARIANCE
) -> int:
    """
    Calculate the minimum sample size required to achieve the target power.

    Uses the standard formula for two-sample t-test power analysis:
    n = 2 * (Z_alpha + Z_beta)^2 * sigma^2 / delta^2

    Where:
    - Z_alpha is the critical value for the significance level (two-tailed)
    - Z_beta is the critical value for the desired power (1 - beta)
    - sigma^2 is the variance estimate
    - delta is the effect size (minimum detectable difference)

    Args:
        alpha: Significance level (default: 0.05)
        power: Target statistical power (default: 0.8)
        effect_size: Minimum detectable effect size (default: 0.1)
        variance: Estimated variance of the outcome (default: 0.15)

    Returns:
        Minimum sample size per group (rounded up)
    """
    if effect_size <= 0:
        raise ValueError("Effect size must be positive")
    if variance <= 0:
        raise ValueError("Variance must be positive")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1")
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1")

    # Z-scores approximation
    # Z for alpha (two-tailed)
    z_alpha = abs(math.sqrt(2) * math.erfcinv(2 * alpha))
    # Z for power (beta = 1 - power)
    z_beta = abs(math.sqrt(2) * math.erfcinv(2 * (1 - power)))

    # Calculate sample size per group
    numerator = 2 * (z_alpha + z_beta) ** 2 * variance
    denominator = effect_size ** 2
    n_per_group = math.ceil(numerator / denominator)

    return n_per_group

def calculate_power(
    n_per_group: int,
    alpha: float = DEFAULT_ALPHA,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    variance: float = DEFAULT_VARIANCE
) -> float:
    """
    Calculate the statistical power for a given sample size.

    Args:
        n_per_group: Sample size per group
        alpha: Significance level
        effect_size: Effect size
        variance: Estimated variance

    Returns:
        Calculated statistical power (between 0 and 1)
    """
    if n_per_group <= 0:
        return 0.0

    # Standard error
    se = math.sqrt(2 * variance / n_per_group)

    # Non-centrality parameter
    ncp = effect_size / se

    # Approximate power using normal distribution
    # Power = P(Z > Z_alpha - ncp) + P(Z < -Z_alpha - ncp)
    # For two-tailed test, simplified approximation:
    z_alpha = abs(math.sqrt(2) * math.erfcinv(2 * alpha))

    # Power calculation
    power = 1 - 0.5 * (
        math.erfc((z_alpha - ncp) / math.sqrt(2)) +
        math.erfc((z_alpha + ncp) / math.sqrt(2))
    )

    return max(0.0, min(1.0, power))

def run_power_analysis(
    alpha: float = DEFAULT_ALPHA,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    variance: float = DEFAULT_VARIANCE,
    target_power: float = TARGET_POWER
) -> Dict[str, Any]:
    """
    Run a complete power analysis and return the results.

    This function calculates the minimum sample size required to achieve
    the target power given the specified effect size and variance.

    Args:
        alpha: Significance level (default: 0.05)
        effect_size: Effect size to detect (default: 0.1)
        variance: Estimated variance (default: 0.15)
        target_power: Target statistical power (default: 0.8)

    Returns:
        Dictionary containing power analysis results
    """
    logger = get_logger(__name__)
    logger.info(f"Starting power analysis with alpha={alpha}, effect_size={effect_size}, variance={variance}")

    # Calculate minimum sample size
    min_sample_size = calculate_sample_size_for_power(
        alpha=alpha,
        power=target_power,
        effect_size=effect_size,
        variance=variance
    )

    # Verify power at this sample size
    actual_power = calculate_power(
        n_per_group=min_sample_size,
        alpha=alpha,
        effect_size=effect_size,
        variance=variance
    )

    # Check requirements
    power_requirement_met = actual_power >= target_power
    effect_size_requirement_met = effect_size >= 0.1

    result = {
        "analysis_type": "a priori power analysis",
        "parameters": {
            "alpha_level": alpha,
            "effect_size": effect_size,
            "variance_estimate": variance,
            "target_power": target_power
        },
        "results": {
            "power": round(actual_power, 4),
            "effect_size": effect_size,
            "min_sample_size": min_sample_size,
            "total_sample_size": min_sample_size * 2  # Two groups
        },
        "requirements": {
            "power_requirement_met": power_requirement_met,
            "power_threshold": target_power,
            "effect_size_requirement_met": effect_size_requirement_met,
            "effect_size_threshold": 0.1,
            "fr_015_compliant": power_requirement_met and effect_size_requirement_met
        },
        "summary": {
            "status": "PASS" if power_requirement_met and effect_size_requirement_met else "FAIL",
            "message": (
                f"Power analysis complete. "
                f"Power: {actual_power:.4f} (target >= {target_power}), "
                f"Effect Size: {effect_size} (target >= 0.1), "
                f"Minimum Sample Size per Group: {min_sample_size}."
            )
        }
    }

    logger.info(f"Power analysis complete: {result['summary']['status']}")

    return result

def save_report(result: Dict[str, Any], output_path: Path = OUTPUT_FILE) -> None:
    """
    Save the power analysis report to a JSON file.

    Args:
        result: Power analysis result dictionary
        output_path: Path to save the report
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    # Log success
    logger = get_logger(__name__)
    logger.info(f"Power analysis report saved to {output_path}")

def main():
    """Main entry point for the power analysis script."""
    logger = get_logger(__name__)
    logger.info("Executing power analysis utility (T009)")

    try:
        # Run analysis with default parameters as specified in FR-015
        # alpha = 0.05, variance = 0.15, effect_size >= 0.1
        result = run_power_analysis(
            alpha=DEFAULT_ALPHA,
            effect_size=DEFAULT_EFFECT_SIZE,
            variance=DEFAULT_VARIANCE,
            target_power=TARGET_POWER
        )

        # Save the report
        save_report(result)

        # Print summary
        print(f"\n{result['summary']['message']}")
        print(f"FR-015 Compliance: {result['summary']['status']}")

        if not result["requirements"]["fr_015_compliant"]:
            logger.warning("Power analysis did not meet FR-015 requirements")
            return 1

        logger.info("Power analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    exit(main())
