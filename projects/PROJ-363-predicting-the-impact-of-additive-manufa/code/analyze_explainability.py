import os
import sys
import json
import logging
import pickle
import time
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import shap
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score

# Import project utilities
from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging()

def load_state_file(state_path):
    """Load the state.yaml file."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found at {state_path}")
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def load_model_from_path(model_path):
    """Load a pickled model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_data_from_path(data_path):
    """Load a CSV dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}")
    return pd.read_csv(data_path)

def find_best_model(state):
    """Extract the selected model info from state."""
    if 'selected_model' not in state:
        raise ValueError("No selected model found in state.yaml")
    return state['selected_model']

def calculate_shap_and_plot(model, X_data, feature_names, output_path):
    """Calculate SHAP values and generate a summary plot."""
    logger.info(f"Calculating SHAP values for {len(X_data)} samples...")
    explainer = shap.Explainer(model, X_data)
    shap_values = explainer(X_data)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_data, feature_names=feature_names, plot_type="bar", show=False)
    plt.title(f"SHAP Summary - {os.path.basename(output_path)}")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"SHAP plot saved to {output_path}")
    return shap_values

def perform_statistical_analysis(model, X_data, y_data, feature_names, output_path, n_permutations=1000, n_bootstrap=1000):
    """Perform SHAP Bootstrap CI and Permutation Importance."""
    logger.info("Performing unified statistical analysis...")
    
    # 1. SHAP Bootstrap CI
    logger.info(f"Running SHAP Bootstrap (N={n_bootstrap})...")
    shap_values = shap.Explainer(model, X_data)(X_data)
    if isinstance(shap_values, shap.Explanation):
        shap_values_array = shap_values.values
    else:
        shap_values_array = shap_values

    bootstrap_means = []
    for i in range(n_bootstrap):
        idx = np.random.choice(len(X_data), len(X_data), replace=True)
        X_boot = X_data.iloc[idx]
        y_boot = y_data.iloc[idx]
        boot_explainer = shap.Explainer(model, X_boot)
        boot_shap = boot_explainer(X_boot)
        if isinstance(boot_shap, shap.Explanation):
            bootstrap_means.append(np.mean(np.abs(boot_shap.values), axis=0))
        else:
            bootstrap_means.append(np.mean(np.abs(boot_shap), axis=0))
    
    bootstrap_means = np.array(bootstrap_means)
    ci_lower = np.percentile(bootstrap_means, 2.5, axis=0)
    ci_upper = np.percentile(bootstrap_means, 97.5, axis=0)
    mean_shap = np.mean(np.abs(shap_values_array), axis=0)

    # 2. Permutation Importance
    logger.info(f"Running Permutation Importance (N={n_permutations})...")
    perm_result = permutation_importance(model, X_data, y_data, n_repeats=n_permutations, random_state=42, scoring='r2')
    perm_importance = perm_result.importances_mean
    perm_std = perm_result.importances_std
    
    # Calculate p-values (one-sided test: importance > 0)
    # Assuming normal distribution of permutation results
    z_scores = perm_importance / (perm_std + 1e-8)
    from scipy.stats import norm
    p_values = 1 - norm.cdf(z_scores)
    significant = p_values < 0.05

    report = {
        "header": {
            "n_permutations": n_permutations,
            "n_bootstrap": n_bootstrap,
            "significance_threshold": 0.05
        },
        "features": []
    }

    for i, name in enumerate(feature_names):
        report["features"].append({
            "name": name,
            "mean_shap": float(mean_shap[i]),
            "ci_lower": float(ci_lower[i]),
            "ci_upper": float(ci_upper[i]),
            "perm_importance": float(perm_importance[i]),
            "p_value": float(p_values[i]),
            "significant": bool(significant[i])
        })

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Statistical report saved to {output_path}")
    return report

def run_comparison_analysis(state, models_dir, data_dir, results_dir):
    """
    Compare feature importance and SHAP values from X_raw and X_derived models.
    - Loads best_raw_model.pkl and best_derived_model.pkl (or equivalent).
    - Loads X_raw.csv and X_derived.csv.
    - Calculates Spearman correlation between feature importance ranks.
    - Generates a side-by-side bar chart.
    - Saves results to feature_comparison.json.
    """
    logger.info("Starting Separate Model Comparison (T035)...")

    # 1. Identify models and data based on state
    # We need to analyze BOTH models regardless of which was "selected"
    # The task requires comparing the "separate model outputs"
    
    raw_model_path = os.path.join(models_dir, 'best_raw_model.pkl')
    derived_model_path = os.path.join(models_dir, 'best_derived_model.pkl')
    
    raw_data_path = os.path.join(data_dir, 'X_raw.csv')
    derived_data_path = os.path.join(data_dir, 'X_derived.csv')

    # Check existence
    if not os.path.exists(raw_model_path) or not os.path.exists(derived_model_path):
        logger.error("Missing model artifacts for comparison. Expected: best_raw_model.pkl, best_derived_model.pkl")
        # If only one exists, we can't compare. Raise error.
        raise FileNotFoundError("Both raw and derived model artifacts must exist for comparison.")
    
    if not os.path.exists(raw_data_path) or not os.path.exists(derived_data_path):
        logger.error("Missing feature subset data for comparison.")
        raise FileNotFoundError("Both X_raw.csv and X_derived.csv must exist.")

    # Load Models
    logger.info("Loading models...")
    model_raw = load_model_from_path(raw_model_path)
    model_derived = load_model_from_path(derived_model_path)

    # Load Data
    logger.info("Loading feature subsets...")
    X_raw = load_data_from_path(raw_data_path)
    X_derived = load_data_from_path(derived_data_path)

    # We need the target variable for permutation importance
    # Load the cleaned dataset to get 'porosity'
    cleaned_path = os.path.join(data_dir, 'cleaned_316L.csv')
    if not os.path.exists(cleaned_path):
        raise FileNotFoundError(f"Target data not found at {cleaned_path}")
    df_clean = load_data_from_path(cleaned_path)
    y = df_clean['porosity']

    feature_names_raw = X_raw.columns.tolist()
    feature_names_derived = X_derived.columns.tolist()

    # 2. Calculate Feature Importance (using Permutation Importance as the metric for rank)
    logger.info("Calculating permutation importance for Raw model...")
    perm_raw = permutation_importance(model_raw, X_raw, y, n_repeats=100, random_state=42, scoring='r2')
    imp_raw = perm_raw.importances_mean

    logger.info("Calculating permutation importance for Derived model...")
    perm_derived = permutation_importance(model_derived, X_derived, y, n_repeats=100, random_state=42, scoring='r2')
    imp_derived = perm_derived.importances_mean

    # 3. Calculate Spearman Correlation between Ranks
    # Note: The feature sets are different. 
    # Raw: ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    # Derived: ['energy_density']
    # Direct rank correlation is impossible if lengths differ.
    # However, the task asks to "validate physical intuition".
    # If Derived is just Ev, and Ev is a function of Raw, we expect high correlation 
    # between the importance of Ev and the *combined* importance of Raw features.
    # But strictly, Spearman requires same length.
    # Interpretation: If the task implies comparing the *ranking* of features within their own sets,
    # that's trivial (1 vs 1). 
    # Alternative Interpretation: The "Derived" model might have multiple derived features in a real scenario.
    # Here, based on T016b, X_derived has only 'energy_density'.
    # X_raw has 4 features.
    # We cannot compute Spearman correlation between a list of 4 and a list of 1.
    # We must handle this gracefully.
    # Strategy: If lengths differ, report N/A for correlation, but still compare the *values* 
    # or note the structural difference.
    # OR: Perhaps the "Derived" model in a real scenario includes interaction terms?
    # Given the strict spec: "Calculate Spearman correlation between feature importance ranks".
    # If we cannot, we must state why.
    # However, let's look at the output schema: `{"spearman_correlation": <float>, ...}`.
    # This implies a float is expected.
    # If X_derived only has 1 feature, the rank is trivial.
    # Maybe the "Derived" set in the spec implies something else?
    # Re-reading T016b: "create distinct feature subsets: X_raw ... and X_derived (only Ev)".
    # So X_derived has 1 column. X_raw has 4.
    # Spearman correlation is undefined for different lengths.
    # We will set it to None or 0.0 with a note, OR we calculate the correlation between the 
    # importance of 'energy_density' and the *sum* of importance of raw features? No, that's not Spearman.
    # Let's assume the task implies a scenario where both have >1 feature, or we handle the 1-feature case.
    # If N=1, the rank is [1]. If M=4, ranks are [1,2,3,4].
    # We will compute the correlation only if lengths match. If not, we set it to NaN and log a warning.
    
    spearman_corr = None
    if len(feature_names_raw) == len(feature_names_derived):
        ranks_raw = pd.Series(imp_raw).rank(ascending=False).values
        ranks_derived = pd.Series(imp_derived).rank(ascending=False).values
        corr, _ = spearmanr(ranks_raw, ranks_derived)
        spearman_corr = float(corr)
    else:
        logger.warning(f"Cannot compute Spearman correlation: Raw features ({len(feature_names_raw)}) != Derived features ({len(feature_names_derived)}).")
        spearman_corr = None

    # 4. Identify Significant Features
    significant_raw = [name for name, imp in zip(feature_names_raw, imp_raw) if imp > 0] # Simple threshold
    significant_derived = [name for name, imp in zip(feature_names_derived, imp_derived) if imp > 0]

    # 5. Generate Side-by-Side Bar Chart
    logger.info("Generating comparison bar chart...")
    plt.figure(figsize=(12, 6))
    
    x = np.arange(len(feature_names_raw))
    width = 0.35

    # We need to align features if possible, but they are different.
    # Let's plot them side by side but grouped by "Model Type" if we had matching features.
    # Since they don't match, we'll plot two separate groups or a single chart with different x-axes?
    # Standard approach: Two subplots or a grouped bar if we map them?
    # Let's do two subplots for clarity, or a single bar chart with "Raw Features" and "Derived Features" as categories.
    # Given the "Side-by-side" requirement, let's try to plot them in one figure with two clusters.
    
    # Cluster 1: Raw
    plt.subplot(1, 2, 1)
    plt.barh(feature_names_raw, imp_raw, color='skyblue')
    plt.xlabel('Permutation Importance')
    plt.title('Raw Model Feature Importance')
    plt.gca().invert_yaxis()

    # Cluster 2: Derived
    plt.subplot(1, 2, 2)
    plt.barh(feature_names_derived, imp_derived, color='salmon')
    plt.xlabel('Permutation Importance')
    plt.title('Derived Model Feature Importance')
    plt.gca().invert_yaxis()

    plt.tight_layout()
    chart_path = os.path.join(results_dir, 'feature_comparison_chart.png')
    plt.savefig(chart_path)
    plt.close()
    logger.info(f"Comparison chart saved to {chart_path}")

    # 6. Save JSON Report
    report = {
        "spearman_correlation": spearman_corr,
        "significant_features_raw": significant_raw,
        "significant_features_derived": significant_derived,
        "raw_importance": dict(zip(feature_names_raw, imp_raw.tolist())),
        "derived_importance": dict(zip(feature_names_derived, imp_derived.tolist())),
        "note": "Spearman correlation is only computed if feature counts match." if spearman_corr is None else "Correlation computed on ranks."
    }

    output_json_path = os.path.join(results_dir, 'feature_comparison.json')
    with open(output_json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Feature comparison report saved to {output_json_path}")
    return report

def main():
    logger.info("Starting Explainability Analysis (T035: Separate Model Comparison)")
    
    # Paths
    project_root = Path(__file__).parent.parent
    state_path = project_root / 'state' / 'state.yaml'
    models_dir = project_root / 'models' / 'artifacts'
    data_dir = project_root / 'data' / 'processed'
    results_dir = project_root / 'results' / 'reports'

    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load State
    state = load_state_file(str(state_path))
    
    # Run Comparison
    try:
        run_comparison_analysis(state, str(models_dir), str(data_dir), str(results_dir))
        logger.info("T035 Comparison Analysis completed successfully.")
    except Exception as e:
        logger.error(f"T035 Comparison Analysis failed: {e}")
        raise

    # Update State (hash of new report)
    report_path = results_dir / 'feature_comparison.json'
    if report_path.exists():
        h = compute_file_hash(str(report_path))
        update_state(state_path, 'feature_comparison_report', h)
        logger.info("State updated with feature_comparison_report hash.")

if __name__ == "__main__":
    main()