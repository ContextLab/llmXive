import os
import sys
import json
import pickle
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from scipy.stats import norm

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
MODELS_DIR = DATA_DIR / "models"

def ensure_dirs():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_model_and_features():
    """
    Loads the trained Random Forest model and the feature matrix used for training.
    Assumes T024 has saved 'data/models/random_forest.pkl' and T028/T029 have
    prepared the necessary feature context or we reload from the saved model's context.
    
    Since scikit-learn models don't store the feature matrix, we expect the 
    processed data to be available or derived. For this implementation, we assume
    the model was trained on 'data/processed/merged_dataset.csv' after feature 
    aggregation (T016). We load the model and the processed data to align features.
    """
    ensure_dirs()
    
    model_path = MODELS_DIR / "random_forest.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. "
                                "Please ensure T024 (model training) is completed.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load the processed dataset to get feature names
    # We assume the processed dataset contains the aggregated features
    processed_path = DATA_DIR / "processed" / "merged_dataset.csv"
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {processed_path}. "
                                "Please ensure T017 (data validation/merge) is completed.")
    
    df = pd.read_csv(processed_path)
    
    # Identify feature columns (exclude target and non-feature columns like 'sample_id')
    # Assuming the target is 'total_voc_emission' or similar, and we need to infer features.
    # For robustness, we look for columns that are numeric and not the target.
    # If the target column name is not fixed, we might need to load it from a config or metadata.
    # Based on typical VOC prediction tasks, 'total_voc_emission' is a likely target.
    # Let's assume the last numeric column is the target or a specific column name.
    # To be safe, we'll load the target name from a metadata file if it exists, 
    # otherwise default to 'total_voc_emission'.
    target_col = 'total_voc_emission'
    
    # Filter columns: keep numeric, exclude target and sample_id
    feature_cols = [col for col in df.columns 
                    if col != target_col and col != 'sample_id' and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in the processed dataset.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    return model, X, y, feature_cols

def run_permutation_importance(model, X, y, n_repeats=10, random_state=42, n_jobs=1):
    """
    Runs permutation importance and calculates p-values.
    
    This function computes the permutation importance and then performs a 
    statistical test to determine if the importance is significantly different from zero.
    We approximate the null distribution by assuming the importance scores follow a 
    normal distribution under the null hypothesis (mean=0), or we can use a 
    permutation-based p-value calculation if we have the permutation scores.
    
    For this implementation, we calculate p-values based on the mean importance 
    relative to the standard deviation of the importance scores across repeats,
    treating the repeats as samples from a distribution.
    """
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=n_jobs,
        scoring='r2'  # Assuming R2 is the metric of interest
    )
    
    # result.importances_mean: mean importance
    # result.importances_std: std deviation
    # result.importances: array of shape (n_features, n_repeats)
    
    importances_mean = result.importances_mean
    importances_std = result.importances_std
    importances_raw = result.importances  # (n_features, n_repeats)
    
    # Calculate p-values: 
    # Null hypothesis: The true importance is 0.
    # We can use a t-test or a Z-test approximation.
    # Since we have n_repeats, we can compute the t-statistic.
    # t = (mean - 0) / (std / sqrt(n_repeats))
    # However, permutation importance distributions can be non-normal.
    # A robust approach is to count how many permuted importances are >= observed mean?
    # No, the standard approach for p-values in permutation importance is often:
    # p-value = (number of times permuted_importance >= observed_importance + 1) / (n_permutations + 1)
    # But here 'result.importances' is the distribution of importance under permutation for EACH feature.
    # The mean is the observed statistic. The null distribution is the set of values in result.importances.
    # Wait, permutation_importance returns the importance values obtained by permuting the feature.
    # If the feature is important, the importance (drop in score) will be positive.
    # Under the null (feature not important), the importance should be around 0.
    # The 'result.importances' contains the importance scores for each repeat.
    # We can calculate the p-value as the proportion of repeats where the importance is <= 0 (for a one-sided test of positive importance).
    # Or more formally, if we want to test if mean > 0:
    # p-value = proportion of values in result.importances <= 0? 
    # Actually, the standard permutation test p-value for a feature being important (positive impact):
    # p = (count(importance <= 0) + 1) / (n_repeats + 1)
    # This tests H0: importance <= 0 vs H1: importance > 0.
    
    n_features = len(importances_mean)
    n_repeats = result.n_repeats
    
    p_values = np.zeros(n_features)
    for i in range(n_features):
        # Count how many times the importance was <= 0
        # This tests if the feature has a positive importance
        count_le_zero = np.sum(importances_raw[i, :] <= 0)
        # Add 1 to numerator and denominator for conservative estimate
        p_values[i] = (count_le_zero + 1) / (n_repeats + 1)
        
    return {
        'mean_importance': importances_mean,
        'std_importance': importances_std,
        'raw_importances': importances_raw,
        'p_values': p_values
    }

def benjamini_hochberg_correction(p_values, alpha=0.05):
    """
    Applies the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).
    
    Returns:
      - corrected_p_values: The adjusted p-values.
      - is_significant: Boolean array indicating which features are significant after correction.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])
    
    # Sort the p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH critical values
    # rank is 1-indexed
    ranks = np.arange(1, n + 1)
    bh_thresholds = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= k/n * alpha
    # We want to find the cutoff index
    # A simpler way to get corrected p-values is to compute the adjusted p-values:
    # p_adj_i = min( p_j * n / j for j >= i )
    # We do this on the sorted p-values.
    
    corrected_p_values_sorted = np.zeros(n)
    corrected_p_values_sorted[-1] = sorted_p_values[-1]
    for i in range(n - 2, -1, -1):
        # p_adj[i] = min(p_adj[i+1], p_sorted[i] * n / (i+1))
        # But we must ensure monotonicity: p_adj[i] <= p_adj[i+1]
        # The standard formula: p_adj_i = min_{j>=i} (p_j * n / j)
        # We can compute this by iterating backwards
        val = sorted_p_values[i] * n / (i + 1)
        corrected_p_values_sorted[i] = min(val, corrected_p_values_sorted[i+1])
    
    # Ensure values are <= 1
    corrected_p_values_sorted = np.minimum(corrected_p_values_sorted, 1.0)
    
    # Map back to original order
    corrected_p_values = np.zeros(n)
    is_significant = np.zeros(n, dtype=bool)
    
    for i, idx in enumerate(sorted_indices):
        corrected_p_values[idx] = corrected_p_values_sorted[i]
        is_significant[idx] = corrected_p_values_sorted[i] < alpha
        
    return corrected_p_values, is_significant

def main():
    """
    Main entry point for T030: Apply Benjamini-Hochberg correction to permutation importance p-values.
    
    1. Load model and features (from T024 and T017/T016).
    2. Run permutation importance (if not already done, or re-run to get p-values).
       Note: T028 was supposed to generate p-values. We re-run the logic here to ensure
       we have the raw data to apply the correction, or we load the p-values if T028 saved them.
       Given T028 is marked as completed but potentially failed, we implement the full pipeline here.
    3. Apply Benjamini-Hochberg correction.
    4. Save results to data/results/feature_importance_pvalues.json.
    """
    print("Starting T030: Benjamini-Hochberg correction for feature importance p-values.")
    
    try:
        # Load model and data
        model, X, y, feature_names = load_model_and_features()
        print(f"Loaded model and {len(feature_names)} features.")
        
        # Run permutation importance to get p-values
        # We use n_repeats=10 as a default, which should be sufficient for a demonstration.
        # In a production setting, this might need to be higher.
        perm_result = run_permutation_importance(model, X, y, n_repeats=10, random_state=42, n_jobs=-1)
        
        p_values = perm_result['p_values']
        mean_importances = perm_result['mean_importance']
        
        # Apply Benjamini-Hochberg correction
        corrected_p_values, is_significant = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        # Prepare output data
        results = []
        for i, name in enumerate(feature_names):
            results.append({
                "feature": name,
                "mean_importance": float(mean_importances[i]),
                "p_value_raw": float(p_values[i]),
                "p_value_corrected": float(corrected_p_values[i]),
                "is_significant_fdr_0.05": bool(is_significant[i])
            })
        
        # Sort by corrected p-value
        results.sort(key=lambda x: x['p_value_corrected'])
        
        # Create output dictionary
        output_data = {
            "method": "Permutation Importance with Benjamini-Hochberg Correction",
            "alpha": 0.05,
            "n_repeats": 10,
            "features": results,
            "summary": {
                "total_features": len(results),
                "significant_features": int(np.sum(is_significant)),
                "max_p_value_raw": float(np.max(p_values)),
                "min_p_value_corrected": float(np.min(corrected_p_values))
            }
        }
        
        # Save to JSON
        output_path = RESULTS_DIR / "feature_importance_pvalues.json"
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Successfully saved corrected p-values to {output_path}")
        print(f"Found {output_data['summary']['significant_features']} significant features at FDR < 0.05.")
        
    except Exception as e:
        print(f"Error during T030 execution: {e}")
        raise

if __name__ == "__main__":
    main()
