import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from config import get_path, set_global_seed

def load_features(features_path: str) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load features and prepare X, y arrays.
    Returns: (df, X, y)
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    df = pd.read_csv(features_path)
    
    # Identify feature columns (exclude 'participant_id' and 'median_rt')
    feature_cols = [col for col in df.columns if col not in ['participant_id', 'median_rt']]
    
    X = df[feature_cols].values
    y = df['median_rt'].values
    
    return df, X, y

def load_split_indices(indices_path: str) -> Dict[int, Dict[str, np.ndarray]]:
    """
    Load pre-computed train/test split indices.
    """
    if not os.path.exists(indices_path):
        raise FileNotFoundError(f"Split indices file not found: {indices_path}")
    
    with open(indices_path, 'r') as f:
        indices = json.load(f)
    
    # Convert string keys to integers and ensure numpy arrays
    return {int(k): v for k, v in indices.items()}

def prepare_test_data(X: np.ndarray, y: np.ndarray, 
                      split_indices: Dict[int, Dict[str, np.ndarray]],
                      fold: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare train/test data for a specific fold.
    """
    train_idx = split_indices[fold]['train']
    test_idx = split_indices[fold]['test']
    
    X_train = X[train_idx]
    y_train = y[train_idx]
    X_test = X[test_idx]
    y_test = y[test_idx]
    
    return X_train, y_train, X_test, y_test

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R² score.
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    
    return 1 - (ss_res / ss_tot)

def run_permutation_test(X: np.ndarray, y: np.ndarray,
                         split_indices: Dict[int, Dict[str, np.ndarray]],
                         n_permutations: int = 1000,
                         random_state: int = 42) -> np.ndarray:
    """
    Run permutation test to generate null distribution of R².
    
    For each permutation:
    1. Shuffle y values
    2. For each fold, train model and compute R²
    3. Average R² across folds
    4. Store in null distribution
    
    Returns:
        null_distribution: numpy array of R² values under null hypothesis
    """
    set_global_seed(random_state)
    
    null_r2s = []
    n_folds = len(split_indices)
    
    print(f"Running permutation test with {n_permutations} permutations...")
    print(f"Number of folds: {n_folds}")
    
    for perm_idx in range(n_permutations):
        # Shuffle y
        y_shuffled = y.copy()
        np.random.shuffle(y_shuffled)
        
        fold_r2s = []
        
        for fold in range(n_folds):
            X_train, y_train, X_test, y_test = prepare_test_data(
                X, y_shuffled, split_indices, fold
            )
            
            # Simple linear regression for each fold
            # X_train: (n_train, n_features), y_train: (n_train,)
            # Fit: y = X * beta
            if X_train.shape[0] > X_train.shape[1]:
                try:
                    beta = np.linalg.lstsq(X_train, y_train, rcond=None)[0]
                    y_pred = X_test @ beta
                    r2 = calculate_r2(y_test, y_pred)
                    fold_r2s.append(r2)
                except np.linalg.LinAlgError:
                    fold_r2s.append(0.0)
            else:
                fold_r2s.append(0.0)
        
        # Average R² across folds for this permutation
        avg_r2 = np.mean(fold_r2s)
        null_r2s.append(avg_r2)
        
        if (perm_idx + 1) % 100 == 0:
            print(f"  Completed {perm_idx + 1}/{n_permutations} permutations")
    
    return np.array(null_r2s)

def calculate_permutation_pvalue(observed_r2: float, 
                                 null_distribution: np.ndarray) -> float:
    """
    Calculate two-sided p-value from permutation test.
    
    For R², we typically care about whether observed is significantly 
    greater than expected under null. Using one-sided test:
    p = (number of null R² >= observed R² + 1) / (n_permutations + 1)
    
    The +1 is for the observed statistic itself (conservative estimate).
    """
    # Count how many null R² values are >= observed
    count_ge = np.sum(null_distribution >= observed_r2)
    n_perm = len(null_distribution)
    
    # Two-sided p-value calculation for R²
    # Since R² is bounded [0, 1] and we're testing if model explains variance,
    # we use the proportion of null R² >= observed
    p_value = (count_ge + 1) / (n_perm + 1)
    
    return p_value

def load_observed_results(results_path: str) -> Dict[str, Any]:
    """
    Load observed model results to get the observed R².
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    return results

def save_permutation_results(results_path: str, 
                             observed_r2: float,
                             p_value: float,
                             null_distribution: np.ndarray,
                             n_permutations: int) -> None:
    """
    Append permutation test results to model_results.json.
    """
    results = load_observed_results(results_path)
    
    # Ensure permutation_results key exists
    if 'permutation_results' not in results:
        results['permutation_results'] = {}
    
    results['permutation_results'].update({
        'observed_r2': float(observed_r2),
        'p_value': float(p_value),
        'n_permutations': n_permutations,
        'null_distribution_mean': float(np.mean(null_distribution)),
        'null_distribution_std': float(np.std(null_distribution)),
        'null_distribution_min': float(np.min(null_distribution)),
        'null_distribution_max': float(np.max(null_distribution)),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01
    })
    
    # Save updated results
    output_dir = os.path.dirname(results_path)
    os.makedirs(output_dir, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Permutation results saved to: {results_path}")

def main():
    parser = argparse.ArgumentParser(description='Permutation Test Part 2: Calculate Significance')
    parser.add_argument('--features', type=str, default=None,
                      help='Path to features CSV')
    parser.add_argument('--split-indices', type=str, default=None,
                      help='Path to split indices JSON')
    parser.add_argument('--results', type=str, default=None,
                      help='Path to model results JSON')
    parser.add_argument('--null-distribution', type=str, default=None,
                      help='Path to null distribution numpy file')
    parser.add_argument('--n-permutations', type=int, default=1000,
                      help='Number of permutations (default: 1000)')
    parser.add_argument('--random-state', type=int, default=42,
                      help='Random state for reproducibility')
    
    args = parser.parse_args()
    
    # Set paths from config if not provided
    if args.features is None:
        args.features = get_path('data/processed/features.csv')
    if args.split_indices is None:
        args.split_indices = get_path('data/interim/split_indices.json')
    if args.results is None:
        args.results = get_path('data/processed/model_results.json')
    if args.null_distribution is None:
        args.null_distribution = get_path('data/interim/permutation_null_distribution.npy')
    
    print("Loading data...")
    
    # Load features
    df, X, y = load_features(args.features)
    print(f"  Loaded {len(df)} samples with {X.shape[1]} features")
    
    # Load split indices
    split_indices = load_split_indices(args.split_indices)
    print(f"  Loaded {len(split_indices)} fold splits")
    
    # Load null distribution
    if os.path.exists(args.null_distribution):
        null_distribution = np.load(args.null_distribution)
        print(f"  Loaded null distribution with {len(null_distribution)} samples")
    else:
        print(f"  Null distribution not found at {args.null_distribution}")
        print("  Generating null distribution...")
        null_distribution = run_permutation_test(
            X, y, split_indices, 
            n_permutations=args.n_permutations,
            random_state=args.random_state
        )
        # Save null distribution
        os.makedirs(os.path.dirname(args.null_distribution), exist_ok=True)
        np.save(args.null_distribution, null_distribution)
        print(f"  Saved null distribution to {args.null_distribution}")
    
    # Load observed results to get observed R²
    observed_results = load_observed_results(args.results)
    
    # Extract observed R² from model results
    # The observed R² should be in the main results
    if 'adjusted_r2' in observed_results:
        observed_r2 = observed_results['adjusted_r2']
    elif 'r2' in observed_results:
        observed_r2 = observed_results['r2']
    elif 'model_results' in observed_results and 'r2' in observed_results['model_results']:
        observed_r2 = observed_results['model_results']['r2']
    else:
        raise ValueError("Could not find observed R² in model results")
    
    print(f"  Observed R²: {observed_r2:.4f}")
    
    # Calculate p-value
    p_value = calculate_permutation_pvalue(observed_r2, null_distribution)
    print(f"  Permutation p-value: {p_value:.4f}")
    
    # Save results
    save_permutation_results(
        args.results, 
        observed_r2, 
        p_value, 
        null_distribution, 
        args.n_permutations
    )
    
    print("\nPermutation test completed successfully!")
    print(f"  Observed R²: {observed_r2:.4f}")
    print(f"  Null distribution mean: {np.mean(null_distribution):.4f}")
    print(f"  Null distribution std: {np.std(null_distribution):.4f}")
    print(f"  P-value: {p_value:.4f}")
    print(f"  Significant at 0.05: {p_value < 0.05}")
    print(f"  Significant at 0.01: {p_value < 0.01}")

if __name__ == '__main__':
    main()