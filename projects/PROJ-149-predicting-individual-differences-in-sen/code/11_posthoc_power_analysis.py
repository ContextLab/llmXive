"""
Task T023: Post-hoc Power Analysis

Performs post-hoc power analysis using statsmodels to determine the required
sample size for a target R² of 0.10 with power >= 0.80, given the observed
effect size from the modeling results.

Appends the results to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import config for paths
# Note: We assume config.py is in the same directory or PYTHONPATH
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for direct execution if config is not in path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path, ensure_dirs

import numpy as np

# Attempt to import statsmodels
try:
    from statsmodels.stats.power import FTestPower
    from statsmodels.stats.ftest import f_oneway
    import scipy.stats as stats
except ImportError:
    print("ERROR: statsmodels is required for power analysis. Install with: pip install statsmodels")
    sys.exit(1)


def load_model_results() -> Optional[Dict[str, Any]]:
    """
    Loads the model results from data/processed/model_results.json.
    Returns None if the file does not exist.
    """
    try:
        path = get_path("processed", "model_results.json")
        if not os.path.exists(path):
            print(f"Warning: Model results file not found at {path}")
            return None
        
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading model results: {e}")
        return None


def calculate_effect_size_from_r2(r2: float, n_obs: int, n_predictors: int) -> float:
    """
    Calculates Cohen's f² effect size from R².
    
    Formula: f² = R² / (1 - R²)
    
    Args:
        r2: The R² value from the model.
        n_obs: Number of observations (not strictly needed for f² calculation itself, 
               but useful for context).
        n_predictors: Number of predictors (not strictly needed for f² calculation itself).
    
    Returns:
        Cohen's f² effect size.
    """
    if r2 >= 1.0:
        # Avoid division by zero or infinity
        return float('inf')
    if r2 <= 0:
        return 0.0
    
    f_squared = r2 / (1.0 - r2)
    return f_squared


def perform_power_analysis(
    observed_r2: float, 
    n_obs: int, 
    n_predictors: int,
    target_r2: float = 0.10,
    target_power: float = 0.80,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Performs post-hoc power analysis.
    
    Calculates:
    1. The observed effect size (f²) from the actual model R².
    2. The power of the current study given the observed effect size and N.
    3. The required sample size (required_n) to achieve target_power (0.80) 
       for the target R² (0.10).
    
    Args:
        observed_r2: The R² achieved in the current study.
        n_obs: Current number of observations.
        n_predictors: Number of predictors in the model.
        target_r2: The target R² for power calculation (default 0.10).
        target_power: Desired statistical power (default 0.80).
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing analysis results.
    """
    results = {}
    
    # 1. Calculate observed effect size (f²)
    observed_f2 = calculate_effect_size_from_r2(observed_r2, n_obs, n_predictors)
    results['observed_effect_size_f2'] = observed_f2
    
    # 2. Calculate current power based on observed effect size
    # Using FTestPower for linear regression
    # nobs = sample size
    # effect = f2
    # df_num = n_predictors (degrees of freedom for the model)
    # df_denom = n_obs - n_predictors - 1 (degrees of freedom for error)
    
    df_num = n_predictors
    df_denom = max(1, n_obs - n_predictors - 1)
    
    power_test = FTestPower()
    
    # Calculate power for the observed effect size
    current_power = power_test.power(
        effect_size=observed_f2,
        df_num=df_num,
        df_denom=df_denom,
        alpha=alpha,
        nobs1=n_obs
    )
    results['current_power'] = float(current_power)
    
    # 3. Calculate required N for target R² (0.10) and target power (0.80)
    target_f2 = calculate_effect_size_from_r2(target_r2, 0, 0)
    
    # Solve for nobs
    # We need to find n such that power(n, f2_target) >= target_power
    # We can use the solve_power method
    
    try:
        required_n = power_test.solve_power(
            effect_size=target_f2,
            df_num=df_num,
            df_denom=None, # Let it solve for denominator degrees of freedom
            alpha=alpha,
            power=target_power,
            alternative='larger'
        )
        # solve_power returns total sample size (nobs)
        if required_n is None or np.isnan(required_n) or np.isinf(required_n):
            # If we can't solve it (e.g., effect size is too small for any N to achieve power)
            # or if the required N is unreasonably large
            results['required_n'] = None
            results['required_n_note'] = "Could not calculate required N (effect size too small or calculation failed)"
        else:
            results['required_n'] = int(np.ceil(required_n))
            results['required_n_note'] = f"Calculated for R²={target_r2}, Power={target_power}, Alpha={alpha}"
    except Exception as e:
        results['required_n'] = None
        results['required_n_note'] = f"Calculation failed: {str(e)}"
    
    # Add metadata
    results['target_r2'] = target_r2
    results['target_power'] = target_power
    results['alpha'] = alpha
    results['n_predictors'] = n_predictors
    results['analysis_type'] = "post_hoc"
    
    return results


def save_results(power_results: Dict[str, Any], model_results_path: str) -> bool:
    """
    Appends the power analysis results to the existing model_results.json file.
    
    Args:
        power_results: Dictionary containing the power analysis results.
        model_results_path: Path to the model_results.json file.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure directory exists
        ensure_dirs(model_results_path)
        
        # Load existing results if file exists
        if os.path.exists(model_results_path):
            with open(model_results_path, 'r') as f:
                existing_results = json.load(f)
        else:
            existing_results = {}
        
        # Append power analysis results
        existing_results['post_hoc_power_analysis'] = power_results
        
        # Write back to file
        with open(model_results_path, 'w') as f:
            json.dump(existing_results, f, indent=2)
        
        print(f"Successfully appended power analysis results to {model_results_path}")
        return True
        
    except Exception as e:
        print(f"Error saving results: {e}")
        return False


def main():
    """Main entry point for the post-hoc power analysis task."""
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis for T023")
    parser.add_argument(
        '--target-r2', 
        type=float, 
        default=0.10, 
        help='Target R² for power calculation (default: 0.10)'
    )
    parser.add_argument(
        '--target-power', 
        type=float, 
        default=0.80, 
        help='Target statistical power (default: 0.80)'
    )
    args = parser.parse_args()
    
    print("Starting Post-Hoc Power Analysis (T023)...")
    
    # Load model results
    model_results = load_model_results()
    if not model_results:
        print("ERROR: Could not load model results. Exiting.")
        sys.exit(1)
    
    # Extract necessary parameters
    # We need R², number of observations, and number of predictors
    # The model_results.json structure is expected to have:
    # - test_r2 (or adjusted_r2)
    # - We need to infer n_obs and n_predictors from the data used in modeling
    
    # Since we don't have direct access to the modeling script's internal variables,
    # we need to load the features to count observations and predictors
    try:
        features_path = get_path("processed", "features.csv")
        if not os.path.exists(features_path):
            print(f"ERROR: Features file not found at {features_path}")
            sys.exit(1)
        
        import pandas as pd
        df = pd.read_csv(features_path)
        
        n_obs = len(df)
        # Assume all columns except 'participant_id' and 'median_rt' are features
        feature_cols = [col for col in df.columns if col not in ['participant_id', 'median_rt']]
        n_predictors = len(feature_cols)
        
        if n_predictors == 0:
            print("ERROR: No feature columns found in features.csv")
            sys.exit(1)
            
        print(f"Loaded {n_obs} observations with {n_predictors} predictors.")
        
    except Exception as e:
        print(f"ERROR: Could not load features to determine N and predictors: {e}")
        sys.exit(1)
    
    # Get observed R²
    # Prefer adjusted_r2 if available, otherwise test_r2
    observed_r2 = model_results.get('adjusted_r2') or model_results.get('test_r2')
    if observed_r2 is None:
        print("ERROR: Could not find R² value in model results.")
        sys.exit(1)
    
    print(f"Using observed R²: {observed_r2:.4f}")
    
    # Perform power analysis
    power_analysis_results = perform_power_analysis(
        observed_r2=observed_r2,
        n_obs=n_obs,
        n_predictors=n_predictors,
        target_r2=args.target_r2,
        target_power=args.target_power
    )
    
    print("Power Analysis Results:")
    print(f"  Observed Effect Size (f²): {power_analysis_results['observed_effect_size_f2']:.4f}")
    print(f"  Current Power: {power_analysis_results['current_power']:.4f}")
    if power_analysis_results['required_n']:
        print(f"  Required N for R²={args.target_r2}, Power=0.80: {power_analysis_results['required_n']}")
    else:
        print(f"  Required N: {power_analysis_results['required_n_note']}")
    
    # Save results
    model_results_path = get_path("processed", "model_results.json")
    if save_results(power_analysis_results, model_results_path):
        print("Task T023 completed successfully.")
        sys.exit(0)
    else:
        print("Task T023 failed to save results.")
        sys.exit(1)


if __name__ == "__main__":
    main()
