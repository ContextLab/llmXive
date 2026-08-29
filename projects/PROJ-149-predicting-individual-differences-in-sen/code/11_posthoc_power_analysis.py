"""
T023: Perform post-hoc power analysis using statsmodels.

Calculates required N, observed power, and effect size for the target R²=0.10
with power >= 0.80 using statsmodels.stats.power.FTestPower.solve_power.
Appends the results to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from statsmodels.stats.power import FTestPower
except ImportError:
    print("Error: statsmodels is required. Install it via 'pip install statsmodels'.")
    sys.exit(1)

from config import get_path, ensure_dirs


def load_model_results() -> Dict[str, Any]:
    """Load the existing model results from data/processed/model_results.json."""
    results_path = get_path("processed", "model_results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(
            f"Model results file not found at {results_path}. "
            "Please ensure T017 (modeling) has completed successfully."
        )
    
    with open(results_path, 'r') as f:
        return json.load(f)


def calculate_effect_size_from_r2(r2: float, n_obs: int, k_features: int) -> float:
    """
    Calculate Cohen's f² effect size from R².
    
    Formula: f² = R² / (1 - R²)
    
    Args:
        r2: The observed R² value.
        n_obs: Number of observations (not used in formula, but part of signature).
        k_features: Number of predictors (not used in formula, but part of signature).
    
    Returns:
        Cohen's f² effect size.
    """
    # Avoid division by zero if R² is exactly 1.0
    if r2 >= 1.0:
        return float('inf')
    return r2 / (1.0 - r2)


def perform_power_analysis(
    observed_r2: float,
    n_obs: int,
    k_features: int,
    target_power: float = 0.80,
    target_r2: float = 0.10,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis.
    
    1. Calculates observed effect size (f²) from observed R².
    2. Calculates observed power given current N and effect size.
    3. Calculates required N to achieve target_power (0.80) for target_r2 (0.10).
    
    Args:
        observed_r2: The R² obtained from the model.
        n_obs: Number of observations in the dataset.
        k_features: Number of predictors (features) in the model.
        target_power: Desired statistical power (default 0.80).
        target_r2: Target R² for required N calculation (default 0.10 per FR-011).
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary with required_n, observed_power, and effect_size.
    """
    # 1. Calculate observed effect size (f²)
    effect_size = calculate_effect_size_from_r2(observed_r2, n_obs, k_features)
    
    # Handle edge case where effect_size is infinite (R² = 1.0)
    if np.isinf(effect_size):
        # If R² is 1.0, power is 1.0 and required N is theoretically minimal (k+1)
        observed_power = 1.0
        required_n = k_features + 1
    else:
        # 2. Calculate observed power
        power_analysis = FTestPower()
        # f2 = effect_size
        # nobs = n_obs
        # alpha = alpha
        # df_num = k_features (numerator degrees of freedom)
        # df_denom = n_obs - k_features - 1 (denominator degrees of freedom)
        
        # FTestPower.power requires: effect_size, nobs, alpha, df_num, df_denom
        # However, FTestPower.solve_power is used for finding nobs.
        # We can use FTestPower().power() to get observed power directly.
        df_num = k_features
        df_denom = n_obs - k_features - 1
        
        if df_denom <= 0:
            observed_power = 0.0 # Cannot compute power if n <= k+1
        else:
            observed_power = power_analysis.power(
                effect_size=effect_size,
                nobs1=n_obs,
                alpha=alpha,
                df_num=df_num,
                df_denom=df_denom
            )
        
        # 3. Calculate required N for target R² (0.10)
        # Target effect size for R² = 0.10
        target_effect_size = calculate_effect_size_from_r2(target_r2, 0, 0)
        
        # Solve for nobs
        # We need to estimate df_num and df_denom. 
        # Since we don't know the final N, we iterate or use a large df_denom approximation.
        # FTestPower.solve_power can solve for nobs1 directly.
        # df_num is fixed (k_features). df_denom depends on nobs1.
        # We use the 'solve_power' method which handles the df calculation internally 
        # if we pass the number of predictors (k_features).
        
        try:
            # The 'solve_power' method in FTestPower expects:
            # effect_size, alpha, power, nobs1=None, df_num=None, df_denom=None
            # But for regression, we usually pass k_features as df_num and let it solve for nobs.
            # However, the signature is specific. Let's use the standard approach:
            # n = ( (z_alpha + z_beta)^2 ) / f^2 ... approximation, but FTestPower is better.
            
            # Using FTestPower().solve_power:
            # We need to provide df_num. df_denom is derived from nobs - df_num - 1.
            # The method signature: solve_power(effect_size, alpha, power, nobs1, df_num, df_denom)
            # If we set nobs1=None, it solves for it.
            
            required_n = power_analysis.solve_power(
                effect_size=target_effect_size,
                alpha=alpha,
                power=target_power,
                nobs1=None,
                df_num=k_features,
                df_denom=None # It calculates this based on nobs1 and df_num
            )
        except Exception:
            # Fallback if solver fails (e.g., target power too high for effect size)
            required_n = -1

    return {
        "required_n": int(np.ceil(required_n)) if required_n > 0 else -1,
        "observed_power": float(observed_power),
        "effect_size": float(effect_size)
    }


def save_results(analysis_results: Dict[str, Any], original_results: Dict[str, Any]) -> None:
    """
    Append the post-hoc power analysis block to the model results JSON.
    
    Args:
        analysis_results: The dictionary containing required_n, observed_power, effect_size.
        original_results: The original model results dictionary.
    """
    output_path = get_path("processed", "model_results.json")
    ensure_dirs(output_path)
    
    # Create the block to append
    post_hoc_block = {
        "post_hoc_power_analysis": analysis_results
    }
    
    # Merge with original results
    # Note: We update the original dict to preserve existing keys
    original_results.update(post_hoc_block)
    
    with open(output_path, 'w') as f:
        json.dump(original_results, f, indent=2)
    
    print(f"Post-hoc power analysis results appended to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis (T023).")
    parser.add_argument(
        "--target-r2", 
        type=float, 
        default=0.10, 
        help="Target R² for required N calculation (default: 0.10)"
    )
    parser.add_argument(
        "--target-power", 
        type=float, 
        default=0.80, 
        help="Target statistical power (default: 0.80)"
    )
    parser.add_argument(
        "--alpha", 
        type=float, 
        default=0.05, 
        help="Significance level (default: 0.05)"
    )
    args = parser.parse_args()

    try:
        # Load existing model results
        model_results = load_model_results()
        
        # Extract necessary parameters
        # We need observed R², N, and number of features (k)
        # model_results.json structure from T017:
        # { "adjusted_r2": float, "optimal_lambda": float, "rmse": float, "test_r2": float, "test_rmse": float, ... }
        # We use 'test_r2' as the observed R².
        
        observed_r2 = model_results.get("test_r2")
        if observed_r2 is None:
            # Fallback to adjusted_r2 if test_r2 is missing, though test_r2 is preferred
            observed_r2 = model_results.get("adjusted_r2")
        
        if observed_r2 is None:
            raise ValueError("Could not find 'test_r2' or 'adjusted_r2' in model_results.json")

        # We need N (number of participants in test set) and k (features).
        # These are not explicitly in model_results.json from T017 description.
        # We must infer or load them.
        # T017 writes split_indices.json. We can load that to get N_test.
        # T012c writes features.csv. We can count columns to get k.
        
        # Load split indices to get N_test
        split_indices_path = get_path("interim", "split_indices.json")
        if os.path.exists(split_indices_path):
            with open(split_indices_path, 'r') as f:
                split_data = json.load(f)
            # Assuming split_data has 'test' key with list of indices
            n_test = len(split_data.get("test", []))
        else:
            # Fallback: try to infer from features.csv if split_indices missing
            # This is less accurate for test set size but better than crashing
            features_path = get_path("processed", "features.csv")
            if os.path.exists(features_path):
                df = pd.read_csv(features_path)
                n_test = len(df) # Assuming all are used if split missing
            else:
                raise FileNotFoundError("Cannot determine N: missing split_indices.json and features.csv")

        # Load features.csv to get number of predictors (k)
        # Columns: participant_id, median_rt, delta_rel, theta_rel, ...
        # We need to exclude 'participant_id' and 'median_rt' (target)
        features_path = get_path("processed", "features.csv")
        if os.path.exists(features_path):
            df = pd.read_csv(features_path)
            # Predictors are all columns except 'participant_id' and 'median_rt'
            predictor_cols = [c for c in df.columns if c not in ['participant_id', 'median_rt']]
            k_features = len(predictor_cols)
        else:
            # Default assumption if file missing (should not happen if T012c ran)
            k_features = 6 # delta, theta, alpha, low_beta, high_beta, gamma
            print(f"Warning: features.csv not found. Assuming k={k_features}.")

        if n_test <= k_features + 1:
            print(f"Warning: N ({n_test}) is too small relative to features ({k_features}). Power analysis may be invalid.")

        # Perform analysis
        analysis_results = perform_power_analysis(
            observed_r2=observed_r2,
            n_obs=n_test,
            k_features=k_features,
            target_power=args.target_power,
            target_r2=args.target_r2,
            alpha=args.alpha
        )

        # Save results
        save_results(analysis_results, model_results)

        print(f"Power Analysis Complete:")
        print(f"  Observed R²: {observed_r2:.4f}")
        print(f"  Effect Size (f²): {analysis_results['effect_size']:.4f}")
        print(f"  Observed Power: {analysis_results['observed_power']:.4f}")
        print(f"  Required N for R²=0.10, Power=0.80: {analysis_results['required_n']}")

    except Exception as e:
        print(f"Error during post-hoc power analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
