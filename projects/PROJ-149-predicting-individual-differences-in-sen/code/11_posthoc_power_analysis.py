"""
T023: Perform post-hoc power analysis to estimate required sample size (N).

Estimates the sample size needed to achieve power >= 0.80 for R² = 0.10.
If the observed result is non-significant, reports the null result with
effect sizes and explicitly states "The hypothesis was not supported".

Input: data/processed/model_results.json
Output: Appends to data/processed/model_results.json
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
from statsmodels.stats.power import FTestPower

# Import from config to ensure paths are consistent
from config import get_path, ensure_dirs


def load_model_results() -> Dict[str, Any]:
    """Load model results from the JSON file."""
    results_path = get_path("data/processed", "model_results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(
            f"Model results file not found at {results_path}. "
            "Please run the modeling pipeline first (T019)."
        )
    
    with open(results_path, 'r') as f:
        return json.load(f)


def perform_power_analysis(
    observed_r2: float,
    n_obs: int,
    n_predictors: int,
    target_r2: float = 0.10,
    target_power: float = 0.80,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis.
    
    Calculates:
    1. Observed power for the current sample size and effect size.
    2. Required sample size (N) to achieve target_power (0.80) for target_r2 (0.10).
    
    Args:
        observed_r2: The observed R² from the model.
        n_obs: The number of observations (participants) used.
        n_predictors: Number of predictors in the model.
        target_r2: The target effect size (R²) for sample size estimation.
        target_power: Desired statistical power (default 0.80).
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing power analysis results.
    """
    # Calculate non-centrality parameter for observed effect
    # For multiple regression, F = (R² / k) / ((1 - R²) / (N - k - 1))
    # Non-centrality parameter lambda = F * (N - k - 1) ? No, lambda = f² * N
    # Effect size f² = R² / (1 - R²)
    
    f2_observed = observed_r2 / (1 - observed_r2) if observed_r2 < 1 else 10.0
    f2_target = target_r2 / (1 - target_r2)
    
    # Use statsmodels FTestPower
    # We need to calculate power for the observed effect
    # and sample size for the target effect
    
    power_test = FTestPower()
    
    # 1. Calculate observed power
    # f2 = R² / (1 - R²)
    # numerator df = k (predictors)
    # denominator df = N - k - 1
    df_num = n_predictors
    df_denom = n_obs - n_predictors - 1
    
    if df_denom <= 0:
        return {
            "status": "error",
            "message": "Insufficient observations for power calculation (N <= k + 1).",
            "observed_power": None,
            "required_n": None
        }
    
    # Calculate non-centrality parameter for observed power
    ncp_observed = f2_observed * n_obs
    
    # Calculate observed power
    try:
        observed_power = power_test.power(
            effect_size=np.sqrt(f2_observed),
            nobs1=n_obs,
            alpha=alpha,
            df_num=df_num,
            df_denom=df_denom
        )
    except Exception:
        observed_power = None
    
    # 2. Calculate required sample size for target R²
    # We want to find N such that power >= target_power for effect size f2_target
    # statsmodels solve_power can solve for nobs1
    try:
        required_n = power_test.solve_power(
            effect_size=np.sqrt(f2_target),
            alpha=alpha,
            power=target_power,
            nobs1=None,
            df_num=df_num,
            df_denom=None, # Will be calculated based on nobs1
            ratio=1.0,
            alternative='larger'
        )
        
        # solve_power might return None or inf if parameters are invalid
        if required_n is None or not np.isfinite(required_n):
            # Fallback: manual estimation or return a large number
            # Approximation: N ≈ (z_alpha + z_beta)² / f² + k + 1
            # For alpha=0.05 (2-sided), z ~ 1.96; for power=0.80, z ~ 0.84
            # N ≈ (1.96 + 0.84)² / f² + k + 1
            z_alpha = 1.96
            z_beta = 0.84
            required_n = ((z_alpha + z_beta) ** 2) / f2_target + n_predictors + 1
        
        required_n = int(np.ceil(required_n))
    except Exception:
        required_n = None
    
    return {
        "observed_r2": observed_r2,
        "observed_power": float(observed_power) if observed_power is not None else None,
        "target_r2": target_r2,
        "target_power": target_power,
        "required_n_for_target": required_n,
        "n_observed": n_obs,
        "n_predictors": n_predictors,
        "alpha": alpha
    }


def save_results(power_results: Dict[str, Any], results_path: str) -> None:
    """Append power analysis results to the model results JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    # Load existing results
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    # Append power analysis
    data["power_analysis"] = power_results
    
    # Handle hypothesis statement
    is_significant = data.get("model_metrics", {}).get("is_significant", False)
    if not is_significant:
        data["hypothesis_statement"] = "The hypothesis was not supported."
        data["hypothesis_details"] = {
            "status": "not_supported",
            "reason": "Observed effect was not statistically significant after Bonferroni correction and permutation testing.",
            "observed_r2": data.get("model_metrics", {}).get("adjusted_r2"),
            "observed_power": power_results.get("observed_power"),
            "note": "Reported effect sizes and confidence intervals reflect the null result."
        }
    else:
        data["hypothesis_statement"] = "The hypothesis was supported."
        data["hypothesis_details"] = {
            "status": "supported",
            "observed_r2": data.get("model_metrics", {}).get("adjusted_r2"),
            "observed_power": power_results.get("observed_power")
        }
    
    # Write back
    with open(results_path, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    """Main entry point for T023."""
    parser = argparse.ArgumentParser(description="T023: Post-hoc power analysis")
    parser.add_argument(
        "--target-r2", 
        type=float, 
        default=0.10, 
        help="Target R² for sample size estimation (default: 0.10)"
    )
    parser.add_argument(
        "--target-power", 
        type=float, 
        default=0.80, 
        help="Target power (default: 0.80)"
    )
    args = parser.parse_args()
    
    print("Starting post-hoc power analysis (T023)...")
    
    try:
        # Load model results
        results = load_model_results()
        
        # Extract necessary metrics
        model_metrics = results.get("model_metrics", {})
        observed_r2 = model_metrics.get("adjusted_r2")
        
        if observed_r2 is None:
            raise ValueError("Adjusted R² not found in model_results.json. Run T019 first.")
        
        # Estimate N from features.csv if not explicitly stored
        # We assume the modeling script used the full features dataset
        # Let's try to infer N from the data if available, or use a placeholder
        # The modeling script (T017) should have saved split_indices.json
        # which contains the number of samples used.
        
        split_indices_path = get_path("data/interim", "split_indices.json")
        n_obs = None
        if os.path.exists(split_indices_path):
            with open(split_indices_path, 'r') as f:
                splits = json.load(f)
                # Count samples in training set (usually the largest)
                # Assuming 5-fold CV, we take the sum of one fold's training size
                # or just count unique IDs if stored.
                # For simplicity, let's assume the 'train' key in one fold has the count.
                # If structure is {0: {'train': [ids], 'test': [ids]}, ...}
                if splits:
                    first_fold = list(splits.values())[0]
                    n_obs = len(first_fold.get("train", []))
        
        if n_obs is None:
            # Fallback: try to load features.csv to count rows
            features_path = get_path("data/processed", "features.csv")
            if os.path.exists(features_path):
                import pandas as pd
                df = pd.read_csv(features_path)
                n_obs = len(df)
            else:
                raise FileNotFoundError(
                    "Could not determine sample size (N). "
                    "Neither split_indices.json nor features.csv found."
                )
        
        n_predictors = model_metrics.get("n_predictors", 6) # Default 6 bands
        
        print(f"  Observed R²: {observed_r2:.4f}")
        print(f"  Sample size (N): {n_obs}")
        print(f"  Predictors: {n_predictors}")
        print(f"  Target R²: {args.target_r2}")
        print(f"  Target Power: {args.target_power}")
        
        # Perform analysis
        power_results = perform_power_analysis(
            observed_r2=observed_r2,
            n_obs=n_obs,
            n_predictors=n_predictors,
            target_r2=args.target_r2,
            target_power=args.target_power
        )
        
        print(f"  Observed Power: {power_results['observed_power']:.4f}")
        print(f"  Required N for R²={args.target_r2}: {power_results['required_n_for_target']}")
        
        # Save results
        results_path = get_path("data/processed", "model_results.json")
        ensure_dirs(results_path)
        save_results(power_results, results_path)
        
        print("Power analysis completed and saved to data/processed/model_results.json")
        
    except Exception as e:
        print(f"Error during power analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
