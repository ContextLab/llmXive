"""Power analysis utility for A/B test sample size calculation (FR-025).

Computes minimum N given baseline, detectable effect, α and power.
Writes result to output/power_analysis.json and asserts audited corpus
meets N ≥ 300 OR N ≥ calculated_minimum.
"""

import json
import math
import os
from typing import Dict, Any, Optional

from scipy.stats import norm

# Default parameters for power analysis
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_MIN_CORPUS_SIZE = 300

def calculate_minimum_sample_size(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    ratio: float = 1.0
) -> int:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        baseline_rate: Expected baseline conversion rate (0-1)
        detectable_effect: Minimum detectable effect size (absolute difference)
        alpha: Significance level (default 0.05)
        power: Statistical power (1 - beta, default 0.80)
        ratio: Ratio of sample sizes between groups (n2/n1, default 1.0)
    
    Returns:
        Minimum sample size per group
    
    Raises:
        ValueError: If rates are not in valid range or effect is invalid
    """
    # Validate inputs
    if not (0 < baseline_rate < 1):
        raise ValueError(f"Baseline rate must be between 0 and 1, got {baseline_rate}")
    
    p2 = baseline_rate + detectable_effect
    if not (0 < p2 < 1):
        raise ValueError(f"Treatment rate must be between 0 and 1, got {p2}")
    
    if detectable_effect <= 0:
        raise ValueError(f"Detectable effect must be positive, got {detectable_effect}")
    
    # Z-scores for alpha (two-tailed) and power
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    
    # Pooled proportion under null
    p_pooled = (baseline_rate + p2) / 2
    
    # Standard formula for two-proportion z-test sample size
    # n = [(z_alpha * sqrt(2*p_pooled*(1-p_pooled)) + z_beta * sqrt(p1*(1-p1) + p2*(1-p2)))^2] / effect^2
    numerator = (
        z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled) * (1 + ratio)) +
        z_beta * math.sqrt(baseline_rate * (1 - baseline_rate) + p2 * (1 - p2) * ratio)
    ) ** 2
    
    denominator = detectable_effect ** 2
    
    n_per_group = numerator / denominator
    
    return math.ceil(n_per_group)

def calculate_power(
    sample_size_per_group: int,
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = DEFAULT_ALPHA
) -> float:
    """
    Calculate statistical power given sample size and effect parameters.
    
    Args:
        sample_size_per_group: Number of samples per group
        baseline_rate: Expected baseline conversion rate (0-1)
        detectable_effect: Minimum detectable effect size (absolute difference)
        alpha: Significance level (default 0.05)
    
    Returns:
        Statistical power (1 - beta)
    """
    z_alpha = norm.ppf(1 - alpha / 2)
    
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    # Standard error under null hypothesis (assuming equal rates)
    se_null = math.sqrt(2 * p1 * (1 - p1) / sample_size_per_group)
    
    # Standard error under alternative hypothesis
    se_alt = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / sample_size_per_group)
    
    # Calculate power using non-centrality parameter
    delta = abs(detectable_effect)
    z_power = (delta - z_alpha * se_null) / se_alt
    power = norm.cdf(z_power)
    
    return max(0.0, min(1.0, power))

def run_power_analysis(
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.02,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    corpus_size: Optional[int] = None,
    min_corpus_size: int = DEFAULT_MIN_CORPUS_SIZE
) -> Dict[str, Any]:
    """
    Run power analysis and generate report.
    
    Args:
        baseline_rate: Expected baseline conversion rate
        detectable_effect: Minimum detectable effect size
        alpha: Significance level
        power: Target statistical power
        corpus_size: Actual corpus size (optional)
        min_corpus_size: Minimum required corpus size (default 300)
    
    Returns:
        Dictionary with power analysis results
    """
    # Calculate minimum sample size per group
    minimum_n = calculate_minimum_sample_size(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )
    
    # Calculate total minimum (both groups)
    total_minimum = minimum_n * 2
    
    # Check if corpus meets requirements (N ≥ 300 OR N ≥ calculated_minimum)
    meets_requirement = False
    if corpus_size is not None:
        meets_requirement = corpus_size >= max(min_corpus_size, total_minimum)
    
    # Calculate actual power if corpus size provided
    actual_power = None
    if corpus_size is not None and corpus_size >= 2:
        actual_power = calculate_power(
            sample_size_per_group=corpus_size // 2,
            baseline_rate=baseline_rate,
            detectable_effect=detectable_effect,
            alpha=alpha
        )
    
    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "minimum_sample_size_per_group": minimum_n,
        "total_minimum_sample_size": total_minimum,
        "corpus_size": corpus_size,
        "minimum_corpus_size_requirement": min_corpus_size,
        "meets_requirement": meets_requirement,
        "actual_power_if_corpus_provided": actual_power,
        "notes": (
            f"Corpus meets requirement (N ≥ {min_corpus_size} OR N ≥ {total_minimum})"
            if meets_requirement else
            f"Corpus does NOT meet requirement (N={corpus_size} < {max(min_corpus_size, total_minimum)})"
        )
    }
    
    return result

def write_output(result: Dict[str, Any], output_path: str = "output/power_analysis.json") -> None:
    """Write power analysis results to JSON file."""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

def main():
    """Main entry point for power analysis utility."""
    # Default parameters
    baseline_rate = 0.10  # 10% baseline conversion
    detectable_effect = 0.02  # 2 percentage point difference
    alpha = DEFAULT_ALPHA
    power = DEFAULT_POWER
    min_corpus_size = DEFAULT_MIN_CORPUS_SIZE
    
    # Try to read corpus size from environment or use None
    corpus_size = None
    
    # Run analysis
    result = run_power_analysis(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power,
        corpus_size=corpus_size,
        min_corpus_size=min_corpus_size
    )
    
    # Write output
    output_path = "output/power_analysis.json"
    write_output(result, output_path)
    
    # Print summary
    print(f"Power analysis results written to {output_path}")
    print(f"  Baseline rate: {baseline_rate:.2%}")
    print(f"  Detectable effect: {detectable_effect:.2%}")
    print(f"  Alpha: {alpha}")
    print(f"  Target power: {power}")
    print(f"  Minimum sample size per group: {result['minimum_sample_size_per_group']}")
    print(f"  Total minimum sample size: {result['total_minimum_sample_size']}")
    print(f"  Meets requirement: {result['meets_requirement']}")

if __name__ == "__main__":
    main()
