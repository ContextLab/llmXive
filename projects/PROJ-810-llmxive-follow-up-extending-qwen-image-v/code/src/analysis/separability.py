import json
import os
from pathlib import Path
import numpy as np
from scipy.stats import ttest_ind, norm

def calculate_sample_size_for_power(effect_size: float = 0.8, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate the minimum sample size (N per group) required to achieve the specified statistical power.
    
    Uses the standard formula for a two-sample t-test (assuming equal variance and equal sample sizes).
    N = 2 * ((Z_alpha + Z_beta) / effect_size)^2
    
    Args:
        effect_size: Cohen's d (standardized mean difference).
        power: Desired statistical power (1 - beta).
        alpha: Significance level (Type I error rate).
    
    Returns:
        Minimum N required per group.
    """
    z_alpha = norm.ppf(1 - alpha / 2)  # Two-tailed
    z_beta = norm.ppf(power)
    
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n_per_group))

def run_power_analysis(output_path: str, effect_size: float = 0.8, power: float = 0.8, alpha: float = 0.05) -> dict:
    """
    Perform power analysis and write results to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
        effect_size: Target effect size (Cohen's d).
        power: Target power.
        alpha: Significance level.
    
    Returns:
        Dictionary containing the analysis results.
    """
    n_required = calculate_sample_size_for_power(effect_size, power, alpha)
    
    # N_audit is typically a small subset for manual verification (e.g., 50 or 100)
    # ensuring it is less than or equal to N_required if N_required is small, 
    # but usually fixed for audit purposes.
    n_audit = min(100, n_required) if n_required < 100 else 100
    
    results = {
        "N_required": n_required,
        "effect_size": effect_size,
        "power": power,
        "alpha": alpha,
        "N_audit": n_audit,
        "description": f"Minimum sample size per group for effect size {effect_size} with {power} power"
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """
    Main entry point for the power analysis script.
    Writes results to data/results/power_analysis.json.
    """
    # Default parameters as per task requirements
    output_file = "data/results/power_analysis.json"
    effect_size = 0.8
    power = 0.8
    alpha = 0.05
    
    print(f"Running power analysis with effect_size={effect_size}, power={power}, alpha={alpha}...")
    results = run_power_analysis(output_file, effect_size, power, alpha)
    print(f"Power analysis complete. Results written to {output_file}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
