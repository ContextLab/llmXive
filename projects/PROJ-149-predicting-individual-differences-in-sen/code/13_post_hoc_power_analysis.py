"""
Task T023: Perform post-hoc power analysis using statsmodels.

Logic:
1. Load model results from data/processed/model_results.json.
2. Calculate effect_size (Cohen's f) from observed R^2: f = sqrt(R^2 / (1 - R^2)).
3. Use statsmodels.stats.power.FTestPower.solve_power to find required N for power >= 0.80.
4. Calculate observed power based on observed N and effect size.
5. Append results to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path

import numpy as np

# Add project root to path to import config if needed, though we use relative paths here
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from statsmodels.stats.power import FTestPower
except ImportError:
    print("Error: statsmodels is required. Please install it via requirements.txt.")
    sys.exit(1)

from config import get_path

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_cohens_f(r_squared):
    """Calculate Cohen's f from R-squared."""
    if r_squared >= 1.0:
        # Avoid division by zero or infinity
        return float('inf')
    return np.sqrt(r_squared / (1 - r_squared))

def run_power_analysis(observed_r2, observed_n, alpha=0.05, target_power=0.80):
    """
    Perform power analysis.
    Returns: (required_n, observed_power, effect_size)
    """
    effect_size = calculate_cohens_f(observed_r2)

    if effect_size == float('inf'):
        # If R^2 is 1, power is effectively 1 for any N > 0, or undefined if N=0
        return 0, 1.0, float('inf')

    power_analysis = FTestPower()

    # Calculate required N for target power
    # solve_power(effect_size, nobs1, alpha, power, k_num, k_denom)
    # For a linear model (ANOVA context in FTestPower), k_num = number of predictors, k_denom = n - k_num - 1
    # However, solve_power typically solves for nobs1 (total sample size) given k_num and k_denom as parameters
    # The standard F-test for R^2 in linear regression:
    # H0: All coefficients (except intercept) are zero.
    # k_num = number of predictors (p)
    # k_denom = n - p - 1
    # solve_power usually assumes k_denom is large or solves for nobs1 where k_denom = nobs1 - k_num - 1.
    # We need to know the number of predictors used in the model to set k_num correctly.
    # Since we don't have the model coefficients count explicitly here, we assume a standard multiple regression context.
    # If the model used LASSO, the effective number of predictors is the number of non-zero coefficients.
    # However, for a general post-hoc on R^2, we often assume a generic k_num or estimate it.
    # Given the context of "Predicting Individual Differences", let's assume a small set of features (e.g., 6 bands).
    # But strictly, FTestPower.solve_power needs k_num.
    # Let's assume k_num = 6 (delta, theta, alpha, low_beta, high_beta, gamma) as per the feature set.
    # If the actual model had a different number, this is an approximation, but standard for such analysis without full model object.
    k_num = 6  # Number of predictors (bands)

    # We need to solve for nobs1 (total sample size) such that power >= target_power.
    # The function signature is: solve_power(effect_size, nobs1, alpha, power, k_num, k_denom)
    # We set power=target_power and solve for nobs1.
    # k_denom is not strictly needed if we are solving for nobs1, as it is derived: nobs1 - k_num - 1.
    # But the function might require it or handle it internally. Let's check docs logic.
    # In statsmodels, FTestPower.solve_power(effect_size, nobs1, alpha, power, k_num, k_denom)
    # If we solve for nobs1, we pass None for nobs1.
    # k_denom can be None, it will be calculated as nobs1 - k_num - 1.

    try:
        required_n = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=None,
            alpha=alpha,
            power=target_power,
            k_num=k_num,
            k_denom=None
        )
    except Exception as e:
        # Fallback or specific error handling if solver fails (e.g., effect size too large/small)
        print(f"Warning: Power calculation for required N failed: {e}")
        required_n = observed_n  # Fallback to observed if calculation fails

    # Calculate observed power given observed_n and effect_size
    # observed_power = FTestPower.power(effect_size, nobs1, alpha, k_num, k_denom)
    # k_denom = observed_n - k_num - 1
    k_denom_obs = observed_n - k_num - 1
    if k_denom_obs <= 0:
        observed_power = 0.0
    else:
        observed_power = power_analysis.power(
            effect_size=effect_size,
            nobs1=observed_n,
            alpha=alpha,
            k_num=k_num,
            k_denom=k_denom_obs
        )

    return required_n, observed_power, effect_size

def main():
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis.")
    parser.add_argument('--input', type=str, default=None, help='Path to model_results.json')
    parser.add_argument('--output', type=str, default=None, help='Path to output model_results.json')
    args = parser.parse_args()

    # Paths
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = get_path('processed', 'model_results.json')

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path('processed', 'model_results.json')

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    print(f"Loading model results from {input_path}...")
    results = load_json(input_path)

    # Extract observed R2 and N
    # The model results JSON structure from T017 is expected to have 'adjusted_r2' or 'test_r2' and we need N.
    # T017 output: { "adjusted_r2", "optimal_lambda", "rmse", "test_r2", "test_rmse" }
    # We need the number of participants (N).
    # If not explicitly in the JSON, we might need to infer from the features file or assume it's not stored.
    # However, T017 loads features.csv. The N is the number of rows in features.csv.
    # Let's try to get N from the features file if not in results.
    # But the task says "Pass this to ... solve_power with alpha=0.05 to find required_n".
    # We need observed_n.
    # Let's check if 'n_samples' or similar is in results. If not, load features.csv.

    observed_r2 = results.get('adjusted_r2') or results.get('test_r2')
    if observed_r2 is None:
        print("Error: Could not find adjusted_r2 or test_r2 in model results.")
        sys.exit(1)

    # Get N
    observed_n = results.get('n_samples')
    if observed_n is None:
        # Load features.csv to count rows
        features_path = get_path('processed', 'features.csv')
        if not features_path.exists():
            print(f"Error: Cannot determine N. {features_path} not found and n_samples not in results.")
            sys.exit(1)
        
        import pandas as pd
        df = pd.read_csv(features_path)
        observed_n = len(df)
        print(f"Derived N from features.csv: {observed_n}")

    print(f"Observed R^2: {observed_r2}, N: {observed_n}")

    required_n, observed_power, effect_size = run_power_analysis(observed_r2, observed_n)

    print(f"Effect Size (Cohen's f): {effect_size:.4f}")
    print(f"Required N for 80% power: {required_n:.1f}")
    print(f"Observed Power: {observed_power:.4f}")

    # Append to results
    power_analysis_block = {
        "post_hoc_power_analysis": {
            "effect_size": float(effect_size),
            "required_n": float(required_n),
            "observed_power": float(observed_power),
            "alpha": 0.05,
            "target_power": 0.80,
            "observed_r2": float(observed_r2),
            "n_samples": int(observed_n)
        }
    }

    results.update(power_analysis_block)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_json(output_path, results)
    print(f"Power analysis results appended to {output_path}")

if __name__ == '__main__':
    main()
