import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr
from scipy.stats import zscore
import xgboost as xgb

# Import shared config
import config

# --- Helper Functions for Permutation Importance & Convergence (T026) ---

def load_model_and_data() -> Tuple[Any, pd.DataFrame, pd.DataFrame, np.ndarray]:
    """
    Loads the trained model, features, and target from the processed data.
    Assumes T023 has run and produced the necessary artifacts.
    """
    model_path = config.PROJECT_ROOT / "data" / "models" / "model.json"
    features_path = config.PROJECT_ROOT / "data" / "processed" / "filtered_features.csv"
    target_path = config.PROJECT_ROOT / "data" / "processed" / "filtered_features.csv" # Target is in the same file usually

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run T023 first.")
    
    # Load model
    model = xgb.XGBClassifier()
    model.load_model(str(model_path))

    # Load data
    df = pd.read_csv(features_path)
    
    # Identify target column based on standard naming or config
    # Assuming 'bleaching_label' is the target based on context
    if 'bleaching_label' not in df.columns:
        raise ValueError("Target column 'bleaching_label' not found in filtered_features.csv")
    
    X = df.drop(columns=['bleaching_label'])
    y = df['bleaching_label']

    return model, X, y, df

def run_permutation_importance(model: Any, X: pd.DataFrame, y: np.ndarray, n_repeats: int = 10, random_state: int = 42) -> pd.DataFrame:
    """
    Runs permutation importance and returns a DataFrame of scores.
    """
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1, 
        scoring='roc_auc'
    )
    
    df_importance = pd.DataFrame({
        'feature': X.columns,
        'mean_importance': result.importances_mean,
        'std_importance': result.importances_std
    })
    return df_importance.sort_values(by='mean_importance', ascending=False)

def compute_ranking_correlation(rankings: List[pd.DataFrame]) -> float:
    """
    Computes the Spearman correlation between the rankings of two consecutive batches.
    Returns the mean correlation of top-K features if K is specified, or all.
    """
    if len(rankings) < 2:
        return 0.0
    
    # Flatten rankings to just the feature order (or mean importance)
    # We compare the mean_importance columns
    last_rank = rankings[-1]['mean_importance'].values
    prev_rank = rankings[-2]['mean_importance'].values
    
    corr, _ = spearmanr(last_rank, prev_rank)
    return corr if not np.isnan(corr) else 0.0

def run_convergence_loop(model: Any, X: pd.DataFrame, y: np.ndarray, 
                         batch_size: int = 200, max_runs: int = 2000, 
                         tolerance: float = 0.01, patience: int = 2) -> Tuple[int, pd.DataFrame]:
    """
    Runs permutation importance in batches until the ranking stabilizes.
    Returns the final N (total runs) and the final ranking.
    """
    current_n = 0
    rankings = []
    stable_count = 0
    final_ranking = None

    print("Starting convergence loop for permutation importance...")

    while current_n < max_runs:
        # Calculate how many more repeats we need for this batch
        # We simulate 'n_repeats' by running the permutation function multiple times
        # Note: sklearn's permutation_importance with n_repeats=k does k shuffles.
        # To simulate convergence, we run the whole process multiple times with increasing total repeats?
        # Actually, the task implies running the permutation importance with a growing 'n_repeats' parameter
        # or running the whole experiment multiple times.
        # Interpretation: We run permutation importance with n_repeats = batch_size, then 2*batch_size, etc.
        
        next_n = min(current_n + batch_size, max_runs)
        
        # Run permutation importance with current total repeats
        # Note: sklearn's n_repeats is the number of shuffles per feature.
        # We interpret "convergence" as the stability of the ranking as we increase the number of shuffles (n_repeats).
        
        current_ranking = run_permutation_importance(model, X, y, n_repeats=next_n, random_state=42)
        rankings.append(current_ranking)
        
        if len(rankings) >= 2:
            corr = compute_ranking_correlation(rankings)
            if abs(corr) > 1 - tolerance: # High correlation means stable
                stable_count += 1
                if stable_count >= patience:
                    print(f"Convergence reached at N={next_n} (Correlation: {corr:.4f})")
                    return next_n, current_ranking
            else:
                stable_count = 0
        
        current_n = next_n
        print(f"Current N={current_n}, Correlation={compute_ranking_correlation(rankings) if len(rankings)>=2 else 0:.4f}")

    warnings.warn("Convergence loop hit max runs without stabilizing.")
    return max_runs, rankings[-1]

def calculate_p_values(importance_df: pd.DataFrame, n_permutations: int) -> pd.DataFrame:
    """
    Calculates empirical p-values for feature importance.
    Assumes null distribution is centered at 0.
    """
    # Simple empirical p-value: proportion of permuted importances <= 0 (for positive importance)
    # Or more robustly, compare observed to a distribution of nulls.
    # Since we only have the mean/std from sklearn, we approximate a Z-score assuming normality of the permutation distribution.
    # Z = (mean - 0) / std
    
    z_scores = importance_df['mean_importance'] / (importance_df['std_importance'] + 1e-8)
    
    # One-tailed p-value (probability of observing this or more extreme under null)
    # Using survival function for positive importance
    from scipy.stats import norm
    p_values = norm.sf(z_scores)
    
    importance_df['p_value'] = p_values
    return importance_df

def apply_fdr_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies Benjamini-Hochberg correction to p-values.
    """
    p_values = df['p_value'].values
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    corrected_p = np.zeros(n)
    for i in range(n):
        corrected_p[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
    
    # Ensure values are <= 1
    corrected_p = np.minimum(corrected_p, 1.0)
    
    df['p_value_corrected'] = corrected_p
    return df

# --- T028: Bootstrap Stability Analysis ---

def run_bootstrap_stability(model: Any, X: pd.DataFrame, y: np.ndarray, 
                            n_bootstraps: int = 100, random_state: int = 42) -> Dict[str, Any]:
    """
    Performs Bootstrap Stability analysis (100 resamples) to measure ranking stability 
    of the top-3 predictors.
    
    Returns a dictionary with:
    - 'top_3_features': list of feature names
    - 'stability_scores': dict mapping feature name to frequency of being in top-3
    - 'ranking_variance': variance in the ranking positions
    """
    np.random.seed(random_state)
    n_samples = len(y)
    feature_names = X.columns.tolist()
    top_k = 3
    top_3_counts = {f: 0 for f in feature_names}
    all_rankings = []

    print(f"Starting Bootstrap Stability Analysis ({n_bootstraps} resamples)...")

    for i in range(n_bootstraps):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_boot = X.iloc[indices]
        y_boot = y.iloc[indices]
        
        # Train a quick model on bootstrap sample to get ranking
        # Re-train XGB on bootstrap data
        boot_model = xgb.XGBClassifier(random_state=random_state)
        boot_model.fit(X_boot, y_boot)
        
        # Get permutation importance for this bootstrap sample
        # Use a smaller n_repeats for speed during bootstrap, e.g., 50
        importance_df = run_permutation_importance(boot_model, X_boot, y_boot, n_repeats=50, random_state=random_state + i)
        
        # Extract top K features
        top_k_features = importance_df.head(top_k)['feature'].tolist()
        all_rankings.append(importance_df['feature'].tolist())
        
        # Update counts
        for f in top_k_features:
            top_3_counts[f] += 1

    # Calculate stability scores (frequency of being in top 3)
    stability_scores = {f: count / n_bootstraps for f, count in top_3_counts.items()}
    
    # Determine the "base" top 3 from the full model (or average)
    # For this task, we report the stability of the features that appear most often in top 3
    sorted_stability = sorted(stability_scores.items(), key=lambda x: x[1], reverse=True)
    most_stable_features = [f[0] for f in sorted_stability[:top_k]]
    
    # Calculate variance in rankings (Spearman correlation stability or position variance)
    # Let's compute the standard deviation of the rank position for each feature
    rank_positions = {f: [] for f in feature_names}
    for ranking in all_rankings:
        for idx, f in enumerate(ranking):
            rank_positions[f].append(idx + 1)
    
    rank_variance = {f: np.var(positions) for f, positions in rank_positions.items()}

    return {
        'n_bootstraps': n_bootstraps,
        'top_3_features': most_stable_features,
        'stability_scores': stability_scores,
        'rank_variance': rank_variance,
        'all_rankings': all_rankings # Optional, might be large
    }

def evaluate_model() -> Dict[str, Any]:
    """
    Main evaluation function that orchestrates T026 (Convergence) and T028 (Bootstrap).
    """
    print("Loading model and data...")
    model, X, y, df = load_model_and_data()

    # 1. Run Convergence Loop (T026)
    print("Running Convergence Loop...")
    final_n, final_ranking = run_convergence_loop(model, X, y)
    
    # 2. Calculate P-values and FDR (T026)
    final_ranking = calculate_p_values(final_ranking)
    final_ranking = apply_fdr_correction(final_ranking)
    
    # Save permutation results
    results_path = config.PROJECT_ROOT / "data" / "processed" / "permutation_results.json"
    # Convert dataframe to serializable dict
    permutation_data = final_ranking.to_dict(orient='records')
    
    # 3. Run Bootstrap Stability (T028)
    print("Running Bootstrap Stability Analysis...")
    bootstrap_results = run_bootstrap_stability(model, X, y, n_bootstraps=100)
    
    # Merge results
    output = {
        'convergence': {
            'final_n_repeats': final_n,
            'top_features': final_ranking.head(10)['feature'].tolist(),
            'p_values': final_ranking[['feature', 'p_value', 'p_value_corrected']].to_dict(orient='records')
        },
        'bootstrap_stability': {
            'n_bootstraps': bootstrap_results['n_bootstraps'],
            'top_3_features': bootstrap_results['top_3_features'],
            'stability_scores': bootstrap_results['stability_scores'],
            'rank_variance': bootstrap_results['rank_variance']
        }
    }

    with open(results_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Evaluation complete. Results saved to {results_path}")
    return output

def compute_metrics() -> Dict[str, Any]:
    """
    Placeholder for metric computation if needed separately.
    """
    return {}

def main():
    """
    Entry point for the evaluation script.
    """
    try:
        results = evaluate_model()
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Evaluation failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
