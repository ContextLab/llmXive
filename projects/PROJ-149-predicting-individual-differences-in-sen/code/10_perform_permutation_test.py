import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import from existing API surface
from config import get_path, get_cv_folds, bonferroni_correct
from utils.stats_helpers import permutation_test

def load_features() -> pd.DataFrame:
    """Load the processed features dataset."""
    features_path = get_path("data/processed/features.csv")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found at {features_path}")
    df = pd.read_csv(features_path)
    return df

def load_split_indices() -> Dict[str, Any]:
    """Load the cross-validation split indices."""
    split_path = get_path("data/interim/split_indices.json")
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split indices not found at {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)

def load_observed_results() -> Dict[str, Any]:
    """Load the observed model results from T019."""
    results_path = get_path("data/processed/model_results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model results not found at {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def prepare_test_data(df: pd.DataFrame, split_indices: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare X and y for the specific fold used in the observed model.
    We assume the observed model was trained on the first fold's training set
    and evaluated on the first fold's test set for consistency, or we aggregate
    across folds if the observed R2 is a mean.
    
    For permutation testing, we typically shuffle y across the WHOLE dataset
    (or the training set) and re-evaluate the model.
    """
    # Identify feature columns (all columns except participant_id and median_rt)
    feature_cols = [c for c in df.columns if c not in ['participant_id', 'median_rt']]
    
    X = df[feature_cols].values
    y = df['median_rt'].values
    
    return X, y, feature_cols

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared score."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def run_permutation_test(
    X: np.ndarray, 
    y: np.ndarray, 
    n_permutations: int = 1000, 
    random_state: int = 42
) -> np.ndarray:
    """
    Run the permutation test to generate the null distribution of R².
    Shuffles y values and recalculates the model performance.
    
    We use a simple linear regression for speed in the permutation loop,
    as the observed model was a Multiple Linear Regression (T017).
    """
    rng = np.random.default_rng(random_state)
    n_samples = len(y)
    null_distribution = np.zeros(n_permutations)
    
    # Pre-allocate arrays for speed
    X_b = np.ones((n_samples, X.shape[1] + 1))
    X_b[:, 1:] = X
    
    # Pseudo-inverse for fast OLS solution: (X'X)^-1 X'y
    # We compute (X'X)^-1 X' once since X is fixed
    try:
        # Using pinv for numerical stability
        # beta = (X'X)^-1 X' y  =>  y_hat = X beta = X (X'X)^-1 X' y
        # Let H = X (X'X)^-1 X' (hat matrix)
        # y_hat = H y
        # R2 = 1 - SS_res / SS_tot = 1 - ||y - Hy||^2 / ||y - y_mean||^2
        
        # Compute H matrix
        XtX_inv = np.linalg.pinv(X_b.T @ X_b)
        H = X_b @ XtX_inv @ X_b.T
        
        # Center y for SS_tot calculation
        y_mean = np.mean(y)
        y_centered = y - y_mean
        ss_tot = np.sum(y_centered ** 2)
        
        for i in range(n_permutations):
            # Shuffle y
            y_perm = rng.permutation(y)
            
            # Calculate predictions using the hat matrix: y_hat = H * y_perm
            y_hat = H @ y_perm
            
            # Calculate R2
            ss_res = np.sum((y_perm - y_hat) ** 2)
            # SS_tot for permuted data is the same as original if we just shuffle
            # But strictly, R2 is calculated against the mean of the permuted y
            # However, since we are shuffling, the mean is the same.
            # To be safe, we calculate it per permutation if we want strict definition,
            # but for null distribution generation, comparing against the observed R2
            # (calculated on original data) usually assumes the same SS_tot denominator
            # or we calculate it on the permuted y.
            # Standard practice: R2 = 1 - SS_res / SS_tot(y_perm)
            # Since we shuffle, mean(y_perm) == mean(y), so SS_tot is constant.
            
            r2 = 1 - (ss_res / ss_tot)
            null_distribution[i] = r2
            
    except np.linalg.LinAlgError:
        # Fallback to loop if matrix inversion fails (rare)
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        for i in range(n_permutations):
            y_perm = rng.permutation(y)
            model.fit(X, y_perm)
            y_hat = model.predict(X)
            r2 = model.score(X, y_perm)
            null_distribution[i] = r2

    return null_distribution

def calculate_permutation_pvalue(
    observed_r2: float, 
    null_distribution: np.ndarray
) -> float:
    """
    Calculate the p-value by comparing observed R2 against the null distribution.
    p = (number of null R2 >= observed R2 + 1) / (n_permutations + 1)
    """
    count_ge = np.sum(null_distribution >= observed_r2)
    p_value = (count_ge + 1) / (len(null_distribution) + 1)
    return p_value

def save_permutation_results(
    p_value: float,
    observed_r2: float,
    null_distribution: np.ndarray,
    output_path: str
):
    """Save permutation test results to the model_results.json file."""
    # Load existing results
    results = load_observed_results()
    
    # Prepare new section
    permutation_results = {
        "permutation_test": {
            "n_permutations": len(null_distribution),
            "observed_r2": float(observed_r2),
            "p_value": float(p_value),
            "null_distribution_mean": float(np.mean(null_distribution)),
            "null_distribution_std": float(np.std(null_distribution)),
            "null_distribution_min": float(np.min(null_distribution)),
            "null_distribution_max": float(np.max(null_distribution)),
            "significant": p_value < 0.05
        }
    }
    
    # Append to results
    results.update(permutation_results)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write back to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Permutation Test Part 2: Calculate Significance")
    parser.add_argument("--n-permutations", type=int, default=1000, help="Number of permutations")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print("Loading features...")
    df = load_features()
    
    print("Loading split indices...")
    split_indices = load_split_indices()
    
    print("Loading observed results...")
    observed_results = load_observed_results()
    observed_r2 = observed_results.get("adjusted_r2", observed_results.get("r2", 0.0))
    
    print(f"Observed R²: {observed_r2:.4f}")

    print("Preparing data...")
    X, y, feature_cols = prepare_test_data(df, split_indices)
    
    print(f"Running permutation test with {args.n_permutations} permutations...")
    null_distribution = run_permutation_test(
        X, y, 
        n_permutations=args.n_permutations, 
        random_state=args.random_state
    )
    
    print("Calculating p-value...")
    p_value = calculate_permutation_pvalue(observed_r2, null_distribution)
    
    print(f"Permutation p-value: {p_value:.4f}")
    
    output_path = get_path("data/processed/model_results.json")
    save_permutation_results(p_value, observed_r2, null_distribution, output_path)
    
    print(f"Results appended to {output_path}")

if __name__ == "__main__":
    main()