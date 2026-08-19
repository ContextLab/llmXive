import math
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
import sys
import os
import json

@dataclass
class ZTestResult:
    """Result of a two-proportion z-test."""
    p1: float
    p2: float
    n1: int
    n2: int
    z_score: float
    p_value: float
    diff_proportion: float
    ci_lower: float
    ci_upper: float
    is_significant: bool
    alpha: float = 0.05

@dataclass
class TOSTResult:
    """Result of a Two One-Sided Test (TOST) for equivalence."""
    p1: float
    p2: float
    n1: int
    n2: int
    diff: float
    lower_bound: float
    upper_bound: float
    p_value_lower: float
    p_value_upper: float
    is_equivalent: bool
    equivalence_margin: float

@dataclass
class PreRegistration:
    """Statistical framework pre-registration record."""
    framework_type: str  # 'equivalence' or 'non-inferiority'
    alpha: float
    power_target: float
    effect_size_hypothesis: float
    timestamp: str = field(default_factory=lambda: str(os.times().elapsed))

def calculate_effect_size(p1: float, p2: float, n1: int, n2: int) -> float:
    """
    Calculate Cohen's h effect size for two proportions.
    h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
    """
    # Avoid domain errors for p=0 or p=1
    p1 = max(0.0001, min(0.9999, p1))
    p2 = max(0.0001, min(0.9999, p2))
    
    phi1 = 2 * math.asin(math.sqrt(p1))
    phi2 = 2 * math.asin(math.sqrt(p2))
    return abs(phi1 - phi2)

def calculate_power_z_test(p1: float, p2: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """
    Estimate statistical power for a two-proportion z-test.
    Uses the normal approximation.
    """
    if n1 <= 0 or n2 <= 0:
        return 0.0
    
    # Pooled proportion under H0
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    q_pool = 1 - p_pool
    
    # Standard error under H0
    se_null = math.sqrt(p_pool * q_pool * (1/n1 + 1/n2))
    
    # Standard error under H1 (using individual proportions)
    se_alt = math.sqrt(p1 * (1-p1)/n1 + p2 * (1-p2)/n2)
    
    if se_null == 0 or se_alt == 0:
        return 0.0
    
    # Critical value for two-tailed test
    z_crit = math.sqrt(2) * math.erfinv(1 - alpha)
    if z_crit == 0:
        return 0.0
        
    # Non-centrality parameter
    diff = abs(p1 - p2)
    z_power = (diff / se_alt) - z_crit
    
    # Power is the probability that Z > z_crit under H1
    # Approximate using standard normal CDF
    power = 0.5 * (1 + math.erf(z_power / math.sqrt(2)))
    return max(0.0, min(1.0, power))

def two_proportion_z_test(x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05) -> ZTestResult:
    """
    Perform a two-proportion z-test.
    
    Args:
        x1: Number of successes in group 1
        n1: Total trials in group 1
        x2: Number of successes in group 2
        n2: Total trials in group 2
        alpha: Significance level (default 0.05)
    
    Returns:
        ZTestResult containing test statistics and 95% confidence interval
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive")
    if x1 < 0 or x1 > n1 or x2 < 0 or x2 > n2:
        raise ValueError("Success counts must be within [0, n]")
    
    p1 = x1 / n1
    p2 = x2 / n2
    diff = p1 - p2
    
    # Pooled proportion for standard error under H0
    p_pool = (x1 + x2) / (n1 + n2)
    q_pool = 1 - p_pool
    
    # Standard error
    se = math.sqrt(p_pool * q_pool * (1/n1 + 1/n2))
    
    if se == 0:
        # If pooled proportion is 0 or 1, z-score is undefined unless diff is also 0
        if diff == 0:
            z_score = 0.0
            p_value = 1.0
        else:
            z_score = float('inf') if diff > 0 else float('-inf')
            p_value = 0.0
    else:
        z_score = diff / se
        # Two-tailed p-value
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))
    
    # 95% Confidence Interval for the difference
    # Using unpooled standard error for CI
    se_diff = math.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
    
    # Critical z for 95% CI (alpha=0.05)
    z_crit = 1.96  # Approximate for 95%
    
    ci_lower = diff - z_crit * se_diff
    ci_upper = diff + z_crit * se_diff
    
    is_significant = p_value < alpha
    
    return ZTestResult(
        p1=p1,
        p2=p2,
        n1=n1,
        n2=n2,
        z_score=z_score,
        p_value=p_value,
        diff_proportion=diff,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        is_significant=is_significant,
        alpha=alpha
    )

def tost_equivalence_test(x1: int, n1: int, x2: int, n2: int, 
                          equivalence_margin: float, alpha: float = 0.05) -> TOSTResult:
    """
    Perform a Two One-Sided Test (TOST) for equivalence.
    
    Args:
        x1, n1: Successes and trials for group 1
        x2, n2: Successes and trials for group 2
        equivalence_margin: The maximum acceptable difference for equivalence
        alpha: Significance level
    
    Returns:
        TOSTResult
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive")
        
    p1 = x1 / n1
    p2 = x2 / n2
    diff = p1 - p2
    
    # Standard error for difference
    se_diff = math.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
    
    if se_diff == 0:
        # Edge case: no variance
        if abs(diff) < equivalence_margin:
            return TOSTResult(p1, p2, n1, n2, diff, -equivalence_margin, equivalence_margin, 0.0, 0.0, True, equivalence_margin)
        else:
            return TOSTResult(p1, p2, n1, n2, diff, -equivalence_margin, equivalence_margin, 1.0, 1.0, False, equivalence_margin)
    
    # Test 1: H0: diff <= -margin vs H1: diff > -margin
    z_lower = (diff - (-equivalence_margin)) / se_diff
    p_lower = 1 - 0.5 * (1 + math.erf(z_lower / math.sqrt(2)))
    
    # Test 2: H0: diff >= margin vs H1: diff < margin
    z_upper = (diff - equivalence_margin) / se_diff
    p_upper = 0.5 * (1 + math.erf(z_upper / math.sqrt(2)))
    
    # Equivalence is claimed if both p-values < alpha
    is_equivalent = (p_lower < alpha) and (p_upper < alpha)
    
    return TOSTResult(
        p1=p1,
        p2=p2,
        n1=n1,
        n2=n2,
        diff=diff,
        lower_bound=-equivalence_margin,
        upper_bound=equivalence_margin,
        p_value_lower=p_lower,
        p_value_upper=p_upper,
        is_equivalent=is_equivalent,
        equivalence_margin=equivalence_margin
    )

def register_statistical_framework(framework_type: str, alpha: float = 0.05, 
                                   power_target: float = 0.8, effect_size: float = 0.5) -> PreRegistration:
    """
    Register the statistical framework choice before running tests.
    
    Args:
        framework_type: 'equivalence' (TOST) or 'non-inferiority'
        alpha: Significance level
        power_target: Desired statistical power
        effect_size: Expected effect size for power calculation
    
    Returns:
        PreRegistration object
    """
    return PreRegistration(
        framework_type=framework_type,
        alpha=alpha,
        power_target=power_target,
        effect_size_hypothesis=effect_size,
        timestamp=str(os.times().elapsed)
    )

def main():
    """
    CLI entry point for statistical analysis.
    Reads experiment results and performs z-tests with confidence intervals.
    """
    if len(sys.argv) < 3:
        print("Usage: python stats.py <results_json> <output_json>")
        print("  results_json: Path to JSON file containing success counts for two groups")
        print("  output_json: Path to write ZTestResult")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Expecting structure: {"group1": {"successes": x1, "trials": n1}, "group2": {...}}
        if "group1" not in data or "group2" not in data:
            raise ValueError("Input JSON must contain 'group1' and 'group2' keys")
        
        g1 = data["group1"]
        g2 = data["group2"]
        
        x1 = g1.get("successes", 0)
        n1 = g1.get("trials", 1)
        x2 = g2.get("successes", 0)
        n2 = g2.get("trials", 1)
        
        result = two_proportion_z_test(x1, n1, x2, n2)
        
        output_data = {
            "p1": result.p1,
            "p2": result.p2,
            "n1": result.n1,
            "n2": result.n2,
            "z_score": result.z_score,
            "p_value": result.p_value,
            "diff_proportion": result.diff_proportion,
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "is_significant": result.is_significant,
            "alpha": result.alpha,
            "interpretation": f"95% CI for difference: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]"
        }
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Z-test completed. Results written to {output_path}")
        print(f"p-value: {result.p_value:.4f}, 95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
