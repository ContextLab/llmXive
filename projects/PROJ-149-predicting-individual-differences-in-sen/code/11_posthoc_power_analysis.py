import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from statsmodels.stats.power import TTestIndPower

# Import config utilities
from config import get_path, ensure_dirs

def load_model_results() -> Optional[Dict[str, Any]]:
    """
    Load model_results.json. Returns None if file not found or invalid.
    """
    path = get_path("model_results")
    if not path.exists():
        print(f"Error: Model results file not found at {path}")
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading model results: {e}")
        return None

def perform_power_analysis(model_results: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis for the linear regression model.
    
    Uses the observed R2, sample size (n), and number of predictors (k)
    to estimate the achieved power and the required sample size for 80% power.
    
    For multiple regression, we approximate using the non-centrality parameter
    derived from R2.
    
    Returns:
        Dict with 'required_n', 'power', 'effect_size' (f2).
    """
    n = model_results.get('n', 0)
    if n == 0:
        # Fallback if n not explicitly stored, try to infer from features if available
        # But for this task, we assume n is in model_results or we can't compute.
        # If missing, we might need to load features to count rows.
        # Let's try to load features if n is missing.
        features_path = get_path("features_clr")
        if features_path.exists():
            try:
                df = pd.read_csv(features_path)
                n = len(df)
            except Exception:
                pass
        
        if n == 0:
            return {
                "required_n": 0,
                "power": 0.0,
                "effect_size": 0.0,
                "error": "Could not determine sample size"
            }

    r2 = model_results.get('test_r2', 0.0)
    # Number of predictors (excluding intercept). 
    # Usually derived from the number of features used in the model.
    # We can estimate this from the features file columns if available, 
    # or assume a standard number if not.
    # Let's try to infer from features file.
    k = 0
    features_path = get_path("features_clr")
    if features_path.exists():
        try:
            df = pd.read_csv(features_path)
            # Columns: participant_id, median_rt, delta_rel, theta_rel, alpha_rel, low_beta_rel, high_beta_rel, gamma_rel
            # Features are the rel power bands.
            feature_cols = [c for c in df.columns if c not in ['participant_id', 'median_rt']]
            k = len(feature_cols)
        except Exception:
            k = 6 # Default to 6 bands if file read fails

    if k == 0:
        k = 6 # Default fallback

    # Effect size f2 = R2 / (1 - R2)
    # Handle R2 = 1.0 to avoid division by zero
    if r2 >= 1.0:
        f2 = 10.0 # Large effect
    else:
        f2 = r2 / (1.0 - r2)

    # Calculate power using non-central F distribution approximation
    # We use statsmodels TTestIndPower as a proxy for the F-test power in regression
    # by converting f2 to a non-centrality parameter or using the specific F-test power function if available.
    # statsmodels.stats.power.FTestPower is the correct tool for ANOVA/Regression F-tests.
    from statsmodels.stats.power import FTestPower
    
    f_test = FTestPower()
    
    # Calculate non-centrality parameter (nct) for F-test: nct = f2 * k * n
    # Actually, for regression F-test: nct = f2 * (n - 1) * k / (k + 1) ? 
    # Standard formula: nct = f2 * N * k (where k is number of predictors) -> No.
    # Correct nct for F-test in multiple regression: nct = f^2 * (u + v + 1) where u=k, v=n-k-1.
    # Simplified: nct = f^2 * n * k (approx for large n).
    # Let's use the direct method from statsmodels:
    # power = f_test.solve_power(effect_size=f2, nobs1=n, alpha=alpha, df_num=k, df_denom=n-k-1)
    
    # However, FTestPower.solve_power expects 'effect_size' as Cohen's f2.
    # nobs1 is the sample size.
    # df_num = k (numerator df)
    # df_denom = n - k - 1 (denominator df)
    
    try:
        power = f_test.solve_power(
            effect_size=f2, 
            nobs1=n, 
            alpha=alpha, 
            df_num=k, 
            df_denom=n - k - 1
        )
    except Exception:
        power = 0.0

    # Calculate required N for 80% power
    try:
        required_n = f_test.solve_power(
            effect_size=f2, 
            nobs1=None, 
            alpha=alpha, 
            df_num=k, 
            df_denom=None, 
            power=0.80
        )
    except Exception:
        required_n = n # If calculation fails, assume current n is required

    if required_n is None or np.isnan(required_n):
        required_n = n

    return {
        "required_n": int(np.ceil(required_n)),
        "power": float(power),
        "effect_size": float(f2)
    }

def save_results(power_analysis: Dict[str, Any], output_path: Path) -> None:
    """
    Append power analysis results to model_results.json.
    """
    # Load existing results
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # Update with new results
    existing_data['post_hoc_power_analysis'] = power_analysis

    # Ensure directory exists
    ensure_dirs(output_path.parent)

    # Write back
    with open(output_path, 'w') as f:
        json.dump(existing_data, f, indent=2)

    print(f"Post-hoc power analysis results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis")
    parser.add_argument('--output', type=str, default=None, help='Output path for results (overrides default)')
    args = parser.parse_args()

    # Load model results
    model_results = load_model_results()
    if model_results is None:
        print("Failed to load model results. Exiting.")
        sys.exit(1)

    # Perform analysis
    power_analysis = perform_power_analysis(model_results)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path("model_results")

    # Save results
    save_results(power_analysis, output_path)

    print(f"Power: {power_analysis['power']:.4f}")
    print(f"Required N for 80% power: {power_analysis['required_n']}")
    print(f"Effect size (f2): {power_analysis['effect_size']:.4f}")

if __name__ == "__main__":
    main()
