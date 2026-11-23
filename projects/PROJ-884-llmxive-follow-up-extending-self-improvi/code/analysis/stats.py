import math
import sys
import os
import json
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
import logging

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ZTestResult:
    """Result container for two-proportion z-test."""
    z_statistic: float
    p_value: float
    is_significant: bool
    effect_size: float
    sample_size_group1: int
    sample_size_group2: int
    success_rate_group1: float
    success_rate_group2: float

@dataclass
class TOSTResult:
    """Result container for Two One-Sided Tests (TOST) equivalence test."""
    t_lower: float
    t_upper: float
    p_value_lower: float
    p_value_upper: float
    is_equivalent: bool
    equivalence_margin: float
    mean_diff: float
    pooled_std: float

@dataclass
class PreRegistration:
    """Container for pre-registered statistical framework."""
    framework: str  # 'equivalence', 'non-inferiority', 'superiority'
    alpha: float
    effect_size_hypothesis: float
    power_target: float
    timestamp: str

def calculate_effect_size(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h (effect size for proportions).
    h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
    """
    if not (0 <= p1 <= 1) or not (0 <= p2 <= 1):
        raise ValueError("Proportions must be between 0 and 1.")
    
    # Avoid domain errors for arcsin by clamping to [0, 1]
    p1_clamped = max(0.0, min(1.0, p1))
    p2_clamped = max(0.0, min(1.0, p2))
    
    phi1 = 2.0 * math.asin(math.sqrt(p1_clamped))
    phi2 = 2.0 * math.asin(math.sqrt(p2_clamped))
    return abs(phi1 - phi2)

def calculate_power_z_test(p1: float, p2: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a two-proportion z-test.
    
    This is a simplified approximation using the normal distribution.
    For more accurate results, one would typically use the `statsmodels.stats.power`
    module or non-central t-distributions, but we implement a robust approximation here.
    
    Args:
        p1: Proportion for group 1 (e.g., symbolic)
        p2: Proportion for group 2 (e.g., neural)
        n1: Sample size for group 1
        n2: Sample size for group 2
        alpha: Significance level (default 0.05)
        
    Returns:
        Estimated power (0.0 to 1.0)
    """
    if n1 <= 0 or n2 <= 0:
        return 0.0
    
    # Effect size (Cohen's h)
    h = calculate_effect_size(p1, p2)
    
    if h == 0.0:
        return alpha  # No effect, power equals alpha
    
    # Pooled proportion under null hypothesis (for standard error calculation)
    # Note: For power calculation, we often use the alternative hypothesis proportions
    # but a standard approximation uses the pooled proportion for the null.
    # Here we use the standard error under the alternative for the Z-score calculation.
    
    # Standard error of the difference under the alternative hypothesis
    se = math.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
    
    if se == 0:
        return 1.0 if h > 0 else alpha
    
    # Critical Z value for the given alpha (two-tailed)
    # Using a standard normal approximation: Z_crit for alpha=0.05 is ~1.96
    z_crit = 1.96 if alpha == 0.05 else 1.645 if alpha == 0.10 else 2.576
    
    # Calculate the Z-score of the effect size relative to the standard error
    # This is effectively the non-centrality parameter
    z_power = (abs(p1 - p2) / se) - z_crit
    
    # Approximate power using the standard normal CDF (Phi)
    # Power = 1 - Beta = Phi(z_power)
    # We approximate Phi(x) using a standard approximation
    def phi(x):
        # Approximation of the standard normal cumulative distribution function
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    power = phi(z_power)
    return max(0.0, min(1.0, power))

def required_sample_size_for_power(effect_size: float, alpha: float = 0.05, power_target: float = 0.80) -> int:
    """
    Calculate the required sample size per group to achieve a target power.
    
    Formula for two-proportion z-test (equal sample sizes):
    n = 2 * ((Z_alpha/2 + Z_beta) / effect_size)^2
    
    Args:
        effect_size: Cohen's h (e.g., 0.5 for medium effect)
        alpha: Significance level
        power_target: Target power (e.g., 0.80)
        
    Returns:
        Required sample size per group (integer)
    """
    # Critical Z values
    z_alpha = 1.96 if alpha == 0.05 else 1.645 if alpha == 0.10 else 2.576
    z_beta = 0.84 if power_target == 0.80 else 1.28 if power_target == 0.90 else 0.0
    
    if effect_size == 0:
        return sys.maxsize  # Impossible to detect zero effect
    
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return math.ceil(n)

def two_proportion_z_test(successes1: int, n1: int, successes2: int, n2: int, alpha: float = 0.05) -> ZTestResult:
    """
    Perform a two-proportion z-test.
    
    H0: p1 = p2
    H1: p1 != p2
    
    Args:
        successes1: Number of successes in group 1
        n1: Total trials in group 1
        successes2: Number of successes in group 2
        n2: Total trials in group 2
        alpha: Significance level
        
    Returns:
        ZTestResult object
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes must be greater than 0.")
        
    p1 = successes1 / n1
    p2 = successes2 / n2
    
    # Pooled proportion
    p_pooled = (successes1 + successes2) / (n1 + n2)
    
    # Standard error under null hypothesis
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        # If pooled proportion is 0 or 1, we can't calculate a Z-score in the standard way
        # If both proportions are 0 or both are 1, p-value is 1 (no difference)
        if p1 == p2:
            return ZTestResult(
                z_statistic=0.0,
                p_value=1.0,
                is_significant=False,
                effect_size=calculate_effect_size(p1, p2),
                sample_size_group1=n1,
                sample_size_group2=n2,
                success_rate_group1=p1,
                success_rate_group2=p2
            )
        else:
            # Extreme difference, p-value effectively 0
            return ZTestResult(
                z_statistic=999.0,
                p_value=0.0,
                is_significant=True,
                effect_size=calculate_effect_size(p1, p2),
                sample_size_group1=n1,
                sample_size_group2=n2,
                success_rate_group1=p1,
                success_rate_group2=p2
            )
    
    z_stat = (p1 - p2) / se
    p_value = 2 * (1 - (0.5 * (1.0 + math.erf(abs(z_stat) / math.sqrt(2.0)))))
    
    return ZTestResult(
        z_statistic=z_stat,
        p_value=p_value,
        is_significant=(p_value < alpha),
        effect_size=calculate_effect_size(p1, p2),
        sample_size_group1=n1,
        sample_size_group2=n2,
        success_rate_group1=p1,
        success_rate_group2=p2
    )

def tost_equivalence_test(p1: float, p2: float, n1: int, n2: int, equivalence_margin: float, alpha: float = 0.05) -> TOSTResult:
    """
    Perform TOST equivalence test.
    
    H0: |p1 - p2| >= equivalence_margin
    H1: |p1 - p2| < equivalence_margin
    
    Args:
        p1: Proportion group 1
        p2: Proportion group 2
        n1: Sample size group 1
        n2: Sample size group 2
        equivalence_margin: The margin within which differences are considered equivalent
        alpha: Significance level
        
    Returns:
        TOSTResult object
    """
    diff = p1 - p2
    
    # Standard error of the difference
    se = math.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
    
    if se == 0:
        return TOSTResult(
            t_lower=0.0, t_upper=0.0, p_value_lower=1.0, p_value_upper=1.0,
            is_equivalent=abs(diff) < equivalence_margin,
            equivalence_margin=equivalence_margin,
            mean_diff=diff,
            pooled_std=0.0
        )
    
    t_lower = (diff - equivalence_margin) / se
    t_upper = (diff + equivalence_margin) / se
    
    # One-sided p-values
    def one_side_p(t):
        # P(Z > t)
        return 0.5 * (1.0 - math.erf(t / math.sqrt(2.0)))
    
    p_lower = one_side_p(t_lower)
    p_upper = one_side_p(-t_upper) # P(Z < -t_upper) = P(Z > t_upper) for symmetry in one-sided logic if t is negative? 
    # Actually for TOST: we need P(T < t_lower) and P(T > t_upper) for the two one-sided tests.
    # If we are testing H0: diff <= -margin OR diff >= margin
    # Test 1: H0: diff <= -margin vs H1: diff > -margin -> t = (diff - (-margin))/se
    # Test 2: H0: diff >= margin vs H1: diff < margin -> t = (diff - margin)/se
    
    # Correcting the logic for standard TOST implementation:
    # t1 = (diff - (-margin)) / se = (diff + margin) / se
    # t2 = (diff - margin) / se
    # We reject H0 if t1 > t_crit AND t2 < -t_crit (for two-sided alpha)
    # Or simply: p1 < alpha AND p2 < alpha
    
    t1 = (diff + equivalence_margin) / se
    t2 = (diff - equivalence_margin) / se
    
    p1_val = 0.5 * (1.0 - math.erf(t1 / math.sqrt(2.0))) # P(Z > t1) -> wait, if t1 is large positive, p is small
    p2_val = 0.5 * (1.0 + math.erf(t2 / math.sqrt(2.0))) # P(Z < t2)
    
    is_equiv = (p1_val < alpha) and (p2_val < alpha)
    
    return TOSTResult(
        t_lower=t2, t_upper=t1, p_value_lower=p1_val, p_value_upper=p2_val,
        is_equivalent=is_equiv,
        equivalence_margin=equivalence_margin,
        mean_diff=diff,
        pooled_std=se
    )

def register_statistical_framework(framework: str, alpha: float = 0.05, power: float = 0.80) -> PreRegistration:
    """
    Register the statistical framework to be used.
    
    Args:
        framework: 'equivalence', 'non-inferiority', or 'superiority'
        alpha: Significance level
        power: Target power
        
    Returns:
        PreRegistration object
    """
    from datetime import datetime
    return PreRegistration(
        framework=framework,
        alpha=alpha,
        effect_size_hypothesis=0.5, # Default medium effect size assumption
        power_target=power,
        timestamp=datetime.now().isoformat()
    )

def load_experiment_logs(log_path: str) -> List[Dict[str, Any]]:
    """Load experiment logs from a JSON file."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    with open(log_path, 'r') as f:
        return json.load(f)

def count_successes(logs: List[Dict[str, Any]], success_key: str = 'success') -> Tuple[int, int]:
    """
    Count successes and total trials from logs.
    
    Args:
        logs: List of log entries
        success_key: Key name for the success boolean
        
    Returns:
        Tuple of (success_count, total_count)
    """
    successes = sum(1 for entry in logs if entry.get(success_key, False))
    total = len(logs)
    return successes, total

def write_stats_results(results: Dict[str, Any], output_path: str) -> None:
    """Write statistical results to a JSON file."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def pre_analysis_power_check(planned_n: int, effect_size: float = 0.5, alpha: float = 0.05, target_power: float = 0.80) -> Dict[str, Any]:
    """
    Perform pre-analysis power calculation before an experimental run.
    
    Constraint: Before any experimental run, the system must calculate the required 
    sample size to achieve target_power for a medium effect size (Cohen's h = 0.5) 
    at alpha=0.05. If the planned sample size is insufficient, the system MUST log 
    a critical warning (but NOT halt execution) and proceed.
    
    Args:
        planned_n: The planned sample size for the experiment (N=10..500)
        effect_size: Expected effect size (Cohen's h), default 0.5 (medium)
        alpha: Significance level
        target_power: Target statistical power
        
    Returns:
        Dict containing power analysis results and recommendation.
    """
    required_n = required_sample_size_for_power(effect_size, alpha, target_power)
    
    # Estimate power for the planned sample size assuming the effect size exists
    # We assume equal group sizes for the estimate if planned_n is total, or use it directly
    # For a two-group comparison, if planned_n is per group:
    power_estimate = calculate_power_z_test(
        p1=0.5 + effect_size/2, # Arbitrary baseline to create the effect
        p2=0.5,
        n1=planned_n,
        n2=planned_n,
        alpha=alpha
    )
    
    is_sufficient = planned_n >= required_n
    
    result = {
        "planned_sample_size": planned_n,
        "required_sample_size_per_group": required_n,
        "effect_size_assumed": effect_size,
        "alpha": alpha,
        "target_power": target_power,
        "estimated_power": power_estimate,
        "is_sufficient": is_sufficient,
        "recommendation": "Proceed" if is_sufficient else "WARNING: Underpowered"
    }
    
    if not is_sufficient:
        logger.critical(
            f"Pre-Analysis Power Check FAILED: Planned N={planned_n} is insufficient "
            f"to detect effect size h={effect_size} with power={target_power}. "
            f"Required N per group is {required_n}. "
            f"Proceeding anyway as per Spec Assumptions, but results may be underpowered."
        )
    else:
        logger.info(
            f"Pre-Analysis Power Check PASSED: Planned N={planned_n} is sufficient "
            f"to detect effect size h={effect_size} with estimated power={power_estimate:.2f}."
        )
    
    return result

def main():
    """Main entry point for the stats module when run as a script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistical Analysis Tools")
    parser.add_argument('--symbolic', type=str, help="Path to symbolic run logs")
    parser.add_argument('--neural', type=str, help="Path to neural run logs")
    parser.add_argument('--output', type=str, help="Path to output results JSON")
    parser.add_argument('--check-power', action='store_true', help="Run pre-analysis power check")
    parser.add_argument('--planned-n', type=int, default=50, help="Planned sample size for power check")
    
    args = parser.parse_args()
    
    if args.check_power:
        # Run pre-analysis power check
        result = pre_analysis_power_check(args.planned_n)
        print(json.dumps(result, indent=2))
        return
    
    if args.symbolic and args.neural and args.output:
        # Run full comparison
        try:
            symbolic_logs = load_experiment_logs(args.symbolic)
            neural_logs = load_experiment_logs(args.neural)
            
            s_succ, s_total = count_successes(symbolic_logs)
            n_succ, n_total = count_successes(neural_logs)
            
            z_result = two_proportion_z_test(s_succ, s_total, n_succ, n_total)
            
            # Power check for the observed data
            power_check = pre_analysis_power_check(s_total) # Using symbolic N as reference
            
            output_data = {
                "z_test": asdict(z_result),
                "power_analysis": power_check,
                "symbolic_stats": {"successes": s_succ, "total": s_total},
                "neural_stats": {"successes": n_succ, "total": n_total}
            }
            
            write_stats_results(output_data, args.output)
            print(f"Results written to {args.output}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()