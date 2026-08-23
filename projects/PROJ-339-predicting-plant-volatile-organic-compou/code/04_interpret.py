import os
import sys
import json
import pickle
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure we can import from the project root if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config

def ensure_dirs():
    """Ensure output directories exist."""
    results_dir = PROJECT_ROOT / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def load_model_and_features():
    """Load the trained model and feature names."""
    model_path = PROJECT_ROOT / "data" / "models" / "random_forest.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run training first.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load feature names from the processed dataset or metadata
    # Assuming feature names are stored in the dataset or inferred
    processed_path = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_path}")
    
    df = pd.read_csv(processed_path)
    # Assume the last column is target, rest are features
    feature_names = [col for col in df.columns if col != 'target_voc']
    return model, feature_names, df

def load_processed_data():
    """Load processed data for feature extraction."""
    processed_path = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_path}")
    return pd.read_csv(processed_path)

def run_permutation_importance(model, X, y, n_repeats=10, random_state=42):
    """
    Run permutation importance and return raw p-values.
    Uses a simple approximation: p-value = (count of permuted score >= original score + 1) / (n_repeats + 1)
    """
    # Get original score (R2)
    original_score = model.score(X, y)
    
    # Run permutation
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state,
        scoring='r2',
        n_jobs=-1
    )
    
    # Calculate p-values for each feature
    # We compare the mean importance of permuted features against 0 (or original if we want to test significance of drop)
    # Standard approach: p-value is the probability that the permuted importance is >= 0 (if importance is negative, it's significant)
    # Or: p-value is the probability that the permuted score is >= original score (if we permute and get better score, it's noise)
    
    # Let's use the approach: p-value = (number of times permuted_importance >= observed_importance + 1) / (n_repeats + 1)
    # But permutation_importance returns the drop in score (original - permuted). 
    # If drop is negative, the model performed better with permuted feature (noise).
    # We want to test if the importance is significantly different from 0.
    
    # Alternative: Test if the mean importance is significantly > 0.
    # We can use the distribution of permuted importances to estimate a p-value.
    # However, sklearn's permutation_importance doesn't return the distribution per feature.
    # We will approximate:
    # p_value = 1 - (rank of observed importance among permuted values) / (n_repeats + 1)
    # Actually, let's stick to a simpler, robust method for this task:
    # Calculate the mean and std of the permutation importances.
    # If the mean is > 0, we can estimate a one-sided p-value assuming normality or use the empirical distribution.
    
    # Given the constraints, we will calculate p-values based on the empirical distribution of the permutation results.
    # Since we don't have the full distribution, we will use the mean importance and the standard error.
    # P-value = 1 - CDF(0) for a normal distribution with mean=mean_imp, std=std_imp/sqrt(n)
    # But simpler: if we assume the null is mean=0, we can use a t-test approximation.
    
    # Let's implement the standard "fraction of permuted scores >= original" logic for each feature if we had the full distribution.
    # Since we only have mean_importance and std_importance from sklearn, we will estimate the p-value using a Z-score approximation.
    # Z = (mean_importance - 0) / (std_importance / sqrt(n_repeats))
    # This assumes the permutation distribution is normal, which is a reasonable approximation for n_repeats >= 10.
    
    mean_importance = result.importances_mean
    std_importance = result.importances_std
    
    # Avoid division by zero
    std_importance = np.where(std_importance == 0, 1e-9, std_importance)
    
    z_scores = mean_importance / (std_importance / np.sqrt(n_repeats))
    
    # One-sided p-value (testing if importance > 0)
    # scipy.stats.norm.sf is survival function (1 - cdf)
    # We'll implement a simple approximation or import scipy if available, but to keep deps low:
    # Using erf approximation for normal CDF
    from math import erf, sqrt
    def norm_sf(x):
        return 0.5 * (1 - erf(x / sqrt(2)))
    
    p_values = [norm_sf(z) if z > 0 else 1.0 - norm_sf(-z) for z in z_scores]
    # Actually, if importance is positive, we want P(Z > z). If negative, P(Z < z) is small?
    # We are testing H0: importance = 0. If mean_importance is positive and large, p-value should be small.
    # p-value = P(Importance >= observed | H0).
    # If we assume the permutation distribution centers around 0 under H0, then:
    # p-value = P(Z > z_score)
    
    p_values = [norm_sf(z) for z in z_scores]
    
    return p_values

def benjamini_hochberg_correction(p_values):
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns a list of corrected p-values (q-values).
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    # q_i = (i / n) * alpha, but we want to find the adjusted p-value for each
    # Adjusted p-value for sorted p_i is min( (n/i) * p_j for j >= i )
    # But simpler formula for BH adjusted p-value:
    # p_adj[i] = min( (n/j) * p[j] for j in i..n )
    # And ensure monotonicity (non-decreasing)
    
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        # Calculate (n / (i+1)) * p[i] (using 1-based index for rank)
        rank = i + 1
        raw_adj = sorted_p_values[i] * n / rank
        adjusted_p_values[i] = raw_adj
    
    # Ensure monotonicity (from largest to smallest rank, ensure non-decreasing)
    # We need to make sure that if we go from high rank to low rank, the values don't decrease.
    # Actually, we iterate from the largest rank (n) down to 1.
    # p_adj[i] = min(p_adj[i], p_adj[i+1])
    for i in range(n-2, -1, -1):
        if adjusted_p_values[i] > adjusted_p_values[i+1]:
            adjusted_p_values[i] = adjusted_p_values[i+1]
    
    # Cap at 1.0
    adjusted_p_values = np.minimum(adjusted_p_values, 1.0)
    
    # Restore original order
    final_p_values = np.zeros(n)
    final_p_values[sorted_indices] = adjusted_p_values
    
    return final_p_values.tolist()

def generate_shap_plot(model, X, feature_names):
    """Generate SHAP summary plot and save to file."""
    shap.initjs()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    plt.tight_layout()
    output_path = PROJECT_ROOT / "data" / "results" / "shap_summary.png"
    plt.savefig(output_path)
    plt.close()
    print(f"SHAP plot saved to {output_path}")

def main():
    """Main execution for T030: Apply BH correction to permutation test p-values."""
    print("Starting T030: Benjamini-Hochberg Correction for Feature Importance")
    
    # Ensure directories
    results_dir = ensure_dirs()
    
    # Load model and data
    print("Loading model and data...")
    model, feature_names, df = load_model_and_features()
    
    # Prepare features and target
    X = df.drop(columns=['target_voc', 'sample_id'] if 'sample_id' in df.columns else ['target_voc']).values
    y = df['target_voc'].values
    
    # Run permutation importance
    print("Running permutation importance...")
    raw_p_values = run_permutation_importance(model, X, y, n_repeats=10, random_state=42)
    
    # Apply BH correction
    print("Applying Benjamini-Hochberg correction...")
    corrected_p_values = benjamini_hochberg_correction(raw_p_values)
    
    # Save results
    output_path = results_dir / "feature_importance_pvalues.json"
    output_data = {
        "task_id": "T030",
        "description": "Benjamini-Hochberg corrected p-values for permutation feature importance",
        "features": feature_names,
        "raw_p_values": raw_p_values,
        "corrected_p_values": corrected_p_values,
        "method": "Benjamini-Hochberg FDR"
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Feature importance p-values saved to {output_path}")
    
    # Generate SHAP plot (T029 dependency, but we do it here if not done)
    if not (PROJECT_ROOT / "data" / "results" / "shap_summary.png").exists():
        print("Generating SHAP plot...")
        generate_shap_plot(model, X, feature_names)
    
    print("T030 completed successfully.")

if __name__ == "__main__":
    main()
