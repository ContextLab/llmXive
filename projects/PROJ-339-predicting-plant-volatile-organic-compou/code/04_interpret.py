import os
import sys
import json
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor

# Ensure we can import from project root if run as script
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def ensure_dirs():
    """Create necessary output directories."""
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def load_model_and_features():
    """Load the trained model and the feature names used during training."""
    model_path = Path("data/models/random_forest.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Run T024 first.")
    
    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
    
    # Handle potential variations in pickle structure based on T024 implementation
    if isinstance(model_data, dict):
        model = model_data.get("model")
        feature_names = model_data.get("feature_names")
    else:
        # Fallback if T024 saved just the model and we need to infer features from the merged dataset
        model = model_data
        # We need to load the merged dataset to get feature names if not in pickle
        merged_path = Path("data/processed/merged_dataset.csv")
        if merged_path.exists():
            df = pd.read_csv(merged_path)
            # Assuming target is 'VOC_emission' or similar, and everything else is feature
            # This is a heuristic; ideally feature_names are saved with the model
            target_col = 'VOC_emission' 
            if target_col in df.columns:
                feature_names = [c for c in df.columns if c != target_col]
            else:
                # Fallback: assume last column is target if standard convention
                feature_names = [c for c in df.columns[:-1]]
        else:
            raise FileNotFoundError("Could not determine feature names. Please ensure merged dataset exists or model pickle contains 'feature_names'.")

    if model is None:
        raise ValueError("Loaded model data does not contain a valid model object.")
    
    return model, feature_names

def run_permutation_importance(model, X, y, feature_names, n_repeats=10, random_state=42):
    """
    Run permutation importance and return results with p-values.
    
    Returns:
        pd.DataFrame: Features, importances, standard deviations, and p-values.
    """
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1
    )
    
    # Calculate p-values (one-sided test: importance > 0)
    # The permutation distribution is centered around 0 under the null hypothesis.
    # We count how many permuted importances are >= observed importance.
    p_values = []
    for i in range(len(feature_names)):
        perm_importances = result.importances_mean[i] # This is actually the mean, we need the distribution
        # permutation_importance returns a dict-like object where 'importances' is (n_features, n_repeats)
        # Let's re-calculate or access the raw importances if available, otherwise use mean and std as approximation
        # sklearn permutation_importance returns an object with 'importances' attribute (n_features, n_repeats)
        # Wait, the return object has 'importances' (n_features, n_repeats) and 'importances_mean', 'importances_std'
        
        # Re-run to get raw importances if not stored in result object directly in older sklearn versions
        # The result object from sklearn.inspection.permutation_importance has:
        # result.importances (n_features, n_repeats)
        
        raw_importances = result.importances[i]
        observed = result.importances_mean[i]
        
        # One-sided p-value: proportion of permuted importances >= observed
        # If observed is negative, p-value might be high.
        # We test H0: mean_importance <= 0 vs H1: mean_importance > 0
        # p = P(permuted >= observed)
        if observed <= 0:
            # If observed is <= 0, it's not significant in the positive direction
            # But let's calculate strictly:
            count = np.sum(raw_importances >= observed)
            p_val = count / len(raw_importances)
        else:
            count = np.sum(raw_importances >= observed)
            p_val = count / len(raw_importances)
        
        p_values.append(p_val)

    df = pd.DataFrame({
        "feature": feature_names,
        "importance": result.importances_mean,
        "std": result.importances_std,
        "p_value": p_values
    })
    
    return df

def benjamini_hochberg_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List or array of raw p-values.
        alpha: Significance level.
    
    Returns:
        tuple: (adjusted_p_values, is_significant)
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    # rank i goes from 1 to n
    ranks = np.arange(1, n + 1)
    adjusted_p_values = sorted_p_values * n / ranks
    
    # Ensure monotonicity (cumulative min from the end)
    # Adjusted p-values must be non-decreasing as rank increases
    # We iterate backwards to ensure this
    for i in range(n - 2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i+1])
    
    # Clip to 1.0
    adjusted_p_values = np.minimum(adjusted_p_values, 1.0)
    
    # Restore original order
    final_adjusted_p_values = np.zeros(n)
    final_adjusted_p_values[sorted_indices] = adjusted_p_values
    
    # Determine significance
    is_significant = final_adjusted_p_values < alpha
    
    return final_adjusted_p_values, is_significant

def generate_shap_plot(model, X, feature_names, output_path):
    """Generate and save SHAP summary plot."""
    # Use TreeExplainer for Random Forest
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Handle case where shap_values might be a list (for multi-output, though we expect single)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    
    plt = shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """
    Main execution for T030: Apply Benjamini-Hochberg correction to permutation p-values.
    """
    print("Starting T030: Benjamini-Hochberg Correction for Feature Importance")
    
    results_dir = ensure_dirs()
    
    # 1. Load Model and Features
    print("Loading model and features...")
    model, feature_names = load_model_and_features()
    
    # 2. Load Data for Permutation Test
    # We need the processed data used for training.
    # T024 saved the model, but we need X and y to run permutation importance again 
    # (unless T024 saved X/y, which it likely didn't to save space, or we rely on the merged dataset).
    merged_path = Path("data/processed/merged_dataset.csv")
    if not merged_path.exists():
        raise FileNotFoundError(f"Required input file {merged_path} not found. Run T015/T017 first.")
    
    df = pd.read_csv(merged_path)
    
    # Identify target column. Based on US1/US2 context, it's likely 'VOC_emission' or similar.
    # Let's assume the last column is the target if not specified, or look for common names.
    target_candidates = ['VOC_emission', 'target', 'y']
    target_col = None
    for cand in target_candidates:
        if cand in df.columns:
            target_col = cand
            break
    
    if not target_col:
        # Fallback: assume last column
        target_col = df.columns[-1]
        print(f"Warning: Target column not explicitly found. Assuming '{target_col}' is the target.")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Ensure feature order matches what the model expects
    # The model was trained on X in T024. We assume the column order in merged_dataset.csv
    # matches the order used in T024, or we re-align based on feature_names loaded from pickle.
    if "feature_names" in dir() and len(feature_names) > 0:
        # Reorder X columns to match feature_names
        # Note: feature_names from pickle should match the columns in X used for training
        X = X[feature_names]
    
    print(f"Running permutation importance on {X.shape[0]} samples, {X.shape[1]} features...")
    
    # 3. Run Permutation Importance
    perm_df = run_permutation_importance(model, X, y, feature_names)
    
    # 4. Apply Benjamini-Hochberg Correction
    print("Applying Benjamini-Hochberg correction...")
    adj_p_values, is_sig = benjamini_hochberg_correction(perm_df['p_value'].values)
    
    perm_df['adj_p_value'] = adj_p_values
    perm_df['is_significant_fdr'] = is_sig
    
    # 5. Save Results
    output_file = results_dir / "feature_importance_pvalues.json"
    output_data = {
        "description": "Feature importance with Benjamini-Hochberg corrected p-values",
        "alpha": 0.05,
        "features": perm_df.to_dict(orient="records")
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Successfully saved corrected p-values to {output_file}")
    
    # Also generate SHAP plot as per T029 dependency (though T029 might have done this, 
    # we ensure it's done here if not, or just re-run for completeness if the task implies the whole block)
    # T029 is marked done, but T030 depends on T028. We focus on T030 output.
    # If T029 failed to generate the plot, we could do it here, but per task list, T029 is done.
    # We will NOT regenerate SHAP here to avoid duplication unless T029 is missing.
    # However, the task T030 specifically asks for the JSON output.
    
    return perm_df

if __name__ == "__main__":
    main()
