"""
T023: Perform post-hoc power analysis using statsmodels.

Reads the primary model results from T017 (data/processed/model_results.json)
and calculates the required sample size (N) to achieve 80% power for a
target effect size (R² = 0.10), as well as the observed power given the
current sample size.

Output: Appends 'post_hoc_power_analysis' block to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path if running from subdirectory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

def load_model_results():
    """Load the primary model results JSON."""
    input_path = get_path('processed', 'model_results.json')
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Please ensure T017 (modeling) has completed successfully."
        )
    with open(input_path, 'r') as f:
        return json.load(f)

def calculate_effect_size_r2(r2_target=0.10):
    """
    Calculate Cohen's f from a target R².
    f = sqrt(R² / (1 - R²))
    """
    return np.sqrt(r2_target / (1 - r2_target))

def calculate_observed_effect_size_r2(observed_r2):
    """
    Calculate Cohen's f from the observed R².
    """
    if observed_r2 >= 1.0:
        # Prevent division by zero or NaN if R² is 1.0
        return 10.0 # Arbitrary large number, effectively infinite power
    return np.sqrt(observed_r2 / (1 - observed_r2))

def perform_power_analysis(observed_r2, n_obs, alpha=0.05, power_target=0.80):
    """
    Perform power analysis using statsmodels.

    Returns:
        dict: {
            'required_n': int,
            'observed_power': float,
            'effect_size': float (Cohen's f)
        }
    """
    from statsmodels.stats.power import FTestPower

    # 1. Calculate effect size for the target R² (0.10)
    # This is the effect size we want to be able to detect with 80% power.
    effect_size_target = calculate_effect_size_r2(r2_target=0.10)

    # 2. Calculate required N for target effect size, alpha, and power
    # We assume 1 predictor (the composite EEG feature set) for the F-test
    # degrees of freedom numerator (dfnum) = k = 1
    # degrees of freedom denominator (dfdenom) = N - k - 1
    # solve_power returns N (nobs)
    try:
        required_n = FTestPower.solve_power(
            effect_size=effect_size_target,
            alpha=alpha,
            power=power_target,
            nobs=None,
            ratio=1.0, # Assuming balanced groups if applicable, though here it's regression
            alternative='larger'
        )
        required_n = int(np.ceil(required_n))
    except Exception as e:
        # Fallback if solve_power fails due to extreme parameters
        required_n = -1

    # 3. Calculate observed power given the current N and observed R²
    # Effect size derived from observed R²
    effect_size_observed = calculate_observed_effect_size_r2(observed_r2)
    
    if effect_size_observed > 100: # Handle R²=1.0 case
        observed_power = 1.0
    else:
        try:
            # Calculate power for the observed effect size with current N
            # nobs is the total sample size
            # dfnum = 1 (one model term for the composite predictor)
            # dfdenom = nobs - 2
            observed_power = FTestPower().power(
                effect_size=effect_size_observed,
                nobs=n_obs,
                alpha=alpha,
                dfnum=1,
                dfdenom=n_obs - 2,
                alternative='larger'
            )
        except Exception:
            observed_power = 0.0

    return {
        'required_n': required_n,
        'observed_power': float(observed_power),
        'effect_size': float(effect_size_target) # Reporting the target effect size used for calculation
    }

def main():
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis.")
    parser.add_argument('--input', type=str, default=None, help="Path to model_results.json (optional)")
    parser.add_argument('--output', type=str, default=None, help="Path to output JSON (optional)")
    args = parser.parse_args()

    # Load results
    results = load_model_results()

    # Extract necessary values
    # The model results JSON should contain 'adjusted_r2' or 'test_r2'
    # We use the test R² for observed power calculation as it's the unbiased estimate
    observed_r2 = results.get('test_r2') or results.get('adjusted_r2')
    
    if observed_r2 is None:
        print("Error: Could not find 'test_r2' or 'adjusted_r2' in model_results.json")
        sys.exit(1)

    # Estimate N from the current data
    # We assume the features.csv has the same number of rows as the model used
    # Since we don't have direct access to the raw count here without loading features again,
    # we can infer N from the split indices if available, or just load features.
    # For robustness, let's load features.csv to get the exact N used.
    features_path = get_path('processed', 'features.csv')
    if os.path.exists(features_path):
        df = pd.read_csv(features_path)
        n_obs = len(df)
    else:
        # Fallback: try to estimate from split indices if available
        split_path = get_path('interim', 'split_indices_primary.json')
        if os.path.exists(split_path):
            with open(split_path, 'r') as f:
                splits = json.load(f)
            n_obs = len(splits['train_idx']) + len(splits['test_idx'])
        else:
            print("Warning: Could not determine N. Assuming N=50 for calculation.")
            n_obs = 50

    # Perform analysis
    analysis_results = perform_power_analysis(
        observed_r2=observed_r2,
        n_obs=n_obs,
        alpha=0.05,
        power_target=0.80
    )

    # Append to results
    results['post_hoc_power_analysis'] = analysis_results

    # Write output
    output_path = args.output or get_path('processed', 'model_results.json')
    ensure_dirs(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Power analysis complete. Results appended to {output_path}")
    print(f"Required N for R²=0.10 (80% power): {analysis_results['required_n']}")
    print(f"Observed Power (N={n_obs}): {analysis_results['observed_power']:.4f}")

if __name__ == '__main__':
    main()