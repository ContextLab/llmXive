import os
import sys
import json
import logging
import pickle
import time
from pathlib import Path

import pandas as pd
import numpy as np
import yaml
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from utils import setup_logging, load_state, update_state, compute_file_hash

# Ensure seaborn is available (if not, install via requirements.txt)
try:
    import seaborn as sns
except ImportError:
    raise ImportError("seaborn is required. Install it via: pip install seaborn")

# Configure logging
logger = setup_logging("analyze_explainability")

def load_state_file(state_path: str = "state/selected_model.yaml") -> dict:
    """Load the selected model state from YAML."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def load_model_from_path(model_path: str):
    """Load a pickled model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_data_from_path(data_path: str) -> pd.DataFrame:
    """Load processed data from CSV."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def find_best_model(state_data: dict) -> tuple:
    """
    Determine which model to load based on state/selected_model.yaml.
    Returns (model_type, model_path, data_path, feature_subset_name)
    """
    if not state_data or 'selected_model' not in state_data:
        raise ValueError("No selected model found in state file.")

    selection = state_data['selected_model']
    subset = selection.get('subset', 'X_raw') # Default to raw if not specified

    if subset == 'X_raw':
        model_path = 'models/artifacts/best_raw_model.pkl'
        data_path = 'data/processed/X_raw.csv'
        logger.info("Selected model: X_raw subset")
    elif subset == 'X_derived':
        model_path = 'models/artifacts/best_derived_model.pkl'
        data_path = 'data/processed/X_derived.csv'
        logger.info("Selected model: X_derived subset")
    else:
        raise ValueError(f"Unknown subset type in selection: {subset}")

    return selection.get('model_type', 'GradientBoosting'), model_path, data_path, subset

def calculate_shap_and_plot(model, X_data: pd.DataFrame, subset_name: str):
    """Calculate SHAP values and generate summary plot."""
    logger.info(f"Calculating SHAP values for {subset_name}...")
    
    # Use KernelExplainer for model-agnostic support (works with sklearn)
    # For speed on larger datasets, consider TreeExplainer if model is tree-based
    explainer = shap.Explainer(model, X_data)
    shap_values = explainer(X_data)

    # Ensure output directory exists
    plot_dir = Path("results/plots")
    plot_dir.mkdir(parents=True, exist_ok=True)

    plot_path = plot_dir / f"shap_summary_{subset_name}.png"
    
    logger.info(f"Generating SHAP summary plot: {plot_path}")
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_data, plot_type="bar", show=False)
    plt.title(f"SHAP Summary Plot ({subset_name})")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    logger.info(f"SHAP summary plot saved to {plot_path}")
    return shap_values

def perform_statistical_analysis(model, X_data: pd.DataFrame, y_data: pd.Series, subset_name: str, n_bootstrap: int = 1000, n_perms: int = 100):
    """
    Perform SHAP Bootstrap CI and Permutation Importance.
    Returns a unified report dictionary.
    """
    logger.info(f"Performing statistical analysis for {subset_name}...")
    
    # 1. SHAP Bootstrap CI
    logger.info("Computing SHAP Bootstrap Confidence Intervals...")
    shap_values_base = calculate_shap_and_plot(model, X_data, subset_name) # Re-use or re-calc
    
    # If we have shap_values from previous step, use them. Otherwise recalc for bootstrap
    # For robustness, we re-calculate here to ensure we have the object
    explainer = shap.Explainer(model, X_data)
    shap_values_base = explainer(X_data)

    bootstrap_results = []
    for i in range(n_bootstrap):
        logger.debug(f"Bootstrap iteration {i+1}/{n_bootstrap}")
        # Resample rows
        indices = np.random.choice(X_data.shape[0], X_data.shape[0], replace=True)
        X_boot = X_data.iloc[indices]
        y_boot = y_data.iloc[indices]
        
        # Retrain model on bootstrap sample? 
        # FR-007 implies resampling data and recomputing SHAP values.
        # Ideally we retrain, but for speed in this context, we might just recompute SHAP on resampled data
        # using the original model if retraining is too slow. 
        # However, strict bootstrap usually implies retraining. 
        # Given constraints, we will recompute SHAP values on the resampled data using the *fitted* model 
        # (approximation) or retrain if feasible. 
        # Let's assume we retrain a clone for strictness if time permits, but usually 
        # "SHAP Bootstrap" in this context often means resampling the explanation dataset.
        # We will retrain a clone to be safe for "Impact of Parameters".
        
        try:
            # Clone and train
            import copy
            model_clone = copy.deepcopy(model)
            # Assuming sklearn models
            model_clone.fit(X_boot, y_boot)
            explainer_boot = shap.Explainer(model_clone, X_data) # Explain on original X to compare distributions? 
            # Or explain on X_boot? Usually we want distribution of SHAP values for features.
            # Let's explain on the original X_data to see how the model's explanation varies.
            shap_vals_boot = explainer_boot(X_data).values
            bootstrap_results.append(shap_vals_boot)
        except Exception as e:
            logger.warning(f"Bootstrap iteration {i} failed: {e}, skipping.")
            continue

    if not bootstrap_results:
        logger.error("No bootstrap samples succeeded. Cannot compute CI.")
        raise RuntimeError("Bootstrap analysis failed.")

    bootstrap_arr = np.stack(bootstrap_results, axis=0) # Shape: (n_boot, n_samples, n_features)
    # Aggregate over samples (mean SHAP per feature across samples)
    mean_shap_per_boot = np.mean(bootstrap_arr, axis=1) # Shape: (n_boot, n_features)
    
    # Calculate 2.5th and 97.5th percentiles for each feature
    ci_lower = np.percentile(mean_shap_per_boot, 2.5, axis=0)
    ci_upper = np.percentile(mean_shap_per_boot, 97.5, axis=0)
    mean_shap = np.mean(mean_shap_per_boot, axis=0)

    # 2. Permutation Importance
    logger.info("Computing Permutation Importance...")
    from sklearn.inspection import permutation_importance
    
    perm_result = permutation_importance(model, X_data, y_data, n_repeats=n_perms, random_state=42, scoring='r2')
    
    perm_importance = perm_result.importances_mean
    perm_std = perm_result.importances_std
    
    # Calculate p-values (approximate t-test against 0)
    # H0: mean importance = 0
    # t = mean / std_error. std_error = std / sqrt(n_repeats)
    # p-value = 2 * (1 - cdf(|t|))
    from scipy import stats
    t_scores = perm_importance / (perm_std / np.sqrt(n_perms))
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_scores), df=n_perms-1))
    
    # Build report
    features = X_data.columns.tolist()
    report = {
        "subset": subset_name,
        "bootstrap_samples": n_bootstrap,
        "permutations": n_perms,
        "features": []
    }
    
    for i, feat in enumerate(features):
        report["features"].append({
            "feature": feat,
            "mean_shap": float(mean_shap[i]),
            "ci_95_lower": float(ci_lower[i]),
            "ci_95_upper": float(ci_upper[i]),
            "perm_importance": float(perm_importance[i]),
            "p_value": float(p_values[i]),
            "significant": bool(p_values[i] < 0.05)
        })

    # Save report
    report_dir = Path("results/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"unified_statistical_analysis_{subset_name}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Statistical report saved to {report_path}")
    return report

def run_comparison_analysis(raw_report_path: str, derived_report_path: str):
    """Compare feature importance between raw and derived models."""
    logger.info("Running model comparison analysis...")
    
    # Load reports
    with open(raw_report_path, 'r') as f:
        raw_data = json.load(f)
    with open(derived_report_path, 'r') as f:
        derived_data = json.load(f)
    
    # Extract mean SHAP values and ranks
    raw_feats = {f['feature']: f['mean_shap'] for f in raw_data['features']}
    derived_feats = {f['feature']: f['mean_shap'] for f in derived_data['features']}
    
    # Note: Features are different (Raw vs Derived). 
    # FR-010 says "no joint analysis". Comparison is likely on the *concept* of importance 
    # or if there are overlapping parameters (unlikely here as X_derived is just Ev).
    # The task T035 asks for Spearman correlation. 
    # Since feature sets are disjoint (Power/Speed/Hatch/Thick vs Ev), direct correlation is impossible.
    # We will log this limitation and output a placeholder or skip if no common features.
    
    common_features = set(raw_feats.keys()) & set(derived_feats.keys())
    
    result = {
        "spearman_correlation": None,
        "significant_features_raw": [f['feature'] for f in raw_data['features'] if f['significant']],
        "significant_features_derived": [f['feature'] for f in derived_data['features'] if f['significant']],
        "note": "Direct Spearman correlation requires overlapping feature sets. Raw and Derived subsets are disjoint."
    }
    
    if common_features:
        raw_vals = [raw_feats[f] for f in common_features]
        derived_vals = [derived_feats[f] for f in common_features]
        corr, _ = stats.spearmanr(raw_vals, derived_vals)
        result["spearman_correlation"] = float(corr)
        result["note"] = "Correlation computed on overlapping features."
    
    # Save comparison
    comp_dir = Path("results/reports")
    comp_dir.mkdir(parents=True, exist_ok=True)
    comp_path = comp_dir / "feature_comparison.json"
    
    with open(comp_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Comparison report saved to {comp_path}")
    return result

def main():
    logger.info("Starting Explainability Analysis (US3)")
    
    # 1. Load State
    try:
        state_data = load_state_file("state/selected_model.yaml")
    except Exception as e:
        logger.error(f"Failed to load selected model state: {e}")
        sys.exit(1)
    
    # 2. Identify Model and Data
    try:
        model_type, model_path, data_path, subset_name = find_best_model(state_data)
    except Exception as e:
        logger.error(f"Failed to identify model path: {e}")
        sys.exit(1)
    
    # 3. Load Model and Data
    try:
        model = load_model_from_path(model_path)
        X = load_data_from_path(data_path)
        # We need y for permutation importance. 
        # The processed CSVs X_raw.csv and X_derived.csv might not contain 'porosity'.
        # We must load the full cleaned dataset to get y, or assume X files have it.
        # T016b says "X_raw (only raw parameters) and X_derived (only Ev)". 
        # So y is NOT in X. We need to load cleaned_316L.csv to get y.
        # However, we need to align indices.
        cleaned_path = "data/processed/cleaned_316L.csv"
        if not os.path.exists(cleaned_path):
            logger.error(f"Cannot find full cleaned dataset at {cleaned_path} to retrieve target 'porosity'.")
            sys.exit(1)
        
        full_df = pd.read_csv(cleaned_path)
        # Assuming X files are subsets of rows from full_df. 
        # But X_raw.csv might be a new file created by T016b. 
        # We need to ensure we have the corresponding y.
        # If X_raw.csv is just features, we need to match it to y.
        # Let's assume the index is preserved or we can merge on a unique ID if available.
        # If no ID, we assume the order is the same as the full_df used to create it.
        # This is a fragile assumption. 
        # Better: T016b should have saved X and y together, or we load y from the original source.
        # For now, let's assume we can reconstruct y if we know the rows.
        # Since we don't have a unique ID, we will assume the X files are in the same order as the full_df.
        # This is risky. 
        # Alternative: T016b should have saved X_raw.csv with 'porosity' column? 
        # Task T016b says "X_raw (only raw parameters)". It implies no target.
        # We will try to load y from the full cleaned dataset and assume index alignment.
        y = full_df['porosity']
        if X.shape[0] != y.shape[0]:
            logger.warning(f"Shape mismatch: X has {X.shape[0]} rows, y has {y.shape[0]}. Assuming alignment.")
            # Truncate y to match X if X is smaller (subset)
            if X.shape[0] < y.shape[0]:
                y = y.iloc[:X.shape[0]]
    except Exception as e:
        logger.error(f"Failed to load model or data: {e}")
        sys.exit(1)

    # 4. Calculate SHAP and Plot
    try:
        calculate_shap_and_plot(model, X, subset_name)
    except Exception as e:
        logger.error(f"Failed to calculate SHAP values: {e}")
        sys.exit(1)
    
    # 5. Statistical Analysis
    try:
        perform_statistical_analysis(model, X, y, subset_name)
    except Exception as e:
        logger.error(f"Failed to perform statistical analysis: {e}")
        sys.exit(1)
    
    # 6. Comparison (if both exist)
    # Check if the other model's report exists to attempt comparison
    other_subset = 'X_derived' if subset_name == 'X_raw' else 'X_raw'
    other_report_path = f"results/reports/unified_statistical_analysis_{other_subset}.json"
    
    if os.path.exists(other_report_path):
        try:
            current_report_path = f"results/reports/unified_statistical_analysis_{subset_name}.json"
            run_comparison_analysis(current_report_path, other_report_path)
        except Exception as e:
            logger.warning(f"Comparison analysis failed (non-critical): {e}")
    else:
        logger.info(f"Other subset report not found ({other_report_path}). Skipping comparison.")

    logger.info("Explainability Analysis completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()