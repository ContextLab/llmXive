"""
Permutation Test for Model Significance (FR-007)

This script performs a permutation test to assess the statistical significance
of the observed R² score from the predictive model.

Methodology:
1. Load the observed test R² from model_results.json.
2. Load the full dataset (features.csv) and the original train/test split indices.
3. For 10,000 iterations:
   a. Shuffle the target variable (median_rt) on the FULL dataset.
   b. Apply the stored split indices to the shuffled data.
   c. Train the LASSO model on the shuffled training set.
   d. Predict on the shuffled test set.
   e. Compute R².
4. Store the null distribution of R² scores.
5. Calculate the p-value: proportion of null R² >= observed R².
6. Save results to data/processed/permutation_results.json and null distribution to data/interim/permutation_null_distribution.npy.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from config import get_path, ensure_dirs, get_seed

# Constants
N_PERMUTATIONS = 10000
RANDOM_SEED = get_seed()

def load_observed_results():
    """Load observed model results from data/processed/model_results.json."""
    path = get_path('processed', 'model_results.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Observed results file not found: {path}. "
                                "Please run code/05_modeling.py (T017) first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_features_and_targets():
    """
    Load features and targets from data/processed/features.csv.
    Returns X (features), y (median_rt), and the original split indices.
    """
    features_path = get_path('processed', 'features.csv')
    split_indices_path = get_path('interim', 'split_indices.json')

    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}. "
                                "Please run code/04c_relative_power.py (T012c) first.")
    if not os.path.exists(split_indices_path):
        raise FileNotFoundError(f"Split indices file not found: {split_indices_path}. "
                                "Please run code/05_modeling.py (T017) first.")

    df = pd.read_csv(features_path)

    # Ensure required columns exist
    required_cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 
                     'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in features.csv: {missing_cols}")

    # Separate features and target
    feature_cols = ['delta_rel', 'theta_rel', 'alpha_rel', 'low_beta_rel', 
                    'high_beta_rel', 'gamma_rel']
    X = df[feature_cols].values
    y = df['median_rt'].values

    # Load split indices
    with open(split_indices_path, 'r') as f:
        split_data = json.load(f)

    train_idx = np.array(split_data['train_idx'])
    test_idx = np.array(split_data['test_idx'])

    return X, y, train_idx, test_idx, feature_cols

def compute_r2_for_permutation(X, y, train_idx, test_idx, alpha=0.01):
    """
    Train a LASSO model on shuffled data and compute R².
    
    Args:
        X: Full feature matrix (shuffled y is applied via indexing)
        y: Full target vector (will be shuffled by caller before passing)
        train_idx: Indices for training set
        test_idx: Indices for test set
        alpha: Regularization strength for LASSO
        
    Returns:
        R² score on the test set
    """
    # Split data
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Fit LASSO model
    model = Lasso(alpha=alpha, random_state=RANDOM_SEED, max_iter=10000)
    try:
        model.fit(X_train_scaled, y_train)
    except Exception:
        # If fit fails (e.g., convergence), return NaN or a very low score
        # to indicate a failed permutation
        return -np.inf

    # Predict
    y_pred = model.predict(X_test_scaled)

    # Compute R²
    r2 = r2_score(y_test, y_pred)
    return r2

def run_permutation_test(X, y, train_idx, test_idx, n_permutations=N_PERMUTATIONS):
    """
    Run the permutation test.
    
    Args:
        X: Full feature matrix
        y: Full target vector
        train_idx: Training indices
        test_idx: Test indices
        n_permutations: Number of permutations
        
    Returns:
        null_distribution: Array of R² scores from permutations
    """
    print(f"Running permutation test with {n_permutations} iterations...")
    
    # Set random seed for reproducibility
    np.random.seed(RANDOM_SEED)
    
    null_scores = np.zeros(n_permutations)
    
    # Optimize: Pre-scale X to avoid repeated scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    for i in range(n_permutations):
        # Shuffle y
        y_shuffled = y.copy()
        np.random.shuffle(y_shuffled)
        
        # Compute R² on shuffled data
        r2 = compute_r2_for_permutation(X_scaled, y_shuffled, train_idx, test_idx)
        null_scores[i] = r2
        
        if (i + 1) % 1000 == 0:
            print(f"  Completed {i + 1}/{n_permutations} permutations")
            
    return null_scores

def calculate_p_value(observed_r2, null_distribution):
    """
    Calculate the one-sided p-value.
    p = (number of null R² >= observed R² + 1) / (n_permutations + 1)
    """
    count = np.sum(null_distribution >= observed_r2)
    p_value = (count + 1) / (len(null_distribution) + 1)
    return p_value

def save_results(observed_r2, p_value, null_distribution):
    """Save results to data/processed/permutation_results.json and null distribution to data/interim/permutation_null_distribution.npy."""
    
    # Ensure output directories exist
    ensure_dirs('processed')
    ensure_dirs('interim')
    
    # Save null distribution
    null_path = get_path('interim', 'permutation_null_distribution.npy')
    np.save(null_path, null_distribution)
    print(f"Null distribution saved to: {null_path}")
    
    # Save results JSON
    results = {
        'observed_r2': float(observed_r2),
        'p_value': float(p_value),
        'n_permutations': len(null_distribution),
        'null_distribution_mean': float(np.mean(null_distribution)),
        'null_distribution_std': float(np.std(null_distribution)),
        'null_distribution_min': float(np.min(null_distribution)),
        'null_distribution_max': float(np.max(null_distribution)),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01
    }
    
    output_path = get_path('processed', 'permutation_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Permutation results saved to: {output_path}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Run permutation test for model significance.')
    parser.add_argument('--n-permutations', type=int, default=N_PERMUTATIONS, 
                        help=f'Number of permutations (default: {N_PERMUTATIONS})')
    parser.add_argument('--alpha', type=float, default=0.01, 
                        help='LASSO alpha parameter (default: 0.01)')
    args = parser.parse_args()
    
    try:
        # Load observed results
        print("Loading observed model results...")
        observed_results = load_observed_results()
        observed_r2 = observed_results.get('test_r2')
        
        if observed_r2 is None:
            raise ValueError("test_r2 not found in model_results.json")
        
        print(f"Observed test R²: {observed_r2:.4f}")
        
        # Load features and targets
        print("Loading features and split indices...")
        X, y, train_idx, test_idx, feature_cols = load_features_and_targets()
        print(f"Dataset shape: X={X.shape}, y={y.shape}")
        print(f"Train size: {len(train_idx)}, Test size: {len(test_idx)}")
        
        # Run permutation test
        null_distribution = run_permutation_test(X, y, train_idx, test_idx, args.n_permutations)
        
        # Calculate p-value
        p_value = calculate_p_value(observed_r2, null_distribution)
        print(f"Permutation p-value: {p_value:.4f}")
        
        # Save results
        results = save_results(observed_r2, p_value, null_distribution)
        
        # Print summary
        print("\n" + "="*50)
        print("PERMUTATION TEST RESULTS")
        print("="*50)
        print(f"Observed R²:        {observed_r2:.4f}")
        print(f"P-value:            {p_value:.4f}")
        print(f"Significant (α=0.05): {results['significant_at_0.05']}")
        print(f"Null Mean R²:       {results['null_distribution_mean']:.4f}")
        print(f"Null Std R²:        {results['null_distribution_std']:.4f}")
        print("="*50)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR during permutation test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()