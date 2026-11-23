import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np
from scipy import stats

# Import from project utils as per API surface
from utils.logger import log_script_start, log_script_end, log_analysis_step, info, warning, error
from utils.random_utils import set_global_seed, get_seed

# Constants for the study design
TARGET_POWER = 0.80
EFFECT_SIZE_D = 0.4
ALPHA = 0.05
RECRUITMENT_TARGET_N = 300
GROUPS = 2

def calculate_required_n(effect_size: float = EFFECT_SIZE_D, power: float = TARGET_POWER, alpha: float = ALPHA, groups: int = GROUPS) -> Dict[str, Any]:
    """
    Calculates the required sample size per group and total for a two-sample t-test.
    Uses the standard normal approximation for power analysis (G*Power equivalent logic).
    
    Formula: n = 2 * ((Z_{1-alpha/2} + Z_{1-beta}) / d)^2
    
    Args:
        effect_size: Cohen's d (expected difference in means / pooled std dev)
        power: Desired statistical power (1 - beta)
        alpha: Significance level
        groups: Number of groups (fixed at 2 for this study)
        
    Returns:
        Dictionary with calculated sample sizes and parameters.
    """
    if groups != 2:
        raise ValueError("This implementation assumes a two-group design (Partner vs Tool).")
    
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Calculate sample size per group
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    n_per_group = int(np.ceil(n_per_group))
    total_n = n_per_group * 2
    
    return {
        "effect_size_d": effect_size,
        "target_power": power,
        "alpha": alpha,
        "groups": groups,
        "n_per_group": n_per_group,
        "total_n": total_n,
        "z_alpha": z_alpha,
        "z_beta": z_beta
    }

def calculate_power(n_per_group: int, effect_size: float = EFFECT_SIZE_D, alpha: float = ALPHA) -> float:
    """
    Calculates the achieved power for a given sample size per group.
    
    Args:
        n_per_group: Number of participants per group.
        effect_size: Cohen's d.
        alpha: Significance level.
        
    Returns:
        Calculated power (float between 0 and 1).
    """
    # Non-centrality parameter for t-test
    # For large N, t ~ z, so we can use normal approximation or exact non-central t
    # Using non-central t distribution for accuracy
    df = 2 * n_per_group - 2
    ncp = effect_size * np.sqrt(n_per_group / 2)
    
    # Critical t value
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability that the t-statistic exceeds the critical value
    # under the alternative hypothesis (non-central t)
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return float(power)

def run_power_analysis() -> Dict[str, Any]:
    """
    Executes the prospective power analysis, enforces the recruitment target,
    and returns the final report.
    
    Returns:
        Dictionary containing the analysis results and enforcement status.
    """
    log_script_start("00_power_analysis")
    info("Starting prospective power analysis for N=300 target.")
    
    # 1. Calculate required N based on parameters (d=0.4, power=0.8, alpha=0.05)
    calc_result = calculate_required_n()
    required_total = calc_result['total_n']
    required_per_group = calc_result['n_per_group']
    
    log_analysis_step(f"Calculated required N: {required_total} total ({required_per_group} per group) for d={EFFECT_SIZE_D}, power={TARGET_POWER}")
    
    # 2. Enforce Recruitment Target (FR-009, SC-002)
    # The task requires enforcing the N=300 target.
    # Logic: If calculated N > 300, we must flag that 300 is insufficient.
    # If calculated N <= 300, then 300 is sufficient (or over-powered).
    
    is_target_sufficient = True
    enforcement_message = ""
    
    if required_total > RECRUITMENT_TARGET_N:
        is_target_sufficient = False
        enforcement_message = (
            f"WARNING: The calculated required N ({required_total}) exceeds the target recruitment N ({RECRUITMENT_TARGET_N}). "
            f"To achieve 80% power at d=0.4, recruitment must be increased to {required_total}."
        )
        warning(enforcement_message)
    else:
        enforcement_message = (
            f"Target recruitment N ({RECRUITMENT_TARGET_N}) is sufficient to achieve "
            f"{TARGET_POWER:.0%} power at d={EFFECT_SIZE_D}. "
            f"(Required N: {required_total})."
        )
        info(enforcement_message)
    
    # 3. Calculate actual power at the target N (300)
    # Assuming balanced split: 150 per group
    power_at_target = calculate_power(n_per_group=RECRUITMENT_TARGET_N // 2)
    
    # 4. Compile final report
    report = {
        "analysis_type": "prospective",
        "parameters": {
            "effect_size_d": EFFECT_SIZE_D,
            "target_power": TARGET_POWER,
            "alpha": ALPHA,
            "groups": GROUPS
        },
        "calculations": {
            "required_total_n": required_total,
            "required_per_group": required_per_group,
            "calculated_power_at_target": power_at_target
        },
        "enforcement": {
            "target_n": RECRUITMENT_TARGET_N,
            "is_sufficient": is_target_sufficient,
            "message": enforcement_message
        },
        "recommendation": (
            "Proceed with recruitment of N=300" if is_target_sufficient 
            else f"Increase recruitment to N={required_total}"
        )
    }
    
    log_script_end("00_power_analysis")
    return report

def main():
    """Main entry point for the power analysis script."""
    parser = argparse.ArgumentParser(description="Prospective Power Analysis for AI Framing Study")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument('--output', type=str, default="data/processed/power_analysis_report.json", 
                        help="Path to save the JSON report")
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    info(f"Global seed set to {get_seed()}")
    
    # Run analysis
    report = run_power_analysis()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report to disk
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    info(f"Power analysis report saved to {output_path}")
    print(f"Report saved to: {output_path}")
    
    # Print summary to stdout
    print("\n--- Power Analysis Summary ---")
    print(f"Target Effect Size (d): {report['parameters']['effect_size_d']}")
    print(f"Target Power: {report['parameters']['target_power']}")
    print(f"Calculated Required N: {report['calculations']['required_total_n']}")
    print(f"Recruitment Target N: {report['enforcement']['target_n']}")
    print(f"Sufficient?: {report['enforcement']['is_sufficient']}")
    print(f"Recommendation: {report['recommendation']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())