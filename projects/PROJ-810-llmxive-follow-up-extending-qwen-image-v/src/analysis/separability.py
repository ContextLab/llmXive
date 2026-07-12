"""
Separability Analysis Module.
Implements power analysis and other statistical checks for latent space disentanglement.
"""
import json
import math
from pathlib import Path

# Ensure output directory exists
OUTPUT_DIR = Path("data/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_sample_size_power(effect_size: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Calculates the minimum sample size (N) required per group for a two-sample t-test
    to achieve the specified power given an effect size (Cohen's d).

    Uses the approximation formula:
    N = 2 * ((Z_alpha + Z_beta) / d)^2

    Where:
    - Z_alpha is the critical value for the significance level (two-tailed)
    - Z_beta is the critical value for the desired power (1 - beta)
    - d is the effect size (Cohen's d)

    Args:
        effect_size (float): Cohen's d (e.g., 0.8 for large effect)
        alpha (float): Significance level (default 0.05)
        power (float): Desired statistical power (default 0.80)

    Returns:
        int: Minimum sample size required per group.
    """
    from scipy.stats import norm

    # Z-scores
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    # Formula for two-sample t-test (equal variance, equal n)
    # N per group
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2

    return int(math.ceil(n_per_group))


def run_power_analysis(
    effect_size: float = 0.8,
    alpha: float = 0.05,
    power: float = 0.80,
    audit_ratio: float = 0.05,
    min_audit: int = 30
) -> dict:
    """
    Runs the power analysis to determine required sample size (N_required)
    and the sample size for manual audit (N_audit).

    Args:
        effect_size (float): Expected effect size (Cohen's d).
        alpha (float): Significance level.
        power (float): Target power.
        audit_ratio (float): Ratio of N to sample for manual audit.
        min_audit (int): Minimum number of samples for audit.

    Returns:
        dict: Results dictionary containing N_required, effect_size, power, N_audit.
    """
    n_required = calculate_sample_size_power(effect_size, alpha, power)

    # Calculate N_audit
    # Ensure N_audit is at least min_audit, but not larger than N_required
    n_audit = max(min_audit, int(n_required * audit_ratio))
    if n_audit > n_required:
        n_audit = n_required

    result = {
        "N_required": n_required,
        "effect_size": effect_size,
        "power": power,
        "alpha": alpha,
        "N_audit": n_audit,
        "audit_ratio_applied": audit_ratio,
        "description": "Power analysis for two-sample t-test on latent space separability"
    }

    # Save to file
    output_path = OUTPUT_DIR / "power_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Power analysis complete. Results saved to {output_path}")
    print(f"  N_required: {n_required}")
    print(f"  N_audit: {n_audit}")

    return result


if __name__ == "__main__":
    # Execute the power analysis with default parameters from the task spec
    # Effect size d > 0.8 as defined in Assumptions
    run_power_analysis(effect_size=0.8)
