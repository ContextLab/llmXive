import json
import os
from statsmodels.stats.power import FTestAnovaPower

def calculate_sample_size(effect_size=0.25, alpha=0.05, power=0.80, k=3):
    """
    Calculate the required sample size per group for a one-way ANOVA.
    
    Args:
        effect_size: Cohen's f effect size (default 0.25 for medium)
        alpha: Significance level (default 0.05)
        power: Target statistical power (default 0.80)
        k: Number of groups (default 3: High, Low, Control)
        
    Returns:
        dict: Contains sample size per group and total N
    """
    analysis = FTestAnovaPower()
    n_per_group = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        n_groups=k
    )
    
    return {
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "num_groups": k,
        "n_per_group": int(n_per_group),
        "total_n": int(n_per_group * k)
    }

def main():
    """
    Main entry point to run power analysis and save results.
    """
    # Define parameters based on research plan
    effect_size = 0.25  # Medium effect size (Cohen's f)
    alpha = 0.05
    target_power = 0.80
    num_groups = 3  # High Agency, Low Agency, Control
    
    # Calculate sample size
    result = calculate_sample_size(
        effect_size=effect_size,
        alpha=alpha,
        power=target_power,
        k=num_groups
    )
    
    # Ensure output directory exists
    output_dir = "research"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON
    output_path = os.path.join(output_dir, "power_calculation.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
        
    print(f"Power analysis complete. Results saved to {output_path}")
    print(f"Required N per group: {result['n_per_group']}")
    print(f"Total required N: {result['total_n']}")
    
    return result

if __name__ == "__main__":
    main()
