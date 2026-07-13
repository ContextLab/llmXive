import json
import os
from statsmodels.stats.power import FTestAnovaPower

def calculate_sample_size(effect_size: float = 0.25, alpha: float = 0.05, power: float = 0.80, k: int = 3) -> dict:
    """
    Calculates the required sample size per group for a One-Way ANOVA.
    
    Parameters:
    - effect_size: Cohen's f (default 0.25 for medium effect)
    - alpha: Significance level (default 0.05)
    - power: Target power (default 0.80)
    - k: Number of groups (default 3: High, Low, Control)
    
    Returns:
    - Dictionary containing input parameters and the calculated sample size per group (n) and total N.
    """
    analysis = FTestAnovaPower()
    
    # Calculate sample size per group
    n_per_group = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        n_groups=k,
        alternative='larger'
    )
    
    # Round up to nearest integer
    n_per_group = int(n_per_group) + 1
    total_n = n_per_group * k
    
    return {
        "parameters": {
            "effect_size": effect_size,
            "alpha": alpha,
            "target_power": power,
            "number_of_groups": k,
            "test_type": "One-Way ANOVA"
        },
        "results": {
            "sample_size_per_group": n_per_group,
            "total_sample_size": total_n
        }
    }

def main():
    """
    Executes the pre-study power analysis and saves the result to research/power_calculation.json.
    """
    # Define output path relative to project root
    # The task specifies output to `research/power_calculation.json`
    output_dir = "research"
    output_file = os.path.join(output_dir, "power_calculation.json")
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Run calculation with specified parameters from task description
    # f=0.25, alpha=0.05, power=0.80
    result = calculate_sample_size(effect_size=0.25, alpha=0.05, power=0.80, k=3)
    
    # Write to JSON
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Power analysis completed. Results saved to {output_file}")
    print(f"Required sample size per group: {result['results']['sample_size_per_group']}")
    print(f"Total required sample size (N): {result['results']['total_sample_size']}")

if __name__ == "__main__":
    main()
