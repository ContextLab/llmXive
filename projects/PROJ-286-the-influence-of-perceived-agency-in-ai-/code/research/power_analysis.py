"""
Power analysis module for calculating required sample sizes for One-Way ANOVA.

This module uses statsmodels to calculate the sample size needed to achieve
a target power level for detecting a specified effect size (Cohen's f).
"""
import json
import os
from statsmodels.stats.power import FTestAnovaPower

def calculate_sample_size(effect_size: float = 0.25, alpha: float = 0.05, power: float = 0.80, k_groups: int = 3) -> int:
    """
    Calculate the required sample size per group for a One-Way ANOVA.
    
    Args:
        effect_size: Cohen's f effect size (0.10=small, 0.25=medium, 0.40=large)
        alpha: Significance level (Type I error rate)
        power: Target statistical power (1 - Type II error rate)
        k_groups: Number of groups in the ANOVA (High, Low, Control)
        
    Returns:
        Required sample size per group (rounded up to nearest integer)
    """
    analysis = FTestAnovaPower()
    n_per_group = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        n_groups=k_groups
    )
    
    if n_per_group is None:
        raise ValueError("Could not calculate sample size. Check input parameters.")
        
    return int(n_per_group) + 1  # Round up to ensure sufficient power

def main():
    """
    Execute power analysis and save results to research/power_calculation.json.
    
    This function calculates the sample size for the study's power analysis
    using the specified parameters (f=0.25, alpha=0.05, power=0.80) and
    saves the results to a JSON file for documentation and reproducibility.
    """
    # Define analysis parameters based on study design
    effect_size = 0.25  # Medium effect size (Cohen's f)
    alpha = 0.05        # Standard significance level
    target_power = 0.80 # Desired statistical power
    k_groups = 3        # High Agency, Low Agency, Control
    
    # Calculate required sample size per group
    n_per_group = calculate_sample_size(
        effect_size=effect_size,
        alpha=alpha,
        power=target_power,
        k_groups=k_groups
    )
    
    total_n = n_per_group * k_groups
    
    # Prepare results
    results = {
        "effect_size": effect_size,
        "alpha": alpha,
        "target_power": target_power,
        "k_groups": k_groups,
        "n_per_group": n_per_group,
        "total_required_n": total_n,
        "analysis_method": "One-Way ANOVA (F-test)",
        "software": "statsmodels"
    }
    
    # Ensure output directory exists
    output_dir = "research"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save results to JSON
    output_path = os.path.join(output_dir, "power_calculation.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Power analysis completed successfully.")
    print(f"Required sample size: {n_per_group} per group ({total_n} total)")
    print(f"Results saved to: {output_path}")
    
    return results

if __name__ == "__main__":
    main()
