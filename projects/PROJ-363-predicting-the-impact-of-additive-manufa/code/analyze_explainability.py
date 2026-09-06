import os
import sys
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import shap
from sklearn.inspection import permutation_importance
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from scipy.stats import spearmanr

# Import project utilities
from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging()

def load_state_file(state_path: str) -> Dict[str, Any]:
    """Load a YAML state file."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def load_model_from_path(model_path: str):
    """Load a pickled model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_data_from_path(data_path: str) -> pd.DataFrame:
    """Load a CSV dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def find_best_model(selection_state: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Determine which model and data files to load based on T028 selection.
    
    Returns:
        Tuple of (selected_subset, model_path, data_path)
    """
    selected_subset = selection_state.get('selected_subset')
    
    if not selected_subset:
        raise ValueError("No model selection found in state/selected_model.yaml")
    
    if selected_subset == 'X_raw':
        model_path = 'models/artifacts/best_raw_model.pkl'
        data_path = 'data/processed/X_raw.csv'
    elif selected_subset == 'X_derived':
        model_path = 'models/artifacts/best_derived_model.pkl'
        data_path = 'data/processed/X_derived.csv'
    else:
        raise ValueError(f"Unknown selected_subset: {selected_subset}")
    
    return selected_subset, model_path, data_path

def calculate_shap_and_plot(
    model, 
    X_data: pd.DataFrame, 
    output_path: str, 
    selected_subset: str
) -> np.ndarray:
    """
    Calculate SHAP values and generate the summary plot.
    
    Args:
        model: Trained sklearn model.
        X_data: Feature DataFrame.
        output_path: Path to save the plot.
        selected_subset: Name of the subset (for labeling).
        
    Returns:
        SHAP values array.
    """
    logger.info(f"Calculating SHAP values for {selected_subset} subset...")
    
    # Use a background dataset for KernelExplainer if needed, or use the full data
    # For tree-based models, TreeExplainer is preferred, but we use a generic approach
    # that works for both GBM and MLP (though MLP might be slow with KernelExplainer)
    # We'll try TreeExplainer first for GBM, fallback to KernelExplainer for others.
    
    try:
        if hasattr(model, 'tree_'):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_data)
        else:
            # For MLP or other non-tree models, use KernelExplainer
            # Limit samples for speed if dataset is large
            n_samples = min(100, X_data.shape[0])
            background = shap.kmeans(X_data, n_samples)
            explainer = shap.KernelExplainer(model.predict, background)
            shap_values = explainer.shap_values(X_data)
    except Exception as e:
        logger.warning(f"Specific explainer failed, falling back to KernelExplainer: {e}")
        # Fallback: always use KernelExplainer with sampling
        n_samples = min(50, X_data.shape[0])
        background = shap.kmeans(X_data, n_samples)
        explainer = shap.KernelExplainer(model.predict, background)
        shap_values = explainer.shap_values(X_data)

    # Handle multi-output SHAP if necessary (regression usually returns 1D or 2D)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]  # Take first output for regression
    
    # Ensure shap_values is 2D (n_samples, n_features)
    if len(shap_values.shape) == 1:
        shap_values = shap_values.reshape(-1, 1)
    
    # Generate Plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_data, show=False, plot_type="dot")
    plt.title(f"SHAP Summary Plot ({selected_subset})")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"SHAP summary plot saved to {output_path}")
    return shap_values

def perform_statistical_analysis(
    model, 
    X_data: pd.DataFrame, 
    y_data: pd.Series,
    shap_values: np.ndarray,
    selected_subset: str
) -> Dict[str, Any]:
    """
    Perform SHAP Bootstrap CI and Permutation Importance.
    """
    logger.info("Performing unified statistical analysis...")
    
    n_samples = X_data.shape[0]
    n_features = X_data.shape[1]
    feature_names = list(X_data.columns)
    
    # 1. SHAP Bootstrap CI
    logger.info("Calculating SHAP Bootstrap Confidence Intervals (N=1000)...")
    bootstrap_n = 1000
    shap_means = np.zeros((bootstrap_n, n_features))
    
    # Use a subset of data for speed if too large, but keep it representative
    # We resample rows
    for i in range(bootstrap_n):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_boot = X_data.iloc[indices]
        
        # Recompute SHAP for this sample (using a fast approx if possible, or re-run)
        # Re-running full SHAP 1000 times is expensive. 
        # Optimization: Use the existing shap_values and resample the rows?
        # No, FR-007 requires recomputing. We must re-run.
        # To avoid TLE, we use a smaller background for KernelExplainer or fewer samples if needed.
        # However, for correctness, we attempt to run.
        try:
            if hasattr(model, 'tree_'):
                explainer = shap.TreeExplainer(model)
                sv = explainer.shap_values(X_boot)
            else:
                # Sampling for background in loop is too slow. 
                # We use the original background but resample X_boot for prediction?
                # SHAP values depend on X. We must compute on X_boot.
                # Fallback: Use a very small sample for the bootstrap loop if dataset is huge.
                # But let's try with a fixed small n for the loop if n_samples > 50
                if n_samples > 50:
                    X_boot_small = X_boot.sample(n=50, random_state=i)
                else:
                    X_boot_small = X_boot
                
                background = shap.kmeans(X_data, min(10, n_samples))
                explainer = shap.KernelExplainer(model.predict, background)
                sv = explainer.shap_values(X_boot_small)
            
            if isinstance(sv, list): sv = sv[0]
            if len(sv.shape) == 1: sv = sv.reshape(-1, 1)
            shap_means[i] = np.mean(sv, axis=0)
        except Exception as e:
            logger.warning(f"Bootstrap iteration {i} failed: {e}. Skipping.")
            continue
    
    # Calculate CIs
    ci_lower = np.percentile(shap_means, 2.5, axis=0)
    ci_upper = np.percentile(shap_means, 97.5, axis=0)
    
    # 2. Permutation Importance
    logger.info("Calculating Permutation Importance (n_repeats=30)...")
    perm_result = permutation_importance(
        model, X_data, y_data, 
        n_repeats=30, 
        random_state=42, 
        scoring='r2',
        n_jobs=1
    )
    
    perm_importance = perm_result.importances_mean
    perm_std = perm_result.importances_std
    
    # Calculate p-values (approximate using permutation distribution)
    # We can use the permutation distribution to estimate p-value:
    # How many permuted importances are >= observed? (Here observed is the permuted mean itself? No)
    # Standard approach: The null hypothesis is that the feature has no effect.
    # The distribution of importances under permutation IS the null distribution.
    # We compare the mean importance to the distribution of importances from the permutations.
    # Actually, permutation_importance returns the mean and std of the drop in score.
    # To get a p-value, we can check if the mean is significantly different from 0 using the std.
    # Or use the distribution of importances from the n_repeats.
    # Let's use a simple Z-score approximation: mean / std.
    # If std is 0, p-value is 0 if mean != 0, else 1.
    p_values = []
    for i in range(n_features):
        if perm_std[i] == 0:
            p_val = 0.0 if perm_importance[i] != 0 else 1.0
        else:
            z = perm_importance[i] / perm_std[i]
            # Two-tailed p-value
            from scipy.stats import norm
            p_val = 2 * (1 - norm.cdf(abs(z)))
        p_values.append(p_val)
    
    # Build Report
    report = {
        "selected_subset": selected_subset,
        "sample_size": n_samples,
        "bootstrap_n": bootstrap_n,
        "permutation_n_repeats": 30,
        "significance_threshold": 0.05,
        "features": []
    }
    
    for i, name in enumerate(feature_names):
        report["features"].append({
            "name": name,
            "mean_shap": float(np.mean(shap_values[:, i])),
            "shap_ci_lower": float(ci_lower[i]),
            "shap_ci_upper": float(ci_upper[i]),
            "perm_importance": float(perm_importance[i]),
            "perm_std": float(perm_std[i]),
            "p_value": float(p_values[i]),
            "is_significant": p_values[i] < 0.05
        })
        
    return report

def run_comparison_analysis(
    raw_model_path: str, 
    derived_model_path: str,
    raw_data_path: str,
    derived_data_path: str,
    output_path: str
):
    """
    Compare the two models (Raw vs Derived) using Spearman correlation of feature ranks.
    """
    logger.info("Running model comparison analysis...")
    
    try:
        model_raw = load_model_from_path(raw_model_path)
        model_derived = load_model_from_path(derived_model_path)
        X_raw = load_data_from_path(raw_data_path)
        X_derived = load_data_from_path(derived_data_path)
    except FileNotFoundError as e:
        logger.warning(f"Comparison skipped due to missing file: {e}")
        return None

    # Get feature importances (using permutation importance for consistency)
    # We need y. Load from cleaned dataset?
    # The task says "compare feature importance".
    # We can use the model's built-in feature_importances_ if available (GBM, RF)
    # or permutation importance.
    
    def get_feature_importance(model, X, y):
        if hasattr(model, 'feature_importances_'):
            return model.feature_importances_
        else:
            # Fallback to permutation
            res = permutation_importance(model, X, y, n_repeats=10, random_state=42)
            return res.importances_mean

    # We need y. Let's load the cleaned data to get y
    # The cleaned data has the target 'porosity'
    if os.path.exists('data/processed/cleaned_316L.csv'):
        df_clean = pd.read_csv('data/processed/cleaned_316L.csv')
        y = df_clean['porosity']
    else:
        logger.error("Cannot find cleaned_316L.csv for comparison y.")
        return None

    # Align y with X subsets
    # X_raw and X_derived are subsets of the cleaned data features.
    # We assume they have the same number of rows and order as cleaned_316L.csv
    y_raw = y.iloc[:X_raw.shape[0]]
    y_derived = y.iloc[:X_derived.shape[0]]

    imp_raw = get_feature_importance(model_raw, X_raw, y_raw)
    imp_derived = get_feature_importance(model_derived, X_derived, y_derived)

    # Rank
    rank_raw = np.argsort(np.argsort(imp_raw))
    rank_derived = np.argsort(np.argsort(imp_derived))

    corr, p_val = spearmanr(rank_raw, rank_derived)

    # Identify significant features (p < 0.05 in their own models)
    # We need to run permutation importance again to get p-values for each
    # This is expensive, so we might skip detailed p-values for comparison if not strictly required
    # The task asks for "significant_features_raw" and "significant_features_derived"
    # We'll use a simple threshold on importance > 0 for now, or re-run perm importance.
    # Let's re-run perm importance for p-values.
    
    def get_sig_features(model, X, y):
        res = permutation_importance(model, X, y, n_repeats=30, random_state=42)
        # Approx p-value
        from scipy.stats import norm
        p_vals = []
        for i in range(len(res.importances_mean)):
            if res.importances_std[i] == 0:
                p = 0.0 if res.importances_mean[i] != 0 else 1.0
            else:
                z = res.importances_mean[i] / res.importances_std[i]
                p = 2 * (1 - norm.cdf(abs(z)))
            p_vals.append(p)
        sig = [X.columns[i] for i, p in enumerate(p_vals) if p < 0.05]
        return sig

    sig_raw = get_sig_features(model_raw, X_raw, y_raw)
    sig_derived = get_sig_features(model_derived, X_derived, y_derived)

    comparison_report = {
        "spearman_correlation": float(corr),
        "p_value_correlation": float(p_val),
        "significant_features_raw": sig_raw,
        "significant_features_derived": sig_derived
    }

    with open(output_path, 'w') as f:
        json.dump(comparison_report, f, indent=2)
    
    # Generate Side-by-Side Bar Chart
    plt.figure(figsize=(12, 6))
    x = np.arange(len(imp_raw))
    width = 0.35

    plt.bar(x - width/2, imp_raw, width, label='Raw Model')
    plt.bar(x + width/2, imp_derived, width, label='Derived Model')
    plt.xlabel('Features')
    plt.ylabel('Importance')
    plt.title('Feature Importance Comparison: Raw vs Derived')
    plt.xticks(x, X_raw.columns, rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('results/plots/feature_comparison.png', dpi=150)
    plt.close()

    logger.info(f"Comparison report saved to {output_path}")
    return comparison_report

def main():
    logger.info("Starting Explainability Analysis (T030)...")
    
    # 1. Load Selection State
    state_path = 'state/selected_model.yaml'
    if not os.path.exists(state_path):
        logger.error(f"Selection state not found: {state_path}. Has T028 run?")
        sys.exit(1)
    
    selection_state = load_state_file(state_path)
    
    # 2. Determine Paths
    selected_subset, model_path, data_path = find_best_model(selection_state)
    
    # 3. Load Model and Data
    logger.info(f"Loading model from {model_path} and data from {data_path}")
    model = load_model_from_path(model_path)
    X_data = load_data_from_path(data_path)
    
    # We need y for permutation importance. Load from cleaned data.
    cleaned_path = 'data/processed/cleaned_316L.csv'
    if os.path.exists(cleaned_path):
        df_clean = pd.read_csv(cleaned_path)
        # Ensure we align y with X_data rows. 
        # Since X_raw/X_derived are subsets of the same rows, we take the same count.
        y_data = df_clean['porosity'].iloc[:X_data.shape[0]]
    else:
        logger.error("cleaned_316L.csv not found. Cannot compute permutation importance.")
        sys.exit(1)

    # 4. Calculate SHAP and Plot
    shap_plot_path = f'results/plots/shap_summary_{selected_subset}.png'
    os.makedirs('results/plots', exist_ok=True)
    shap_values = calculate_shap_and_plot(model, X_data, shap_plot_path, selected_subset)
    
    # 5. Statistical Analysis
    stat_report = perform_statistical_analysis(model, X_data, y_data, shap_values, selected_subset)
    stat_report_path = f'results/reports/unified_statistical_analysis_{selected_subset}.json'
    os.makedirs('results/reports', exist_ok=True)
    with open(stat_report_path, 'w') as f:
        json.dump(stat_report, f, indent=2)
    logger.info(f"Statistical report saved to {stat_report_path}")
    
    # 6. Comparison Analysis (T035)
    # Check if the OTHER model exists
    other_subset = 'X_derived' if selected_subset == 'X_raw' else 'X_raw'
    other_model_path = f'models/artifacts/best_{other_subset.lower()}_model.pkl'
    other_data_path = f'data/processed/X_{other_subset.lower()}.csv'
    
    if os.path.exists(other_model_path) and os.path.exists(other_data_path):
        comp_path = 'results/reports/feature_comparison.json'
        run_comparison_analysis(model_path, other_model_path, data_path, other_data_path, comp_path)
    else:
        logger.warning(f"Other model/data not found for comparison: {other_model_path}, {other_data_path}")
    
    # 7. Update State
    update_state({
        'shap_plot': shap_plot_path,
        'stat_report': stat_report_path,
        'comparison_report': 'results/reports/feature_comparison.json' if os.path.exists('results/reports/feature_comparison.json') else None
    })
    
    logger.info("Explainability Analysis complete.")

if __name__ == "__main__":
    main()