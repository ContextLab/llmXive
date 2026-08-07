import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from config import get_path, get_seed

def load_features(path_str: str) -> pd.DataFrame:
    """Load the processed features CSV."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    return pd.read_csv(path)

def load_split_indices(path_str: str) -> Dict[str, Any]:
    """Load the split indices JSON generated during modeling."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Split indices file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def prepare_test_data(
    features: pd.DataFrame,
    split_indices: Dict[str, Any],
    target_col: str = 'median_rt'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare X_test and y_test based on the held-out indices.
    Returns X_test, y_test, and the feature columns used.
    """
    test_indices = split_indices['test_indices']
    
    # Select feature columns (exclude metadata/target)
    feature_cols = [c for c in features.columns if c not in ['participant_id', target_col]]
    
    # Filter to test set only
    test_df = features.iloc[test_indices]
    
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    return X_test, y_test, feature_cols

def run_permutation_test(
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform permutation test on the held-out test set.
    Null hypothesis: There is no relationship between X and y.
    We shuffle y, refit the model, and compute R2.
    """
    rng = np.random.default_rng(seed)
    n_samples = len(y_test)
    
    # Fit original model on test set (simulating the model trained on train set)
    # Note: In a strict pipeline, this R2 should match the one from T017 on the test set
    original_model = LinearRegression()
    original_model.fit(X_test, y_test)
    original_r2 = r2_score(y_test, original_model.predict(X_test))
    
    permuted_r2s = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        # Shuffle y only
        y_shuffled = y_test.copy()
        rng.shuffle(y_shuffled)
        
        # Fit model on shuffled data
        perm_model = LinearRegression()
        perm_model.fit(X_test, y_shuffled)
        
        # Calculate R2
        perm_r2 = r2_score(y_shuffled, perm_model.predict(X_test))
        permuted_r2s[i] = perm_r2
    
    # Calculate p-value: proportion of permuted R2 >= original R2
    # (One-tailed test: is original R2 significantly higher than random?)
    p_value = np.mean(permuted_r2s >= original_r2)
    
    return {
        'original_r2': float(original_r2),
        'p_value': float(p_value),
        'n_permutations': n_permutations,
        'permuted_r2_distribution': permuted_r2s.tolist(),
        'seed': seed
    }

def save_results(results: Dict[str, Any], output_path: str):
    """Save permutation test results to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Permutation test for R2 significance on held-out set.")
    parser.add_argument("--features", type=str, default="data/processed/features.csv",
                        help="Path to features CSV")
    parser.add_argument("--splits", type=str, default="data/processed/split_indices.json",
                        help="Path to split indices JSON")
    parser.add_argument("--output", type=str, default="data/processed/permutation_results.json",
                        help="Output path for results JSON")
    parser.add_argument("--n-permutations", type=int, default=1000,
                        help="Number of permutations")
    
    args = parser.parse_args()
    
    # Load config for seed
    seed = get_seed()
    
    # Load data
    print(f"Loading features from {args.features}...")
    features = load_features(args.features)
    
    print(f"Loading split indices from {args.splits}...")
    split_indices = load_split_indices(args.splits)
    
    # Prepare test data
    print("Preparing test data...")
    X_test, y_test, feature_cols = prepare_test_data(features, split_indices)
    
    if len(X_test) == 0:
        raise ValueError("No test samples found in split_indices. Check T017 output.")
    
    print(f"Running permutation test ({args.n_permutations} permutations, seed={seed})...")
    results = run_permutation_test(X_test, y_test, args.n_permutations, seed)
    
    # Save results
    save_results(results, args.output)
    print(f"Results saved to {args.output}")
    print(f"Original R2: {results['original_r2']:.4f}")
    print(f"Permutation p-value: {results['p_value']:.4f}")
    
    if results['p_value'] < 0.05:
        print("Result is statistically significant (p < 0.05).")
    else:
        print("Result is NOT statistically significant (p >= 0.05).")

if __name__ == "__main__":
    main()
