"""
Permutation Test for Model Significance (T022)

Implements FR-007: Permutation test to establish null distribution for model R².
Reads observed test_r2 from data/processed/model_results.json.
Shuffles median_rt to generate null distribution.
Outputs data/processed/permutation_results.json and data/interim/permutation_null_distribution.npy.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_path, get_seed, set_global_seed
from utils.stats_helpers import permutation_test

# Constants
N_PERMUTATIONS = 1000  # Number of permutations for null distribution
RANDOM_SEED = 42

def load_observed_results(results_path: str) -> Dict[str, Any]:
    """Load observed model results from JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Observed results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    if 'test_r2' not in results:
        raise KeyError("Observed results missing 'test_r2' key")
    
    return results

def load_features_and_targets(features_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """Load features and median_rt from the CLR-transformed features file."""
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    df = pd.read_csv(features_path)
    
    required_cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 
                    'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Features file missing required columns: {missing_cols}")
    
    # Drop rows with missing values in key columns
    df = df.dropna(subset=required_cols)
    
    features = df[required_cols[2:]]  # All band power columns
    targets = df['median_rt']
    
    return features, targets

def compute_r2_for_permutation(X: np.ndarray, y: np.ndarray, 
                              observed_r2: float) -> float:
    """
    Compute R² for a permuted dataset.
    
    We use a simple closed-form R² calculation to avoid refitting the full model.
    R² = 1 - (SS_res / SS_tot)
    
    For a linear model with permuted y, we can compute R² directly.
    """
    n = len(y)
    if n == 0:
        return 0.0
    
    # Mean of y
    y_mean = np.mean(y)
    
    # Total sum of squares
    ss_tot = np.sum((y - y_mean) ** 2)
    if ss_tot == 0:
        return 0.0
    
    # For a permuted dataset, we expect R² to be near 0
    # We'll use a simple linear regression to compute the actual R²
    # This is more accurate than assuming R² = 0
    
    # Add intercept term
    X_with_intercept = np.column_stack([np.ones(n), X])
    
    # Ordinary least squares: beta = (X'X)^-1 X'y
    try:
        # Use pseudo-inverse for numerical stability
        beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
        
        # Predictions
        y_pred = X_with_intercept @ beta
        
        # Residual sum of squares
        ss_res = np.sum((y - y_pred) ** 2)
        
        # R²
        r2 = 1 - (ss_res / ss_tot)
        
        return r2
    except np.linalg.LinAlgError:
        # If matrix is singular, return 0
        return 0.0

def run_permutation_test(X: np.ndarray, y: pd.Series, 
                        observed_r2: float, 
                        n_permutations: int = 1000,
                        random_state: int = 42) -> np.ndarray:
    """
    Run permutation test to generate null distribution of R² values.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        observed_r2: Observed R² value from the original model
        n_permutations: Number of permutations to run
        random_state: Random seed for reproducibility
    
    Returns:
        Array of R² values from permuted datasets (null distribution)
    """
    set_global_seed(random_state)
    rng = np.random.default_rng(random_state)
    
    null_r2_values = []
    
    for i in range(n_permutations):
        # Shuffle y
        y_permuted = y.sample(frac=1, random_state=rng.integers(0, 2**31)).values
        
        # Compute R² for permuted data
        r2_permuted = compute_r2_for_permutation(X, y_permuted, observed_r2)
        null_r2_values.append(r2_permuted)
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Permutation {i + 1}/{n_permutations} completed")
    
    return np.array(null_r2_values)

def calculate_p_value(observed_r2: float, null_distribution: np.ndarray) -> float:
    """
    Calculate two-sided p-value from null distribution.
    
    For permutation tests, p-value = proportion of null values >= observed value.
    """
    n_permutations = len(null_distribution)
    n_extreme = np.sum(null_distribution >= observed_r2)
    p_value = (n_extreme + 1) / (n_permutations + 1)  # Add 1 for observed value
    return p_value

def save_results(observed_r2: float, p_value: float, 
                null_distribution: np.ndarray,
                output_json_path: str,
                output_npy_path: str) -> Dict[str, Any]:
    """Save permutation test results to JSON and null distribution to NPY."""
    # Ensure output directories exist
    output_json_dir = Path(output_json_path).parent
    output_npy_dir = Path(output_npy_path).parent
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_npy_dir.mkdir(parents=True, exist_ok=True)
    
    # Save null distribution
    np.save(output_npy_path, null_distribution)
    
    # Prepare results
    results = {
        'observed_r2': float(observed_r2),
        'p_value': float(p_value),
        'n_permutations': len(null_distribution),
        'null_distribution_mean': float(np.mean(null_distribution)),
        'null_distribution_std': float(np.std(null_distribution)),
        'null_distribution_min': float(np.min(null_distribution)),
        'null_distribution_max': float(np.max(null_distribution)),
        'null_distribution_path': str(output_npy_path),
        'significant_at_0p05': p_value < 0.05,
        'interpretation': (
            "Model is statistically significant" if p_value < 0.05 
            else "Model is not statistically significant"
        )
    }
    
    # Save results to JSON
    with open(output_json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """Main entry point for permutation test."""
    parser = argparse.ArgumentParser(
        description='Run permutation test for model significance (T022)'
    )
    parser.add_argument(
        '--n-permutations',
        type=int,
        default=N_PERMUTATIONS,
        help=f'Number of permutations (default: {N_PERMUTATIONS})'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=RANDOM_SEED,
        help=f'Random seed (default: {RANDOM_SEED})'
    )
    args = parser.parse_args()
    
    print("Starting Permutation Test (T022)...")
    print(f"  N permutations: {args.n_permutations}")
    print(f"  Random seed: {args.seed}")
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Define paths
    features_path = get_path('processed', 'features_clr.csv')
    observed_results_path = get_path('processed', 'model_results.json')
    output_json_path = get_path('processed', 'permutation_results.json')
    output_npy_path = get_path('interim', 'permutation_null_distribution.npy')
    
    # Load observed results
    print("\nLoading observed model results...")
    observed_results = load_observed_results(observed_results_path)
    observed_r2 = observed_results['test_r2']
    print(f"  Observed test R²: {observed_r2:.4f}")
    
    # Load features and targets
    print("\nLoading features and targets...")
    try:
        X, y = load_features_and_targets(features_path)
        print(f"  Loaded {len(X)} samples with {X.shape[1]} features")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure T012b (CLR transform) and T017 (modeling) have completed successfully.")
        sys.exit(1)
    
    # Run permutation test
    print(f"\nRunning permutation test ({args.n_permutations} permutations)...")
    null_distribution = run_permutation_test(
        X.values, 
        y, 
        observed_r2, 
        n_permutations=args.n_permutations,
        random_state=args.seed
    )
    
    # Calculate p-value
    p_value = calculate_p_value(observed_r2, null_distribution)
    print(f"\nPermutation test completed:")
    print(f"  Null distribution mean: {np.mean(null_distribution):.4f}")
    print(f"  Null distribution std: {np.std(null_distribution):.4f}")
    print(f"  Observed R²: {observed_r2:.4f}")
    print(f"  P-value: {p_value:.4f}")
    print(f"  Significant at α=0.05: {p_value < 0.05}")
    
    # Save results
    print("\nSaving results...")
    results = save_results(
        observed_r2,
        p_value,
        null_distribution,
        output_json_path,
        output_npy_path
    )
    
    print(f"\nOutputs written:")
    print(f"  {output_json_path}")
    print(f"  {output_npy_path}")
    
    print("\nPermutation test completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
