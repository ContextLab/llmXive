import os
import math
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import nct

# Constants for the study design
# Effect size: Cohen's f^2 >= 0.02 (small effect)
# Power: 0.80
# Alpha: 0.05
DEFAULT_EFFECT_SIZE_F2 = 0.02
DEFAULT_POWER = 0.80
DEFAULT_ALPHA = 0.05

def calculate_min_sample_size(
    f2: float = DEFAULT_EFFECT_SIZE_F2,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    num_predictors: int = 1
) -> int:
    """
    Calculate the minimum sample size (N) required for a multiple regression analysis.
    
    Uses the non-central F-distribution approximation to find N such that the power
    of the F-test for the R-squared term is at least `power`.
    
    Parameters
    ----------
    f2 : float
        Cohen's f-squared effect size (e.g., 0.02 for small).
    power : float
        Desired statistical power (e.g., 0.80).
    alpha : float
        Significance level (e.g., 0.05).
    num_predictors : int
        Number of independent variables (k) in the model.
        
    Returns
    -------
    int
        The minimum required sample size N.
    """
    if f2 <= 0 or power <= 0 or power >= 1 or alpha <= 0 or alpha >= 1:
        raise ValueError("Invalid parameters for power analysis.")
    
    # We need to find N such that Power(F) >= desired_power
    # The F-statistic for R-squared follows a non-central F distribution.
    # df1 = k (num_predictors)
    # df2 = N - k - 1
    # Non-centrality parameter (lambda) = f^2 * N
    
    k = num_predictors
    
    # Initial guess using the rule of thumb or approximation
    # N approx = (L / f^2) + k + 1, where L is the non-centrality parameter for the target power.
    # For alpha=0.05, power=0.80, df1=1, L is approx 7.85.
    # For df1 > 1, L is slightly higher.
    
    # We will iterate to find the exact N
    N_start = k + 2  # Minimum possible N
    
    # Binary search or iterative approach
    # Since N must be integer, we increment until power is met.
    # Given the constraints, N won't be astronomically large for small f2.
    
    # Approximate L for power=0.80, alpha=0.05, df1=1 is ~7.85
    # L = f^2 * N  => N = L / f^2
    # For f2=0.02, N ~ 7.85 / 0.02 = 392.5. So we start searching around there.
    
    # Let's implement a robust search
    N = int(500) # Start with a reasonable guess for small effect size
    
    # If our guess is too low, increase. If too high, decrease (though we usually start low).
    # We want the SMALLEST N that satisfies the condition.
    
    # Helper to calculate power for a given N
    def get_power_for_n(current_n):
        df1 = k
        df2 = current_n - k - 1
        if df2 <= 0:
            return 0.0
        
        non_central_param = f2 * current_n
        
        # Critical F value
        # Using scipy's f.ppf (percent point function)
        # We need to import from scipy.stats inside to avoid circular issues if any, 
        # though standard imports are fine.
        from scipy.stats import f, nct
        
        f_crit = f.ppf(1 - alpha, df1, df2)
        
        # Power is the probability that the non-central F > f_crit
        # Power = 1 - CDF(f_crit, df1, df2, non_central_param)
        power_val = 1.0 - nct.cdf(f_crit, df1, df2, non_central_param)
        return power_val

    # Search for minimum N
    # Start from a lower bound and go up
    # Lower bound: k + 2
    low = k + 2
    high = 10000 # Upper safety limit
    
    # First, ensure we find a high enough N
    while get_power_for_n(high) < power:
        high *= 2
        if high > 1000000:
            raise ValueError("Could not find sample size within reasonable bounds.")
    
    # Binary search
    while low < high:
        mid = (low + high) // 2
        if get_power_for_n(mid) >= power:
            high = mid
        else:
            low = mid + 1
    
    return low

def run_power_analysis(
    f2: float = DEFAULT_EFFECT_SIZE_F2,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    num_predictors: int = 1
) -> Dict[str, Any]:
    """
    Run the power analysis and return a dictionary of results.
    
    Returns
    -------
    dict
        Dictionary containing input parameters, calculated N, and metadata.
    """
    min_n = calculate_min_sample_size(f2, power, alpha, num_predictors)
    
    result = {
        "parameters": {
            "effect_size_f2": f2,
            "power": power,
            "alpha": alpha,
            "num_predictors": num_predictors
        },
        "results": {
            "minimum_sample_size_N": min_n
        },
        "metadata": {
            "description": "Minimum sample size for multiple regression to detect Cohen's f^2 >= 0.02",
            "calculation_method": "Non-central F-distribution approximation"
        }
    }
    
    return result

def save_power_analysis(result: Dict[str, Any], output_path: str) -> None:
    """
    Save the power analysis result to a YAML file.
    
    Parameters
    ----------
    result : dict
        The result dictionary from run_power_analysis.
    output_path : str
        Path to the output YAML file.
    """
    import yaml
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point to run power analysis and save results.
    """
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/
    # The task specifies output: state/power_analysis.yaml
    # We assume the current working directory is the project root.
    
    output_path = "state/power_analysis.yaml"
    
    print(f"Running power analysis for: f2={DEFAULT_EFFECT_SIZE_F2}, power={DEFAULT_POWER}, alpha={DEFAULT_ALPHA}")
    
    result = run_power_analysis(
        f2=DEFAULT_EFFECT_SIZE_F2,
        power=DEFAULT_POWER,
        alpha=DEFAULT_ALPHA,
        num_predictors=1 # Initial baseline, can be adjusted if more predictors are known
    )
    
    save_power_analysis(result, output_path)
    print(f"Power analysis complete. Minimum sample size N = {result['results']['minimum_sample_size_N']}")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
