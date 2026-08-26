import os
import sys
import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_FEATURES = ['power', 'speed', 'hatch', 'thickness']
EV_FEATURE = 'energy_density'
TARGET = 'porosity'

def load_model(model_path):
    """Load a trained model from a pickle file."""
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_data(data_path):
    """Load the preprocessed dataset."""
    df = pd.read_csv(data_path)
    return df

def find_best_model(models_dir):
    """Find the best performing model file based on metrics in the report."""
    metrics_path = models_dir.parent / 'reports' / 'model_metrics.json'
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics report not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    best_model_name = metrics.get('best_model_name')
    if not best_model_name:
        raise ValueError("No best model identified in metrics report")
    
    model_path = models_dir / f"{best_model_name}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    return model_path, best_model_name

def calculate_shap_and_plot(model, X, feature_names, output_path):
    """Calculate SHAP values and generate a summary plot."""
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, plot_type="bar", show=False)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"SHAP summary plot saved to {output_path}")
    return shap_values

def perform_permutation_importance(model, X, y, feature_names, n_permutations=1000):
    """Perform permutation importance with specified number of permutations."""
    result = permutation_importance(model, X, y, n_repeats=n_permutations, random_state=42, n_jobs=-1)
    logger.info(f"Permutation importance completed with {n_permutations} permutations")
    return result.importances_mean, result.importances

def calculate_bootstrap_shap_ci(shap_values, feature_indices, n_iterations=1000):
    """Calculate 95% Bootstrap Confidence Intervals for SHAP values."""
    n_samples, n_features = shap_values.shape
    ci_lower = np.zeros(n_features)
    ci_upper = np.zeros(n_features)
    mean_shap = np.zeros(n_features)
    
    bootstrap_means = []
    
    for _ in range(n_iterations):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        sampled_shap = shap_values[indices]
        bootstrap_means.append(sampled_shap.mean(axis=0))
    
    bootstrap_means = np.array(bootstrap_means)
    mean_shap = bootstrap_means.mean(axis=0)
    ci_lower = np.percentile(bootstrap_means, 2.5, axis=0)
    ci_upper = np.percentile(bootstrap_means, 97.5, axis=0)
    
    logger.info(f"Bootstrap CI calculated for {n_iterations} iterations")
    return mean_shap, ci_lower, ci_upper

def calculate_p_values_and_significance(shap_values, feature_indices, n_iterations=1000, alpha=0.05):
    """Calculate p-values from bootstrap distribution and identify significant parameters."""
    n_samples, n_features = shap_values.shape
    p_values = np.zeros(n_features)
    significant_features = []
    
    for i in range(n_features):
        # Null hypothesis: mean SHAP value is 0
        bootstrap_values = []
        for _ in range(n_iterations):
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            sampled_shap = shap_values[indices]
            bootstrap_values.append(sampled_shap[:, i].mean())
        
        bootstrap_values = np.array(bootstrap_values)
        observed_mean = shap_values[:, i].mean()
        
        # Two-tailed p-value
        p_val = (np.sum(np.abs(bootstrap_values) >= np.abs(observed_mean)) + 1) / (n_iterations + 1)
        p_values[i] = p_val
        
        if p_val < alpha:
            significant_features.append(feature_indices[i])
    
    logger.info(f"P-values calculated. Significant features: {significant_features}")
    return p_values, significant_features

def main():
    """Main entry point for the explainability analysis."""
    # Paths
    project_root = Path(__file__).parent.parent
    models_dir = project_root / 'models' / 'artifacts'
    data_path = project_root / 'data' / 'processed' / 'cleaned_316L.csv'
    plots_dir = project_root / 'results' / 'plots'
    reports_dir = project_root / 'results' / 'reports'
    
    plots_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading data...")
    df = load_data(data_path)
    
    # CRITICAL: Handle Multicollinearity (Task T034)
    # Ensure we do NOT use both raw parameters and Volumetric Energy Density simultaneously.
    # We prioritize Volumetric Energy Density (EV) if available, as it is the derived physical metric.
    # If EV is present, we drop the raw parameters from the feature set.
    # If EV is not present, we use the raw parameters.
    
    has_ev = EV_FEATURE in df.columns
    has_raw = all(col in df.columns for col in RAW_FEATURES)
    
    if has_ev and has_raw:
        logger.warning("Both raw parameters and Volumetric Energy Density detected. "
                     f"Excluding raw parameters ({RAW_FEATURES}) to avoid multicollinearity. "
                     f"Using '{EV_FEATURE}' as the primary feature.")
        feature_cols = [EV_FEATURE]
        # Optionally, we can keep other non-collinear features if any, but per spec, 
        # the core conflict is between raw params and EV.
        # For this task, we strictly use EV if available to satisfy T034.
    elif has_ev:
        logger.info("Using Volumetric Energy Density as the feature.")
        feature_cols = [EV_FEATURE]
    elif has_raw:
        logger.info("Using raw parameters as features (EV not available).")
        feature_cols = RAW_FEATURES
    else:
        raise ValueError("Neither Volumetric Energy Density nor raw parameters found in dataset.")
    
    # Prepare X and y
    X = df[feature_cols].values
    y = df[TARGET].values
    
    # Load model
    logger.info("Finding best model...")
    model_path, model_name = find_best_model(models_dir)
    model = load_model(model_path)
    logger.info(f"Loaded model: {model_name}")
    
    # Ensure model is fitted (in case it's just the class, though we expect trained)
    # If the model needs X to be a DataFrame for SHAP, convert it
    X_df = pd.DataFrame(X, columns=feature_cols)
    
    # 1. SHAP Analysis
    logger.info("Calculating SHAP values...")
    shap_values = calculate_shap_and_plot(model, X_df, feature_cols, plots_dir / 'shap_summary.png')
    
    # 2. Permutation Importance
    logger.info("Performing permutation importance...")
    perm_importance_mean, perm_importance_dist = perform_permutation_importance(
        model, X_df, y, feature_cols, n_permutations=1000
    )
    
    # 3. Bootstrap CI for SHAP
    logger.info("Calculating Bootstrap Confidence Intervals...")
    mean_shap, ci_lower, ci_upper = calculate_bootstrap_shap_ci(
        shap_values, feature_cols, n_iterations=1000
    )
    
    # 4. P-values and Significance
    logger.info("Calculating p-values...")
    p_values, significant_features = calculate_p_values_and_significance(
        shap_values, feature_cols, n_iterations=1000
    )
    
    # Compile Report
    report = {
        "model_used": model_name,
        "features_used": feature_cols,
        "note_on_multicollinearity": "Raw parameters excluded if EV was present to avoid multicollinearity.",
        "permutation_importance": {
            "feature": feature_cols,
            "mean_importance": perm_importance_mean.tolist(),
            "n_permutations": 1000
        },
        "bootstrap_shap_ci": {
            "feature": feature_cols,
            "mean_shap": mean_shap.tolist(),
            "ci_95_lower": ci_lower.tolist(),
            "ci_95_upper": ci_upper.tolist(),
            "n_iterations": 1000
        },
        "statistical_significance": {
            "p_values": p_values.tolist(),
            "significant_features": significant_features,
            "alpha_threshold": 0.05
        }
    }
    
    # Save Report
    report_path = reports_dir / 'significance_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Significance report saved to {report_path}")
    
    # Update state.yaml (optional but good practice)
    # This would typically be done by a separate utility or task, 
    # but we can call the update_state function if available in utils.
    try:
        from utils import load_state, update_state, compute_file_hash
        state = load_state(project_root / 'state.yaml')
        state['artifacts']['significance_report'] = compute_file_hash(report_path)
        state['artifacts']['shap_plot'] = compute_file_hash(plots_dir / 'shap_summary.png')
        update_state(state, project_root / 'state.yaml')
    except Exception as e:
        logger.warning(f"Could not update state.yaml: {e}")

    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()